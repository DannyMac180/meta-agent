import sys
from typing import Optional

import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("meta_agent")


def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 0,
    backup_count: int = 3,
) -> logging.Logger:
    """Configure and return a logger that writes to stdout or a file.

    If ``log_file`` is provided and ``max_bytes`` is greater than ``0`` a
    :class:`~logging.handlers.RotatingFileHandler` will be used to enable log
    rotation.
    """

    log = logging.getLogger(name)
    log.handlers.clear()
    levelno = getattr(logging, level.upper(), logging.INFO)
    log.setLevel(levelno)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    if log_file:
        if max_bytes > 0:
            fh: logging.Handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
        else:
            fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(levelno)
        fh.setFormatter(formatter)
        log.addHandler(fh)
    else:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(levelno)
        sh.setFormatter(formatter)
        log.addHandler(sh)

    return log
