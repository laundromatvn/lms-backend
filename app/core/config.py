import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    # backend dir:./app
    # root dir:./
    # template dir:./templates
    BACKEND_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ROOT_DIR: str = os.path.dirname(BACKEND_DIR)
    TEMPLATE_DIR: str = os.path.join(ROOT_DIR, "templates")
    
    APP_NAME: str = os.getenv("APP_NAME", "laundry-backend")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    ALLOW_HOSTS: List[str] = [
        s.strip() for s in os.getenv("ALLOW_HOSTS", "").split(",") if s.strip()]
    CORS_ALLOW_ORIGINS: List[str] = [
        s.strip() 
        for s in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if s.strip()]
    
    # Internal URLs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    PORTAL_URL: str = os.getenv("PORTAL_URL", "http://localhost:3001")

    # Database
    DATABASE_DRIVER: str = os.getenv("DATABASE_DRIVER", "postgresql+psycopg2")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = os.getenv("DATABASE_PORT", 5432)
    DATABASE_USER: str = os.getenv("DATABASE_USER", "laundry_admin")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "Secure@123")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "laundry")
    AUTO_MIGRATE: bool = os.getenv("AUTO_MIGRATE", "false").lower() == "true"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = os.getenv("REDIS_PORT", 6379)
    REDIS_USERNAME: str = os.getenv("REDIS_USERNAME", "")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

    # MQTT
    MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT: int = os.getenv("MQTT_PORT", 1883)
    MQTT_BROKERS: List[str] = [
        s.strip()
        for s in os.getenv("MQTT_BROKERS", "").split(",") if s.strip()]
    MQTT_USERNAME: Optional[str] = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD: Optional[str] = os.getenv("MQTT_PASSWORD")
    MQTT_CLIENT_ID_PREFIX: str = os.getenv("MQTT_CLIENT_ID_PREFIX", "lms_backend")
    MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", 60))
    MQTT_RECONNECT_DELAY: int = int(os.getenv("MQTT_RECONNECT_DELAY", 1))
    MQTT_RECONNECT_DELAY_MAX: int = int(os.getenv("MQTT_RECONNECT_DELAY_MAX", 120))
    TOPIC_PREFIX: str = os.getenv("TOPIC_PREFIX", "lms")

    # Time
    ACK_TIMEOUT_SECONDS: int = os.getenv("ACK_TIMEOUT_SECONDS", 5)
    TIMEZONE_NAME: str = os.getenv("TIMEZONE_NAME", "Asia/Ho_Chi_Minh")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_SECONDS", 30 * 60))
    JWT_REFRESH_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_SECONDS", 60 * 60 * 24 * 7))

    # VietQR
    VIETQR_BASE_URL: str = os.getenv("VIETQR_BASE_URL", "https://dev.vietqr.org")
    VIETQR_USERNAME: str = os.getenv("VIETQR_USERNAME", "vietqr-username")
    VIETQR_PASSWORD: str = os.getenv("VIETQR_PASSWORD", "vietqr-password")
    VIETQR_BANK_ACCOUNT: str = os.getenv("VIETQR_BANK_ACCOUNT", "vietqr-bank-account")
    VIETQR_BANK_CODE: str = os.getenv("VIETQR_BANK_CODE", "vietqr-bank-code")
    VIETQR_USER_BANK_NAME: str = os.getenv("VIETQR_USER_BANK_NAME", "vietqr-bank-name")

    # VietQR Partner API Authentication
    VIETQR_PARTNER_USERNAME: str = os.getenv("VIETQR_PARTNER_USERNAME", "vietqr-partner-username")
    VIETQR_PARTNER_PASSWORD: str = os.getenv("VIETQR_PARTNER_PASSWORD", "vietqr-partner-password")
    VIETQR_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("VIETQR_TOKEN_EXPIRE_SECONDS", 300))

    # Email
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "mailer-sender")
    EMAIL_SENDER_NAME: str = os.getenv("EMAIL_SENDER_NAME", "mailer-sender-name")

    # SMTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = os.getenv("SMTP_PORT", 587)
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "mailer-username")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "mailer-password")

    class Config:
        env_prefix = "BACKEND_"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        if not self.MQTT_BROKERS:
            self.MQTT_BROKERS = [
                f"{self.MQTT_HOST}:{self.MQTT_PORT}",
            ]

        if not self.CORS_ALLOW_ORIGINS:
            self.CORS_ALLOW_ORIGINS = (
                self.ALLOW_HOSTS
                if self.ALLOW_HOSTS
                else [
                    "http://localhost:5173",
                    "https://localhost:5173",
                    "http://127.0.0.1:5173",
                    "https://127.0.0.1:5173",
                ]
            )


settings = Settings()
