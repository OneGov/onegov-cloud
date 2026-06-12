from __future__ import annotations

from io import BytesIO
from onegov.core.orm import SessionManager
from onegov.file.attachments import IMAGE_QUALITY
from onegov.form import Form
from onegov.form import parse_form
from onegov.form.fields import UploadField
from onegov.form.validators import ExpectedExtensions
from onegov.form.validators import ImageFileSizeLimit
from onegov.form.validators import InputRequiredIf
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.form.validators import UniqueColumnValue
from onegov.form.validators import ValidPhoneNumber
from PIL import Image
from pytest import raises
from sqlalchemy.orm import mapped_column, registry, DeclarativeBase, Mapped
from werkzeug.datastructures import FileMultiDict
from wtforms.validators import StopValidation
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.core.orm import Base  # noqa: F401
    from onegov.core.request import CoreRequest
    from onegov.form import Form as BaseForm
    from sqlalchemy.orm import Session
    from wtforms import Field as BaseField
else:
    BaseField = BaseForm = CoreRequest = object


def test_unique_column_value_validator(postgres_dsn: str) -> None:
    class Base(DeclarativeBase):
        registry = registry()

    class Dummy(Base):
        __tablename__ = 'dummies'
        name: Mapped[str] = mapped_column(primary_key=True)

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


def test_image_file_size_limit() -> None:
    class Field:
        def __init__(self, size: int | None) -> None:
            self.data = {'size': size} if size is not None else None

        def gettext(self, text: str) -> str:
            return text

    validator = ImageFileSizeLimit()
    assert validator.max_bytes == ImageFileSizeLimit.DEFAULT_MAX_BYTES

    # no data — pass
    validator(None, Field(None))  # type: ignore[arg-type]

    # within limit — pass
    validator(None, Field(ImageFileSizeLimit.DEFAULT_MAX_BYTES))  # type: ignore[arg-type]

    # exceeds limit — fail
    with raises(ValidationError):
        validator(None, Field(ImageFileSizeLimit.DEFAULT_MAX_BYTES + 1))  # type: ignore[arg-type]

    # custom limit
    with raises(ValidationError):
        ImageFileSizeLimit(max_bytes=1024)(None, Field(1025))  # type: ignore[arg-type]

    with raises(ValidationError, match='The image is too large,'):
        validator(None, Field(ImageFileSizeLimit.DEFAULT_MAX_BYTES + 1))  # type: ignore[arg-type]


def test_image_file_size_limit_on_upload_field() -> None:
    limit = 2_000  # 2 KB

    class PhotoForm(Form):
        photo = UploadField(validators=[ImageFileSizeLimit(max_bytes=limit)])

    def make_form(img: Image.Image, fmt: str) -> PhotoForm:
        buf = BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        data: Any = FileMultiDict()
        data.add_file('photo', buf, filename=f'test.{fmt.lower()}')
        return PhotoForm(data)

    # small solid-color JPEG — well under 2 KB
    small = make_form(Image.new('RGB', (10, 10), color=(0, 128, 0)), 'JPEG')
    assert small.validate(), small.photo.errors

    # large PNG (1000×1000) — will exceed 2 KB
    large = make_form(Image.new('RGB', (1000, 1000), color=(255, 0, 0)), 'PNG')
    assert not large.validate()
    assert large.photo.errors
    assert 'The image is too large,' in large.photo.errors[0]


def test_image_file_size_limit_rejects_on_form_submission() -> None:
    limit = 1_000  # 1 KB — small enough that a 1000×1000 PNG always exceeds it

    BaseForm = parse_form("Photo = *.jpg|*.png")

    class PhotoForm(BaseForm):  # type: ignore[valid-type,misc]
        def on_request(self) -> None:
            self.photo.validators = [
                *self.photo.validators,
                ImageFileSizeLimit(max_bytes=limit),
            ]

    small = Image.new('RGB', (10, 10), color=(0, 128, 0))
    buf_small = BytesIO()
    small.save(buf_small, format='JPEG', quality=IMAGE_QUALITY)
    buf_small.seek(0)
    assert len(buf_small.getvalue()) < limit

    data_small: Any = FileMultiDict()
    data_small.add_file('photo', buf_small, filename='small.jpg')
    form_small = PhotoForm(data_small)
    form_small.on_request()
    assert form_small.validate()
    assert not form_small.photo.errors

    large = Image.new('RGB', (1000, 1000), color=(255, 0, 0))
    buf_large = BytesIO()
    large.save(buf_large, format='PNG')
    buf_large.seek(0)
    assert len(buf_large.getvalue()) > limit

    data_large: Any = FileMultiDict()
    data_large.add_file('photo', buf_large, filename='large.png')
    form_large = PhotoForm(data_large)
    form_large.on_request()
    assert not form_large.validate()
    assert 'The image is too large,' in form_large.photo.errors[0]
