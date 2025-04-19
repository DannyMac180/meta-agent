import logging
from logging import Logger, StreamHandler, FileHandler, Formatter
from typing import Optional


def setup_logging(name: str = __name__, level: str = "INFO", log_file: Optional[str] = None) -> Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Name of the logger.
        level: Logging level as string (e.g., "DEBUG", "INFO").
        log_file: Optional path to a log file. If provided, logs will also be written to this file.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
