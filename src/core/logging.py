"""
Logging configuration using loguru.

Why loguru instead of stdlib logging?
1. Zero-config colored output that actually looks good
2. Built-in rotation without handlers/formatters ceremony
3. Structured logging (JSON) for production with one line
4. Exception tracebacks that show local variables (invaluable for debugging)
5. I've wasted too many hours debugging logging.basicConfig issues
"""

import sys
from typing import Literal

from loguru import logger

# Remove default handler - we'll configure our own
logger.remove()


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    json_logs: bool = False,
) -> None:
    """
    Configure loguru for the application.
    
    Args:
        level: Minimum log level to display
        json_logs: If True, output structured JSON (useful for log aggregators)
    """
    # Ensure Windows consoles can handle unicode log lines gracefully.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Development format - human readable with colors
    dev_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    if json_logs:
        # Production format - structured JSON for log aggregators like Loki/ELK
        logger.add(
            sys.stdout,
            level=level,
            serialize=True,  # This is the magic - JSON output
            backtrace=True,
            diagnose=False,  # Don't leak variable values in production
        )
    else:
        # Development format - colored and human-friendly
        logger.add(
            sys.stdout,
            level=level,
            format=dev_format,
            colorize=True,
            backtrace=True,
            diagnose=True,  # Show variable values in tracebacks (dev only!)
        )
    
    # Also log to file with rotation - because grep is still useful
    logger.add(
        "logs/app.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",  # Rotate when file hits 10MB
        retention="7 days",  # Keep logs for a week
        compression="gz",  # Compress old logs
        backtrace=True,
        diagnose=False,  # Don't leak secrets in log files
    )
    
    logger.info(f"Logging configured at {level} level")


# Re-export logger for convenience
# Usage: from src.core.logging import logger
__all__ = ["logger", "setup_logging"]
