import logging
from pathlib import Path

import sib_api_v3_sdk
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import UndefinedError
from sib_api_v3_sdk.rest import ApiException

from config import settings

logger = logging.getLogger(__name__)

# `autoescape` : c'est tout l'objet du passage à Jinja2 (cf. render_template).
# `StrictUndefined` : une clé oubliée devient une erreur, non un trou silencieux.
_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    undefined=StrictUndefined,
)


class EmailSendError(Exception):
    """L'email n'a pas pu être remis au fournisseur.

    Existe pour que l'appelant puisse distinguer un échec d'envoi de n'importe
    quelle autre erreur, et décider quoi faire — historiquement l'exception était
    avalée par un `print`, ce qui a masqué une clé Brevo désactivée pendant des
    semaines : les adhésions passaient en `validated` sans qu'aucun email ne parte.
    """


# Configure API key authorization: api-key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.BREVO_API_KEY

# Create an instance of the API class
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def render_template(template_name: str, context: dict) -> str:
    """Rend un template d'email, valeurs échappées.

    Les templates sont écrits en syntaxe Jinja2 (`{{ }}`, `{% for %}`) et étaient
    rendus par une substitution maison (`str.replace`, `re.sub`) qui n'échappait
    rien : `nom`, `prenom` et les noms d'activités partaient tels quels dans le
    corps de l'email. Un nom d'activité est saisi au back-office et diffusé à tous
    les inscrits — le jour où un compte admin est compromis, c'est un vecteur
    d'injection HTML de masse. `receipt.html` passait déjà par Jinja2 ; les emails
    le font désormais aussi.

    Lève `EmailSendError` si le contexte est incomplet (`StrictUndefined`) : mieux
    vaut un échec d'envoi, que l'appelant sait absorber — l'adhésion reste
    enregistrée, `email_sent_at` reste NULL et le back-office propose le renvoi —
    qu'un email tronqué remis à l'adhérent.
    """
    try:
        return _TEMPLATE_ENV.get_template(template_name).render(**context)
    except UndefinedError as e:
        logger.error("Template %s incomplet : %s", template_name, e)
        raise EmailSendError(f"Template {template_name} incomplet : {e}") from e

def _send(email_to: str, subject: str, html_content: str):
    """Remet un email à Brevo, ou lève `EmailSendError`.

    Volontairement synchrone : le SDK Brevo est bloquant, le marquer `async`
    ferait croire le contraire et bloquerait la boucle d'événements. FastAPI
    exécute les routes synchrones dans un threadpool, ce qui convient mieux ici.
    """
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email_to}],
        sender={"name": "Foyer Rural de Fauverney", "email": settings.MAIL_FROM},
        subject=subject,
        html_content=html_content,
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        # `e.body` porte le diagnostic utile de Brevo ("API Key is not enabled",
        # "sender not valid"…) ; sans lui le message est indéchiffrable.
        logger.error(
            "Échec de l'envoi Brevo vers %s : HTTP %s %s", email_to, e.status, e.body
        )
        raise EmailSendError(f"Brevo a refusé l'envoi (HTTP {e.status})") from e
    except Exception as e:
        # Panne réseau/DNS : urllib3 lève ses propres exceptions, hors ApiException.
        logger.exception("Envoi Brevo impossible vers %s", email_to)
        raise EmailSendError("Fournisseur d'email injoignable") from e

    logger.info("Email envoyé à %s (%s)", email_to, api_response.message_id)
    return api_response


async def send_validation_email(email_to: str, subject: str, body: dict):
    """Email de confirmation, envoyé quand un admin valide l'adhésion."""
    return _send(email_to, subject, render_template("validation_email.html", body))


def send_submission_email(email_to: str, subject: str, body: dict):
    """Accusé de réception, envoyé dès la soumission du formulaire.

    Porte le code de suivi : c'est le seul moyen pour l'adhérent de reprendre sa
    demande s'il ferme la page avant de l'avoir noté.
    """
    return _send(email_to, subject, render_template("submission_email.html", body))
