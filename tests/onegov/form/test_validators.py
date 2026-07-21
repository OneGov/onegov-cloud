from __future__ import annotations

from io import BytesIO
from onegov.core.orm import SessionManager
from onegov.file.attachments import IMAGE_QUALITY
from onegov.form import Form
from onegov.form import parse_form
from onegov.form.fields import UploadField
from onegov.form.validators import ExpectedExtensions, PhoneNumberType
from onegov.form.validators import ImageSizeLimit
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

    # non-swiss numbers are allowed by default
    validator(request, Field('+4909562181751'))  # DE
    validator(request, Field('+4319876543'))  # A
    validator(request, Field('+43695621817'))  # A
    validator(request, Field('+330956218175'))  # FR
    validator(request, Field('+390612345678'))  # IT

    validator(request, Field('+41791112233'))
    validator(request, Field('0041791112233'))
    validator(request, Field('0791112233'))

    def error(data: int | str | None) -> str:
        with raises(ValidationError) as exception:
            validator(request, Field(data))
        return exception.value.args[0].interpolate()

    # numbers that cannot be parsed at all
    assert error(1234) == 'Not a valid phone number.'
    assert error('not a number') == 'Not a valid phone number.'

    # an unknown country code is rejected by the parser
    assert error('+9991234567') == 'Not a valid country code.'
    assert error('+99912345') == 'Not a valid country code.'

    # swiss numbers are 9 or 12 digits long, everything else is invalid
    invalid_length = 'This phone number has an invalid length.'
    assert error('1234') == invalid_length
    assert error('00791112233') == invalid_length
    assert error('+417911122334455') == invalid_length
    assert error('079111223344556677') == invalid_length
    assert error('+417911122333') == invalid_length
    assert error('+4179111223344') == invalid_length

    # plausible length, but no such number exists
    assert error('041791112233') == 'This phone number does not exist.'

    validator = ValidPhoneNumber(country='US')
    assert error('2345678') == 'Please include the area code.'

    validator = ValidPhoneNumber(phone_type=PhoneNumberType.ANY.value)
    validator(request, Field('+41791112233'))
    validator(request, Field('0041791112233'))
    validator(request, Field('41791112233'))
    validator(request, Field('41791112233'))
    validator(request, Field('41781112233'))
    validator(request, Field('41771112233'))
    validator(request, Field('41761112233'))
    validator(request, Field('41411112233'))

    validator = ValidPhoneNumber(phone_type=PhoneNumberType.MOBILE.value)
    validator(request, Field('+41791112233'))
    validator(request, Field('0041791112233'))
    validator(request, Field('41791112233'))
    validator(request, Field('41791112233'))
    validator(request, Field('41781112233'))
    validator(request, Field('41771112233'))
    validator(request, Field('41761112233'))
    assert error('41411112233') == 'Please enter a mobile phone number.'

    validator = ValidPhoneNumber(phone_type=PhoneNumberType.FIXED_LINE.value)
    landline = 'Please enter a landline phone number.'
    assert error('+41791112233') == landline
    assert error('0041791112233') == landline
    assert error('41791112233') == landline
    assert error('41781112233') == landline
    assert error('41771112233') == landline
    assert error('41761112233') == landline
    validator(request, Field('41411112233'))

    # the number type is only checked once the number itself is valid
    assert error('041791112233') == 'This phone number does not exist.'

    validator = ValidPhoneNumber(country_whitelist={'CH'})
    validator(request, Field(None))
    validator(request, Field(''))

    validator(request, Field('+41791112233'))
    validator(request, Field('0041791112233'))
    validator(request, Field('0791112233'))

    # not a swiss number
    unsupported = 'Phone numbers from this country are not supported.'
    assert error('+4909562181751') == (  # DE
        f'{unsupported} Allowed countries: CH'
    )

    # the whitelist is listed in a stable order
    validator = ValidPhoneNumber(country_whitelist={'LI', 'CH', 'AT'})
    assert error('+4909562181751') == (  # DE
        f'{unsupported} Allowed countries: AT, CH, LI'
    )

    # every whitelisted country is accepted
    validator(request, Field('+41791112233'))  # CH
    validator(request, Field('+4319876543'))  # AT
    validator(request, Field('+4232371234'))  # LI

    # numbers from anywhere else are not, no matter how far away
    assert error('+390612345678').startswith(unsupported)  # IT
    assert error('+12025550123').startswith(unsupported)  # US

    # an invalid number is reported as such, not as a country problem
    assert error('+417911122333') == invalid_length
    assert error('+42366012345') == invalid_length

    # the whitelist is combined with the other checks
    validator = ValidPhoneNumber(
        country_whitelist={'CH', 'AT'},
        phone_type=PhoneNumberType.MOBILE.value
    )
    validator(request, Field('+41791112233'))
    assert error('+41411112233') == 'Please enter a mobile phone number.'
    assert error('+390612345678').startswith(unsupported)  # IT

    # the default country has to be part of the whitelist
    with raises(AssertionError) as ex:
        ValidPhoneNumber(country='DE', country_whitelist={'CH'})
    assert "Invalid country code: DE. Allowed are: ['CH']" in str(ex.value)


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

    validator = ImageSizeLimit()
    assert validator.max_bytes == ImageSizeLimit.DEFAULT_MAX_BYTES

    # no data — pass
    validator(None, Field(None))  # type: ignore[arg-type]

    # within limit — pass
    validator(None, Field(ImageSizeLimit.DEFAULT_MAX_BYTES))  # type: ignore[arg-type]

    # exceeds limit — fail
    with raises(ValidationError):
        validator(None, Field(ImageSizeLimit.DEFAULT_MAX_BYTES + 1))  # type: ignore[arg-type]

    # custom limit
    with raises(ValidationError):
        ImageSizeLimit(max_bytes=1024)(None, Field(1025))  # type: ignore[arg-type]

    with raises(ValidationError, match='The image is too large,'):
        validator(None, Field(ImageSizeLimit.DEFAULT_MAX_BYTES + 1))  # type: ignore[arg-type]


