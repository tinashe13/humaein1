from __future__ import annotations

import logging
import sys
import structlog


_logging_configured = False


def configure_logging() -> None:
    """Configure logging in an idempotent way to avoid reload conflicts."""
    global _logging_configured
    
    # Skip if already configured (prevents issues on reload)
    if _logging_configured:
        return
    
    # Clear any existing configuration
    structlog.reset_defaults()
    
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # Only configure basic logging if not already done
    if not logging.getLogger().handlers:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    
    _logging_configured = True



