from __future__ import annotations

from onegov.core.orm import SessionManager
from onegov.form.validators import ExpectedExtensions
from onegov.form.validators import InputRequiredIf
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.form.validators import UniqueColumnValue
from onegov.form.validators import ValidPhoneNumber
from pytest import raises
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from wtforms.validators import StopValidation
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base  # noqa: F401
    from onegov.core.request import CoreRequest
    from onegov.form import Form as BaseForm
    from sqlalchemy.orm import Session
    from wtforms import Field as BaseField
else:
    BaseField = BaseForm = CoreRequest = object


def test_unique_column_value_validator(postgres_dsn: str) -> None:
    # avoid confusing mypy
    if not TYPE_CHECKING:
        Base = declarative_base()

    class Dummy(Base):
        __tablename__ = 'dummies'
        name: Column[str] = Column(Text, nullable=False, primary_key=True)

    class Field(BaseField):
        def __init__(self, name: str, data: str) -> None:
            self.name = name
            self.data = data

    class Request(CoreRequest):
        def __init__(self, session: Session) -> None:
            self.session = session

    class Form(BaseForm):
        def __init__(self, session: Session) -> None:
            self.request = Request(session)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(Base)
    mgr.set_current_schema('foobar')
    session = mgr.session()
    session.add(Dummy(name='Alice'))

    validator = UniqueColumnValue(Dummy)
    form = Form(session)

    with raises(RuntimeError):
        validator(form, Field('id', 'Alice'))
    with raises(ValidationError):
        validator(form, Field('name', 'Alice'))
    validator(form, Field('name', 'Bob'))

    form.model = session.query(Dummy).first()
    validator(form, Field('name', 'Alice'))


def test_phone_number_validator() -> None:

    class Field(BaseField):
        def __init__(self, data: int | str | None) -> None:
            self.data = data

    validator = ValidPhoneNumber()

    request: Any = None
    validator(request, Field(None))
    validator(request, Field(''))

    validator(request, Field('+41791112233'))
    validator(request, Field('0041791112233'))
    validator(request, Field('0791112233'))

    # non-swiss numbers are allowed by default
    validator(request, Field('+4909562181751'))

    with raises(ValidationError):
        validator(request, Field(1234))
    with raises(ValidationError):
        validator(request, Field('1234'))

    with raises(ValidationError):
        validator(request, Field('+417911122333'))
    with raises(ValidationError):
        validator(request, Field('041791112233'))
    with raises(ValidationError):
        validator(request, Field('041791112233'))
    with raises(ValidationError):
        validator(request, Field('00791112233'))


def test_phone_number_validator_whitelist() -> None:

    class Field(BaseField):
        def __init__(self, data: str | None) -> None:
            self.data = data

    validator = ValidPhoneNumber(country_whitelist={'CH'})

    request: Any = None
    validator(request, Field(None))
    validator(request, Field(''))

    validator(request, Field('+41791112233'))
    validator(request, Field('0041791112233'))
    validator(request, Field('0791112233'))

    with raises(ValidationError):
        # not a swiss number
        validator(request, Field('+4909562181751'))


def test_input_required_if_validator() -> None:
    class Field(BaseField):
        def __init__(self, name: str, data: object) -> None:
            self.name = name
            self.data = data
            self.raw_data = [data]
            self.errors = []

        def gettext(self, text: str) -> str:
            return text

    # FIXME: stop mocking Form, just use an actual Form...
    class Form(BaseForm):
        def __init__(self) -> None:
            self.true = Field('true', True)
            self.false = Field('false', False)
            self.zero = Field('zero', 0)
            self.one = Field('one', 1)
            self.none = Field('none', None)
            self.empty = Field('empty', '')
            self.string = Field('string', 'string')

        def __contains__(self, name: str) -> bool:
            return hasattr(self, name)

        def __getitem__(self, name: str) -> Field:
            return getattr(self, name)

    form = Form()
    values = (None, False, 0, '', True, 1, 'string', 'xxx')
    for field in form.__dict__.values():
        expected = {str(value): [value, False] for value in values}
        expected[str(field.data)][1] = True
        for value, fails in expected.values():
            if fails:
                with raises(StopValidation):
                    InputRequiredIf(field.name, value)(form, Field('x', None))
            else:
                InputRequiredIf(field.name, value)(form, Field('x', None))

    for field in form.__dict__.values():
        for value in values:
            InputRequiredIf(field.name, value)(form, Field('x', 'y'))

    InputRequiredIf(form.string.name, '!string')(form, Field('x', None))
    with raises(StopValidation):
        InputRequiredIf(form.string.name, '!xxx')(form, Field('x', None))


def test_swiss_ssn_validator() -> None:

    class Field(BaseField):
        def __init__(self, data: str | None) -> None:
            self.data = data

        def gettext(self, text: str) -> str:
            return text

    request: Any = None
    validator = ValidSwissSocialSecurityNumber()

    validator(request, Field(None))
    validator(request, Field(''))

    validator(request, Field('756.1234.5678.97'))

    with raises(ValidationError):
        validator(request, Field('757.1234.5678.97'))

    with raises(ValidationError):
        validator(request, Field('756.x234.5678.97'))

    with raises(ValidationError):
        validator(request, Field('756.1234.567.97'))

    with raises(ValidationError):
        validator(request, Field('756.1234.5678.7'))

    with raises(ValidationError):
        validator(request, Field(' 756.1234.5678.7'))

    with raises(ValidationError):
        validator(request, Field('756.1234.5678.7 '))


def test_mp3_extension_nonempty_whitelist() -> None:
    validator = ExpectedExtensions(['.mp3'])
    assert validator.whitelist
