# api/logging_config.py
from logging.config import dictConfig
import os

def setup_logging() -> None:
    """Configure application-wide logging to stdout"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # <--- important
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['wsgi'],
        },
    })