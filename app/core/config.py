import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "laundry-backend")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

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
    topic_prefix: str = os.getenv("TOPIC_PREFIX", "laundry/devices")

    ack_timeout_seconds: int = os.getenv("ACK_TIMEOUT_SECONDS", 5)
    timezone_name: str = os.getenv("TIMEZONE_NAME", "Asia/Ho_Chi_Minh")

    class Config:
        env_prefix = "BACKEND_"
        case_sensitive = False


settings = Settings()
