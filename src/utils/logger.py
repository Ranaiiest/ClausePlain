"""
Centralized logging configuration for the platform.

All modules import `get_logger` from here instead of configuring
loguru independently, so log format/sinks stay consistent app-wide.
"""
from __future__ import annotations

import sys
from pathlib import Path
from loguru import logger as _logger

_CONFIGURED = False


def configure_logging(
    log_dir: str = "logs",
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "10 days",
) -> None:
    """Configure the global loguru sink. Safe to call multiple times.

    Args:
        log_dir: Directory where rotating log files are written.
        level: Minimum log level ("DEBUG", "INFO", "WARNING", "ERROR").
        rotation: Loguru rotation policy (size or time based).
        retention: How long to keep rotated log files.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    _logger.remove()  # drop default handler to avoid duplicate console logs

    _logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
    )
    _logger.add(
        str(Path(log_dir) / "platform.log"),
        level=level,
        rotation=rotation,
        retention=retention,
        backtrace=True,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    _CONFIGURED = True


def get_logger(name: str):
    """Return a bound loguru logger tagged with the calling module's name.

    Args:
        name: Typically `__name__` of the calling module.

    Returns:
        A loguru logger instance bound with a `module` context field.
    """
    if not _CONFIGURED:
        configure_logging()
    return _logger.bind(module=name)
