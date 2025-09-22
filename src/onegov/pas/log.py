from __future__ import annotations

import click
import logging
from typing import Protocol


log = logging.getLogger('onegov.org.cronjobs')


class OutputHandler(Protocol):
    """Protocol for handling output during KUB import operations."""

    def info(self, message: str) -> None:
        """Output informational message."""
        ...

    def success(self, message: str) -> None:
        """Output success message."""
        ...

    def error(self, message: str) -> None:
        """Output error message."""
        ...


class ClickOutputHandler:
    """OutputHandler implementation for CLI using click."""

    def info(self, message: str) -> None:
        click.echo(message)

    def success(self, message: str) -> None:
        click.echo(f'✓ {message}')

    def error(self, message: str) -> None:
        click.echo(f'✗ {message}', err=True)


class LogOutputHandler:
    """OutputHandler implementation for cronjobs using logging."""

    def info(self, message: str) -> None:
        log.info(message)

    def success(self, message: str) -> None:
        log.info(message)

    def error(self, message: str) -> None:
        log.error(message)


class CompositeOutputHandler:
    """OutputHandler that forwards messages to multiple handlers."""

    def __init__(self, *handlers: OutputHandler):
        self.handlers = handlers

    def info(self, message: str) -> None:
        for handler in self.handlers:
            handler.info(message)

    def success(self, message: str) -> None:
        for handler in self.handlers:
            handler.success(message)

    def error(self, message: str) -> None:
        for handler in self.handlers:
            handler.error(message)