def test_image_file_size_limit_on_upload_field() -> None:
    limit = 2_000  # 2 KB

    class PhotoForm(Form):
        photo = UploadField(validators=[ImageSizeLimit(max_bytes=limit)])

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
                ImageSizeLimit(max_bytes=limit),
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


def test_image_size_limit_resizes_large_image() -> None:
    """max_dimensions triggers automatic resampling before the byte check."""

    max_dim = 100

    class PhotoForm(Form):
        photo = UploadField(
            validators=[ImageSizeLimit(max_dimensions=max_dim)]
        )

    def make_form(img: Image.Image, fmt: str) -> PhotoForm:
        buf = BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        data: Any = FileMultiDict()
        data.add_file('photo', buf, filename=f'test.{fmt.lower()}')
        return PhotoForm(data)

    # Image larger than max_dim — should be resized and pass validation
    large = make_form(Image.new('RGB', (500, 500), color=(0, 128, 0)), 'JPEG')
    assert large.validate(), large.photo.errors
    # field.data reflects the resized image
    assert large.photo.data is not None
    assert large.photo.data.get('size', 0) > 0

    # Image already within limit — should pass untouched
    small = make_form(Image.new('RGB', (50, 50), color=(0, 0, 255)), 'JPEG')
    assert small.validate(), small.photo.errors

    # Image too large even after resizing (byte limit very tight)
    class TightForm(Form):
        photo = UploadField(
            validators=[ImageSizeLimit(max_bytes=1, max_dimensions=max_dim)]
        )

    def make_tight(img: Image.Image, fmt: str) -> TightForm:
        buf = BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        data: Any = FileMultiDict()
        data.add_file('photo', buf, filename=f'test.{fmt.lower()}')
        return TightForm(data)

    tight = make_tight(Image.new('RGB', (500, 500), color=(255, 0, 0)), 'JPEG')
    assert not tight.validate()
    assert tight.photo.errors
    assert 'The image is too large,' in tight.photo.errors[0]


