import sys
import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import get_settings
from app.core.context import request_id_context

settings = get_settings()

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True

def setup_logging():
    # Ensure logs directory exists
    if not os.path.exists(settings.LOG_DIR):
        os.makedirs(settings.LOG_DIR)

    # Get root logger (or specific app logger)
    # We will configure the root logger to capture everything including Uvicorn
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(request_id)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Filter
    request_id_filter = RequestIdFilter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(request_id_filter)
    logger.addHandler(console_handler)

    # File Handler
    log_path = os.path.join(settings.LOG_DIR, settings.LOG_FILENAME)
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=settings.LOG_MAX_BYTES, 
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(request_id_filter)
    logger.addHandler(file_handler)

    # Specific configuration for Uvicorn to ensure it propagates or uses our handlers
    # access logs might use a different format, but we force ours here for consistency
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn").propagate = True

    logger.info("Logging setup complete")

# Export a logger instance for the app to use
logger = logging.getLogger("app")
