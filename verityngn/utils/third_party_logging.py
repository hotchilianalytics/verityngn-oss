"""Raise log levels for noisy third-party libraries (Cloud Logging noise reduction)."""

from __future__ import annotations

import logging

_configured = False


def configure_third_party_loggers() -> None:
    """markdown-it emits many DEBUG lines; keep at WARNING unless debugging."""
    global _configured
    if _configured:
        return
    _configured = True
    logging.getLogger("markdown_it").setLevel(logging.WARNING)
    for name in list(logging.root.manager.loggerDict.keys()):
        if isinstance(name, str) and name.startswith("markdown_it."):
            logging.getLogger(name).setLevel(logging.WARNING)
