from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаются из переменных окружения / .env."""

    database_url: str = "postgresql+psycopg2://security_user:security_pass@db:5432/security_db"
    secret_key: str = "change-me-to-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000,http://localhost"
    default_page_size: int = 5
    max_page_size: int = 50

    # -------------------- Двухфакторная аутентификация --------------------
    # Одноразовый код отправляется на почту сотрудника через SMTP. Если
    # smtp_host не задан (например, в деве/тестах), код не отправляется по
    # сети, а пишется в лог приложения — это явный и заметный fallback для
    # окружений без настроенной почты, а не тихая подмена функциональности.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@school-security.local"
    smtp_use_tls: bool = True

    otp_length: int = 6
    otp_expire_minutes: int = 5
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 30
    pending_token_expire_minutes: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
