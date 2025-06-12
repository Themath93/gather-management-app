import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "app.log", level: int = logging.INFO) -> None:
    """Configure root logger for the application.

    Parameters
    ----------
    log_file: str
        Path to the log file. Defaults to ``app.log`` in the project root.
    level: int
        Logging level. Defaults to ``logging.INFO``.
    """
    logger = logging.getLogger()
    if logger.handlers:
        # Already configured
        return

    logger.setLevel(level)
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