def test_image_size_limit_output_dimensions() -> None:
    """Resized image dimensions are within max_dimensions; aspect
    ratio kept."""
    from onegov.core.utils import dictionary_to_binary

    max_dim = 100

    class PhotoForm(Form):
        photo = UploadField(
            validators=[ImageSizeLimit(max_dimensions=max_dim)])

    def submit(img: Image.Image, fmt: str) -> PhotoForm:
        buf = BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        data: Any = FileMultiDict()
        data.add_file('photo', buf, filename=f'test.{fmt.lower()}')
        form = PhotoForm(data)
        assert form.validate(), form.photo.errors
        return form

    def decoded_size(form: PhotoForm) -> tuple[int, int]:
        assert form.photo.data is not None
        return Image.open(BytesIO(dictionary_to_binary(form.photo.data))).size  # type: ignore[arg-type]

    # Square: both sides land exactly on max_dim
    w, h = decoded_size(submit(Image.new('RGB', (500, 500)), 'JPEG'))
    assert w == max_dim and h == max_dim

    # Landscape: width is the long side → clamped to max_dim, height scales
    w, h = decoded_size(submit(Image.new('RGB', (600, 300)), 'JPEG'))
    assert w == max_dim
    assert h == 50  # 300 × (100/600)

    # Portrait: height is the long side → height clamped, width scales
    w, h = decoded_size(submit(Image.new('RGB', (300, 600)), 'JPEG'))
    assert w == 50  # 300 × (100/600)
    assert h == max_dim

    # PNG format — quality param is unsupported, must not raise
    w, h = decoded_size(submit(Image.new('RGB', (500, 500)), 'PNG'))
    assert w == max_dim and h == max_dim


def test_image_size_limit_size_field_updated_after_resize() -> None:
    """field.data['size'] reflects the resized byte count, not the original."""
    max_dim = 50

    class PhotoForm(Form):
        photo = UploadField(
            validators=[ImageSizeLimit(max_dimensions=max_dim)])

    original = Image.new('RGB', (800, 800), color=(128, 64, 32))
    buf = BytesIO()
    original.save(buf, format='JPEG')
    original_size = buf.tell()
    buf.seek(0)

    data: Any = FileMultiDict()
    data.add_file('photo', buf, filename='test.jpg')
    form = PhotoForm(data)
    assert form.validate(), form.photo.errors

    assert form.photo.data is not None
    stored_size = form.photo.data['size']
    assert stored_size < original_size


def test_image_size_limit_no_resize_when_within_limit() -> None:
    """Images already within max_dimensions are stored unchanged."""
    max_dim = 200

    class PhotoForm(Form):
        photo = UploadField(
            validators=[ImageSizeLimit(max_dimensions=max_dim)])

    img = Image.new('RGB', (100, 80), color=(0, 200, 100))
    buf = BytesIO()
    img.save(buf, format='JPEG')
    original_size = buf.tell()
    buf.seek(0)

    data: Any = FileMultiDict()
    data.add_file('photo', buf, filename='small.jpg')
    form = PhotoForm(data)
    assert form.validate(), form.photo.errors

    # byte count must not increase (no re-encoding happened)
    assert form.photo.data is not None
    assert form.photo.data['size'] == original_size


def test_image_size_limit_exif_orientation_baked_in() -> None:
    """When resize happens, EXIF rotation is baked into the pixel data."""
    from onegov.core.utils import dictionary_to_binary

    # Build a minimal JPEG with EXIF orientation=6 (90° CW → swap W/H)
    # We construct only the EXIF IFD bytes we need; Pillow reads them on open.
    def jpeg_with_exif_orientation(
        width: int, height: int, orientation: int
    ) -> bytes:
        img = Image.new('RGB', (width, height), color=(200, 100, 50))
        exif = img.getexif()
        exif[0x0112] = orientation  # 0x0112 = Orientation tag
        buf = BytesIO()
        img.save(buf, format='JPEG', exif=exif.tobytes())
        buf.seek(0)
        return buf.read()

    max_dim = 100
    # 300 wide × 600 tall, orientation=6 means "rotate 90° CW" →
    # effective 600×300
    raw = jpeg_with_exif_orientation(300, 600, orientation=6)

    class PhotoForm(Form):
        photo = UploadField(
            validators=[ImageSizeLimit(max_dimensions=max_dim)])

    data: Any = FileMultiDict()
    data.add_file('photo', BytesIO(raw), filename='rotated.jpg')
    form = PhotoForm(data)
    assert form.validate(), form.photo.errors

    assert form.photo.data is not None
    result = Image.open(BytesIO(dictionary_to_binary(form.photo.data)))  # type: ignore[arg-type]
    # After baking orientation=6 the image is 600×300 (landscape).
    # Resized to max_dim=100: width=100, height=50.
    assert result.size == (max_dim, 50)
    # EXIF block should be cleared (no Orientation tag left)
    assert result.getexif().get(0x0112) is None
