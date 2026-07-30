import logging
from pathlib import Path

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from config import settings

logger = logging.getLogger(__name__)


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
            template_str = template_str.replace("{% for activity in activities %}", "")
            template_str = template_str.replace("{% endfor %}", activity_html)
        else:
            template_str = template_str.replace(f"{{{{ {key} }}}}", str(value))

    return template_str

async def send_validation_email(email_to: str, subject: str, body: dict):
    html_content = render_template("validation_email.html", body)
    
    sender = {"name": "Foyer Rural de Fauverney", "email": settings.MAIL_FROM}
    to = [{"email": email_to}]
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
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

    logger.info("Email de validation envoyé à %s (%s)", email_to, api_response.message_id)
    return api_response
