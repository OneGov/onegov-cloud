from __future__ import annotations

from datetime import datetime
from typing import Any


class DatabaseOutputHandler:
    """OutputHandler that collects messages for database storage."""

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
