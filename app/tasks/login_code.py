import aiosmtplib
import asyncio
from email.mime.text import MIMEText

from app.core import env_settings, yaml_settings, celery_app

@celery_app.task(
    name = 'login.send_code',
    bind = True,
    max_retries = 3,
    default_retry_delay = 60
)
def send_code(self, to_email: str, code: str, username: str) -> None:
    try:
        asyncio.run(_send_login_code(to_email, code, username))
    except Exception as e:
        raise self.retry(exc = e)

async def _send_login_code(to_email: str, code: str, username: str) -> None:
    link = f'{yaml_settings.LOGIN_CODE_LINK}'
    msg = MIMEText(f'Привет! Твой код для входа в аккаунт: {code}. Ссылка: {link}/{username}.')
    msg['Subject'] = 'Вход в аккаунт'
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
