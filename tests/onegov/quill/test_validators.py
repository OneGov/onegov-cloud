from __future__ import annotations

from onegov.quill.validators import HtmlDataRequired
from pytest import raises
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from wtforms import Field as BaseField
else:
    BaseField = object


def test_html_data_validator(session: Session) -> None:

    class Field(BaseField):
        def __init__(self, data: object) -> None:
            self.data = data

        def gettext(self, text: str) -> str:
            return text

    form: Any = None
    validator = HtmlDataRequired()

    validator(form, Field('Test'))
    validator(form, Field('<p>Test</p>'))

    with raises(ValidationError):
        validator(form, Field(None))
    with raises(ValidationError):
        validator(form, Field(''))
    with raises(ValidationError):
        validator(form, Field(' '))
    with raises(ValidationError):
        validator(form, Field('<p></p>'))
    with raises(ValidationError):
        validator(form, Field('<p> </p>'))
    with raises(ValidationError):
        validator(form, Field('<p><br></p>'))
    with raises(ValidationError):
        validator(form, Field('<br><br><br><br>'))
