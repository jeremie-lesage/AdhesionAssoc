import logging
import re
from pathlib import Path

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from config import settings

logger = logging.getLogger(__name__)

# Bloc de boucle des templates, corps compris (`re.DOTALL` : il est multiligne).
ACTIVITY_LOOP = re.compile(
    r"{% for activity in activities %}.*?{% endfor %}", re.DOTALL
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
    template_path = Path(__file__).parent / 'templates' / template_name
    with open(template_path) as f:
        template_str = f.read()
    
    for key, value in context.items():
        if key == "activities":
            activity_html = ""
            for activity in value:
                activity_html += f"<tr><td>Activité : {activity['name']}</td><td>{activity['price']}€</td></tr>"
            # Le bloc entier est remplacé, corps de boucle inclus. Ne substituer que
            # les deux balises laissait le `<tr>` modèle dans l'email, avec ses
            # `{{ activity.name }}` en clair — visible par l'adhérent.
            # `lambda` plutôt qu'une chaîne : re.sub interpréterait les échappements
            # (`\g`, `\1`) qu'un nom d'activité pourrait contenir.
            # `html=` lie la valeur maintenant : la lambda capturerait sinon la
            # variable de boucle (ruff B023).
            template_str = ACTIVITY_LOOP.sub(
                lambda _, html=activity_html: html, template_str
            )
        else:
            template_str = template_str.replace(f"{{{{ {key} }}}}", str(value))

    return template_str

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
