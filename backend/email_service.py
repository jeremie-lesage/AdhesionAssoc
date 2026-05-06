import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from config import settings
from pathlib import Path
import os

# Configure API key authorization: api-key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.BREVO_API_KEY

# Create an instance of the API class
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def render_template(template_name: str, context: dict) -> str:
    template_path = Path(__file__).parent / 'templates' / template_name
    with open(template_path, 'r') as f:
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
        print(api_response)
    except ApiException as e:
        print("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)
