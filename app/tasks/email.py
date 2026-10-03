import aiosmtplib
import asyncio
from email.mime.text import MIMEText

from app.core import env_settings, yaml_settings, celery_app

@celery_app.task(
    name = 'email.send_verification',
    bind = True,
    max_retries = 3,
    default_retry_delay = 60
)
def send_verification_email(self, to_email: str, user_id: UUID, token: str) -> None:
    try:
        asyncio.run(_send_verification_email(to_email, user_id, token))
    except Exception as e:
        raise self.retry(exc = e)

async def _send_verification_email(to_email: str, user_id: UUID, token: str) -> None:
    link = f'{yaml_settings.VERIFICATION_LINK}?user_id={user_id}&token={token}'
    msg = MIMEText(f'Привет! Подтверди свою почту по ссылке: {link}. Эта ссылка действительна 10 минут.')
    msg['Subject'] = 'Подтверждение email'
    msg['From'] = env_settings.SMTP_USER
    msg['To'] = to_email

    await aiosmtplib.send(
        msg,
        hostname = env_settings.SMTP_HOST,
        port = env_settings.SMTP_PORT,
        username = env_settings.SMTP_USER,
        password = env_settings.SMTP_PASSWORD,

        start_tls = True,
        use_tls = False
    )
