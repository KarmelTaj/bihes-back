"""
Logging settings: structlog wired through stdlib ``logging``.

structlog sits on top of the stdlib ``logging`` module so that *every* record —
whether emitted via ``structlog.get_logger()`` or a plain
``logging.getLogger()`` (Django, DRF, third-party libs) — flows through the same
processor chain and lands in ``log/app.log``.

Importing this module configures structlog and defines the ``LOGGING`` dict that
Django reads. It is merged into the settings namespace by
``core/settings/__init__.py``.
"""

import structlog

from .base import DEBUG, LOGS_DIR

_LEVEL = "DEBUG" if DEBUG else "INFO"

# Processors shared between structlog-native records and "foreign" stdlib
# records, so both kinds carry the same metadata (timestamp, level, logger
# name, and any context vars such as the per-request ``request_id``).
_SHARED_PROCESSORS = [
    # Pull in anything bound with structlog.contextvars.bind_contextvars()
    # (the request_id middleware uses this).
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.TimeStamper(fmt="iso"),
]

# Configure the structlog side once, at import time. The final
# ``wrap_for_formatter`` processor hands the event dict to the stdlib
# ``ProcessorFormatter`` below, so rendering is decided per-handler.
structlog.configure(
    processors=[
        *_SHARED_PROCESSORS,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # Machine-readable JSON, one object per line.
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                # Render exception info as structured data instead of a single
                # multi-line string, so tracebacks stay grep-able.
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            "foreign_pre_chain": _SHARED_PROCESSORS,
        },
    },
    "handlers": {
        # The single destination for every log record.
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "app.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "json",
            "level": _LEVEL,
        },
    },
    "loggers": {
        # Root logger: catches our app loggers and any unconfigured library.
        "": {
            "handlers": ["app_file"],
            "level": _LEVEL,
        },
        # Django's own logs flow to the same file; propagate=False
        # prevents double emission via the root logger above.
        "django": {
            "handlers": ["app_file"],
            "level": "INFO",
            "propagate": False,
        },
        # The dev server's access log ("GET /… HTTP/1.1" 200) duplicates
        # what RequestIDMiddleware already records, so suppress it at INFO.
        # Server errors (5xx) are logged at ERROR and still come through.
        "django.server": {
            "handlers": ["app_file"],
            "level": "WARNING",
            "propagate": False,
        },
        # django.request emits its own "Bad Request" / "Internal Server Error"
        # lines (without a request_id) that duplicate our api_error and
        # request_finished logs. Silence it — only escalate truly unexpected
        # records at CRITICAL.
        "django.request": {
            "handlers": ["app_file"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}
