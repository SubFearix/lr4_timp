import hmac
import hashlib
import logging
import secrets
import smtplib
from email.mime.text import MIMEText

from .config import get_settings

settings = get_settings()
logger = logging.getLogger("security_app.otp")


def generate_otp_code() -> str:
    upper_bound = 10 ** settings.otp_length
    return str(secrets.randbelow(upper_bound)).zfill(settings.otp_length)


def hash_otp_code(code: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp_code(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_otp_code(code), code_hash)


def mask_email(email: str) -> str:
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return email
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def send_otp_email(to_email: str, full_name: str, code: str) -> None:
    subject = "Код подтверждения входа"
    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Код подтверждения входа в систему учёта безопасности: {code}\n"
        f"Код действителен {settings.otp_expire_minutes} минут.\n\n"
        f"Если вы не пытались войти в систему, просто проигнорируйте это письмо."
    )

    if not settings.smtp_host:
        logger.warning(
            "[DEV MODE] SMTP не настроен (SMTP_HOST пуст) — код для %s НЕ отправлен по почте: %s",
            to_email, code,
        )
        return

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to_email], message.as_string())
        logger.info("Письмо с кодом подтверждения отправлено на %s", mask_email(to_email))
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("Не удалось отправить OTP-письмо на %s: %s", to_email, exc)
        raise
