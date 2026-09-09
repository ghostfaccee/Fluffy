import sys
from loguru import logger
from pathlib import Path
import json

logger.remove()
_console_format = (
    '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
    '<level>{level: <8}</level> | '
    '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
    '<level>{message}</level>'
)

logger.add(
    sys.stdout,
    level = 'INFO',
    format = _console_format,
    enqueue = True,
    diagnose = False,
    backtrace = False
)

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok = True)

logger.add(
    LOG_DIR / 'log_{time:YYYY-MM-DD}.log',
    rotation = '1 day',
    retention = '7 days',
    compression = 'gz',
    level = 'INFO',
    diagnose = False,
    backtrace = False,
    serialize = True,
    enqueue = True
)

__all__ = ['logger']