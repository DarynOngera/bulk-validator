import yagmail
import os
from dotenv import load_dotenv
load_dotenv()

def send_validation_report_email(recipient, subject, body, attachments=None):
    """
    Send an email with the validation summary and optional attachments.
    Attachments can be a list of file paths.
    """
    yag_user = os.getenv('EMAIL_USER')
    yag_pass = os.getenv('EMAIL_PASS')
    if not yag_user or not yag_pass:
        raise RuntimeError('EMAIL_USER and EMAIL_PASS environment variables must be set.')
    yag = yagmail.SMTP(yag_user, yag_pass)
    yag.send(
        to=recipient,
        subject=subject,
        contents=body,
        attachments=attachments or []
    )
