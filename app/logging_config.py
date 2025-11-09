"""Logging configuration for the application."""

import logging
import logging.config
import logging.handlers
import os

def setup_logging():
    """Setup logging configuration."""
    # Logging directory
    log_dir = os.getenv("LOG_DIR", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Log dictionary configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(log_dir, "app.log"),
                "formatter": "standard",
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,  # Keep last 5 log files
                "encoding": "utf8",
            },
            "console_handler": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["file_handler", "console_handler"],
                "level": "DEBUG",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["file_handler", "console_handler"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["file_handler", "console_handler"],
                "level": "ERROR",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["file_handler", "console_handler"],
            "level": "WARNING",
        },
    }

    logging.config.dictConfig(logging_config)
