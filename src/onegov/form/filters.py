from __future__ import annotations

from onegov.core.utils import yubikey_public_id


def as_float(value: str | None) -> float:
    return value and float(value) or 0.0


def strip_whitespace(value: str | None) -> str | None:
    return value and value.strip(' \r\n') or None


def yubikey_identifier(value: str | None) -> str:
    return value and yubikey_public_id(value) or ''
