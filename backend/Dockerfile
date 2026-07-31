FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Sans cela, stdout est bufferisé par blocs de 8 Ko dès qu'il n'est pas un tty :
# un log d'erreur peut rester des heures dans le buffer et ne jamais atteindre
# `docker logs`. C'est ce qui a masqué une clé Brevo désactivée pendant 90 jours.
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE 8000

# `2>&1` : uvicorn journalise ses erreurs sur stderr et ses accès sur stdout, et
# `docker logs` fusionne les deux flux par horodatage d'écriture — d'où des lignes
# qui paraissent dans le désordre. Tout sur un seul flux évite l'ambiguïté.
# `exec` garde uvicorn en PID 1 pour que `docker stop` lui transmette bien SIGTERM.
# `--proxy-headers` est le défaut d'uvicorn, mais explicite ici parce que le rate
# limiter en dépend : c'est ce middleware qui remplace l'IP du conteneur Caddy par
# celle du visiteur. Les proxies de confiance viennent de `FORWARDED_ALLOW_IPS`
# (docker/compose.yml) ; en dev, faute de cette variable, uvicorn ne fait
# confiance qu'à 127.0.0.1 — ce qui est le bon défaut hors reverse proxy.
CMD ["sh", "-c", "exec uv run uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers 2>&1"]
