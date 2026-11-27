"""gunicorn settings for every deployed environment (ADR 0007).

gunicorn loads this file automatically from its working directory (/app) at start
time, so one image runs everywhere and each environment only sets variables.
Local development uses runserver and never reads it.
"""

from config.env import env_bool, env_positive_int

# Fixed per environment and required: never derived from the CPU count, because
# containers see the host's CPUs (ADR 0007, fact 12).
workers = env_positive_int("GUNICORN_WORKERS")

# Railway marks stderr as error, so both gunicorn logs go to stdout, in the same
# format as Django's (same variable and default as LOGGING in config/settings.py).
log_format = "json" if env_bool("DJANGO_LOG_JSON", default=True) else "text"

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "core.json_logging.JsonFormatter"},
        "text": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": log_format,
        },
    },
    "root": {"handlers": ["stdout"], "level": "INFO"},
    "loggers": {
        "gunicorn.error": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        "gunicorn.access": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
    },
}

# gunicorn's default access format, with the byte count taken from Content-Length:
# static files go out with sendfile, which leaves gunicorn's own counter at 0.
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %({content-length}o)s "%(f)s" "%(a)s"'
