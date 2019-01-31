from onegov.core.orm import SessionManager
from onegov.form.validators import InputRequiredIf
from onegov.form.validators import UniqueColumnValue
from onegov.form.validators import ValidPhoneNumber
from pytest import raises
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from wtforms.validators import StopValidation
from wtforms.validators import ValidationError


def test_unique_column_value_validator(postgres_dsn):
    Base = declarative_base()

    class Dummy(Base):
        __tablename__ = 'dummies'
        name = Column(Text, nullable=False, primary_key=True)

    class Field(object):
        def __init__(self, name, data):
            self.name = name
            self.data = data

    class Request(object):
        def __init__(self, session):
            self.session = session

    class Form(object):
        def __init__(self, session):
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


def test_phone_number_validator():

    class Field(object):
        def __init__(self, data):
            self.data = data

    validator = ValidPhoneNumber()

    validator(None, Field(None))
    validator(None, Field(''))

    validator(None, Field('+41791112233'))
    validator(None, Field('0041791112233'))
    validator(None, Field('0791112233'))

    with raises(ValidationError):
        validator(None, Field(1234))
    with raises(ValidationError):
        validator(None, Field('1234'))

    with raises(ValidationError):
        validator(None, Field('+417911122333'))
    with raises(ValidationError):
        validator(None, Field('041791112233'))
    with raises(ValidationError):
        validator(None, Field('041791112233'))
    with raises(ValidationError):
        validator(None, Field('00791112233'))


def test_input_required_if_validator():
    class Field(object):
        def __init__(self, name, data):
            self.name = name
            self.data = data
            self.raw_data = [data]
            self.errors = []

        def gettext(self, text):
            return text

    class Form(object):
        def __init__(self):
            self.true = Field('true', True)
            self.false = Field('false', False)
            self.zero = Field('zero', 0)
            self.one = Field('one', 1)
            self.none = Field('none', None)
            self.empty = Field('empty', '')
            self.string = Field('string', 'string')

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
