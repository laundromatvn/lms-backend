import logging
import sys
import structlog

from app.utils.timezone import iso_now_local


def configure_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        stream=sys.stdout,
    )

    def add_timestamp_processor(_logger, _method_name, event_dict):
        event_dict["timestamp"] = iso_now_local()
        return event_dict

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            add_timestamp_processor,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger()

logger = get_logger()
