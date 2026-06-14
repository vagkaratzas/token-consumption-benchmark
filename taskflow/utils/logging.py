"""Logging helpers."""

from __future__ import annotations

import logging

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given name."""
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=logging.INFO, format="%(levelname)s %(name)s %(message)s"
        )
        _CONFIGURED = True
    return logging.getLogger(name)
