from __future__ import annotations

from sqlalchemy.orm import validates


class StripWhitespaceMixin:
    """ Mixin that strips leading/trailing whitespace from first_name and
    last_name on assignment. Subclasses may override strip_names with a
    broader @validates to cover additional fields (e.g. function). """

    @validates('first_name', 'last_name')
    def strip_names(self, key: str, value: str | None) -> str | None:
        return value.strip() if value is not None else value
