from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import logging


class DatabaseOutputHandler:
    """Collects import messages for database storage in ImportLog.

    Facilitates dataflow by capturing detailed logging separately.
    """

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def info(self, message: str) -> None:
        self._add_message('info', message)

    def success(self, message: str) -> None:
        self._add_message('success', message)

    def error(self, message: str) -> None:
        self._add_message('error', message)

    def _add_message(self, level: str, message: str) -> None:
        """Add a message with timestamp and level to the collection."""
        self.messages.append({
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message
        })

    def get_messages(self) -> list[dict[str, Any]]:
        """Return all collected messages."""
        return self.messages.copy()

    def clear_messages(self) -> None:
        """Clear all collected messages."""
        self.messages.clear()


class LogOutputHandler:
    """Logs import messages using Python logging."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def info(self, message: str) -> None:
        self.logger.info(message)

    def success(self, message: str) -> None:
        self.logger.info(f'SUCCESS: {message}')

    def error(self, message: str) -> None:
        self.logger.error(message)
