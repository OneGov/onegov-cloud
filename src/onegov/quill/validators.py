from __future__ import annotations

from onegov.core.html import html_to_text
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wtforms import Field
    from wtforms.form import BaseForm


class HtmlDataRequired:
    """ Checks the field's data contains text inside HTML otherwise stops the
    validation chain.

    """

    field_flags = {'required': True}

    def __init__(self, message: str | None = None):
        self.message = message

    def __call__(self, form: BaseForm, field: Field) -> None:
        data = html_to_text(field.data or '').strip()
        if not data:
            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message

            raise ValidationError(message)
