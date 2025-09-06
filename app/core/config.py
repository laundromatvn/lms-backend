import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "laundry-backend")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    allow_hosts: List[str] = [s.strip() for s in os.getenv("ALLOW_HOSTS", "").split(",") if s.strip()]
    # Comma-separated list of allowed CORS origins
    cors_allow_origins: List[str] = [s.strip() for s in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if s.strip()]

    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: int = os.getenv("DATABASE_PORT", 5432)
    database_user: str = os.getenv("DATABASE_USER", "laundry_admin")
    database_password: str = os.getenv("DATABASE_PASSWORD", "Secure@123")
    database_name: str = os.getenv("DATABASE_NAME", "laundry")
    database_url: str = f"postgresql+psycopg2://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"
    
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = os.getenv("REDIS_PORT", 6379)
    redis_url: str = f"redis://{redis_host}:{redis_port}/0"

    mqtt_host: str = os.getenv("MQTT_HOST", "localhost")
    mqtt_port: int = os.getenv("MQTT_PORT", 1883)
    # Comma-separated list of brokers in the form host:port
    mqtt_brokers: List[str] = [s.strip() for s in os.getenv("MQTT_BROKERS", "").split(",") if s.strip()]
    mqtt_username: Optional[str] = os.getenv("MQTT_USERNAME")
    mqtt_password: Optional[str] = os.getenv("MQTT_PASSWORD")
    mqtt_client_id_prefix: str = os.getenv("MQTT_CLIENT_ID_PREFIX", "lms")
    mqtt_keepalive: int = int(os.getenv("MQTT_KEEPALIVE", 60))
    mqtt_reconnect_delay: int = int(os.getenv("MQTT_RECONNECT_DELAY", 1))
    mqtt_reconnect_delay_max: int = int(os.getenv("MQTT_RECONNECT_DELAY_MAX", 120))
    topic_prefix: str = os.getenv("TOPIC_PREFIX", "lms")

    ack_timeout_seconds: int = os.getenv("ACK_TIMEOUT_SECONDS", 5)
    timezone_name: str = os.getenv("TIMEZONE_NAME", "Asia/Ho_Chi_Minh")

    class Config:
        env_prefix = "BACKEND_"
        case_sensitive = False

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        # Fallback to single broker from mqtt_host/mqtt_port when list is not provided
        if not self.mqtt_brokers:
            self.mqtt_brokers = [f"{self.mqtt_host}:{self.mqtt_port}"]
        # Provide sensible defaults for CORS when not explicitly set
        if not self.cors_allow_origins:
            self.cors_allow_origins = (
                self.allow_hosts
                if self.allow_hosts
                else [
                    "http://localhost:5173",
                    "https://localhost:5173",
                    "http://127.0.0.1:5173",
                    "https://127.0.0.1:5173",
                ]
            )


settings = Settings()
