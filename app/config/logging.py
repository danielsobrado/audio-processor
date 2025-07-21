import logging
import sys
from logging.handlers import RotatingFileHandler

try:
    from pythonjsonlogger.formatter import JsonFormatter
except ImportError:
    JsonFormatter = None


def setup_logging(
    log_level: str = "INFO",
    environment: str = "development",
    log_format: str = "json",
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Configures the application's logging.

    Args:
        log_level: The minimum level of messages to log (e.g., "INFO", "DEBUG").
        environment: The current application environment (e.g., "development", "production").
        log_format: The format for log messages ("json" or "plain").
        log_file: Optional path to a log file for file-based logging.
        max_bytes: Maximum size of a log file before rotation.
        backup_count: Number of backup log files to keep.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers to prevent duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    if log_format == "json" and JsonFormatter:
        formatter = JsonFormatter(
            "%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s"
        )
    else:
        # Standard format for development or if jsonlogger is not available
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler (optional)
    if log_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress verbose loggers from libraries
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("sqlalchemy").propagate = False
    logging.getLogger("httpx").propagate = False
    logging.getLogger("httpcore").propagate = False

    # Example of how to use it
    if environment == "development":
        logging.info("Logging configured for development environment.")
    else:
        logging.info("Logging configured for production environment.")
