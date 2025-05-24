import sys
from typing import Optional

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

logger = logging.getLogger('meta_agent')

def setup_logging(name: str, level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger that writes to stdout or a file."""
    log = logging.getLogger(name)
    log.handlers.clear()
    levelno = getattr(logging, level.upper(), logging.INFO)
    log.setLevel(levelno)
    formatter = logging.Formatter('%(message)s')

    if log_file:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(levelno)
        fh.setFormatter(formatter)
        log.addHandler(fh)
    else:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(levelno)
        sh.setFormatter(formatter)
        log.addHandler(sh)
    return log
