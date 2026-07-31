import time

from fastapi import HTTPException, Request, status

RATE_LIMIT_WINDOW = 60  # secondes

# Requêtes autorisées par fenêtre et par (IP cliente, méthode, motif de route).
# Les écritures restent serrées : elles créent ou modifient des lignes et
# déclenchent un envoi d'email. La lecture est plus large parce que le
# back-office consulte les dossiers un par un — `AdhesionDetailView` appelle
# `GET /api/adhesions/{code}`, et le bouton « Reçu » de la liste ouvre
# `/receipt` — et qu'un admin en dépouillement dépasse vite cinq dossiers par
# minute. Ce n'est pas un affaiblissement : face aux ~62 bits d'entropie d'un
# code (cf. `crud.generate_random_code`), 30 essais/minute ne rapprochent
# d'aucune devinette utile. La limite n'est de toute façon qu'un frein
# secondaire, l'entropie du code étant le contrôle réel.
DEFAULT_RATE_LIMIT = 5
RATE_LIMITS = {
    "GET /api/adhesions/{code}": 30,
    "GET /api/adhesions/{code}/receipt": 30,
}

# (ip, méthode, route) -> [nombre de requêtes, début de fenêtre]. Dict de module,
# donc remis à zéro entre les tests par la fixture `reset_rate_limiter`.
request_counts = {}


def _client_ip(request: Request) -> str:
    """IP de l'appelant.

    Derrière Caddy, `request.client.host` est l'IP du conteneur proxy : uvicorn
    doit tourner avec `--proxy-headers --forwarded-allow-ips` pour que
    `scope["client"]` porte l'IP réelle lue dans `X-Forwarded-For` (voir
    `backend/Dockerfile`). Sans cette option, le compteur serait commun à tous
    les visiteurs — un seul curieux fermerait le formulaire à toute la commune.
    """
    return request.client.host if request.client else "unknown"


def _route_pattern(request: Request) -> str:
    """Motif de la route (`/api/adhesions/{code}`), pas le chemin résolu.

    C'était la faille : indexée sur `request.url.path`, chaque code essayé
    ouvrait un compteur neuf à 1, si bien que la limite n'était jamais atteinte
    quel que soit le nombre de codes tentés.

    `scope["route"]` est posé par le routeur avant la résolution des
    dépendances ; le repli sur `url.path` ne sert qu'aux appels hors routage.
    """
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def rate_limit(request: Request):
    """Refuse en 429 au-delà de la limite de la route pour cette IP.

    Fenêtre fixe et non glissante : le compteur repart à zéro à la première
    requête arrivant plus de `RATE_LIMIT_WINDOW` secondes après le début de la
    fenêtre courante. Approximation assumée — un pic peut ainsi chevaucher deux
    fenêtres.
    """
    route = _route_pattern(request)
    key = (_client_ip(request), request.method, route)
    limit = RATE_LIMITS.get(f"{request.method} {route}", DEFAULT_RATE_LIMIT)

    current_time = time.time()
    count, window_start = request_counts.get(key, (0, current_time))

    if current_time - window_start > RATE_LIMIT_WINDOW:
        request_counts[key] = [1, current_time]
        return

    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

    request_counts[key] = [count + 1, window_start]
