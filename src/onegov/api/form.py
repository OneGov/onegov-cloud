from __future__ import annotations

import humanize

from abc import abstractmethod, ABC
from datetime import date, time
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from onegov.core.utils import binary_to_dictionary
from onegov.form.fields import HoneyPotField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import If
from onegov.form.validators import Stdnum
from onegov.form.validators import ValidDateRange
from onegov.form.validators import WhitelistedMimeType
from pydantic import create_model, model_validator
from pydantic import AfterValidator, BaseModel, Field
from pydantic import AwareDatetime, Base64Bytes, EmailStr, HttpUrl
from wtforms import HiddenField
from wtforms.validators import DataRequired, InputRequired, Optional
from wtforms.validators import Email, Length, NumberRange, Regexp


from typing import Annotated, Any, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence
    from onegov.core.types import FileDict
    from onegov.form import Form
    from onegov.form.core import FieldDependency
    from onegov.form.types import Validator
    from typing_extensions import TypeForm
    from wtforms import Field as WTField


type ValidatorAdapter[T: Validator[Any, Any]] = Callable[[T], Any]

_A = TypeVar('_A', bound='BaseAdapter')
_V = TypeVar('_V', bound='ValidatorAdapter[Any]')


class AdapterRegistry:
    """ Keeps track of all the adapters and WTForms field types
    they are registered for, making sure each adapter is only
    instantiated once.

    """
    adapter_map: dict[str, BaseAdapter]
    validator_map: dict[type[Any], ValidatorAdapter[Any]]

    def __init__(self) -> None:
        self.adapter_map = {}
        self.validator_map = {}

    def register_for(self, *types: str) -> Callable[[type[_A]], type[_A]]:
        """ Decorator to register a field adapter. """
        def wrapper(adapter: type[_A]) -> type[_A]:
            instance = adapter()

            for type in types:
                assert type not in self.adapter_map
                self.adapter_map[type] = instance
            return adapter
        return wrapper

    def validator(self, validator: type[Any]) -> Callable[[_V], _V]:
        """ Decorator to register a validator adapter. """
        def wrapper(adapter: _V) -> _V:
            assert validator not in self.validator_map
            self.validator_map[validator] = adapter
            return adapter
        return wrapper

    def adapt(self, field: WTField) -> Generator[Any]:
        """ Adapts the WTForms field to a pydantic field yielding a
        sequence of values starting with a type form, followed by
        any number of pydantic metadata objects.

        This output will get unpacked into `Annotated`.

        """
        adapter = self.adapter_map[field.type]
        return adapter(field)

    def adapt_validator(self, validator: Validator[Any, Any]) -> Any:
        adapter = self.validator_map[validator.__class__]
        return adapter(validator)


registry = AdapterRegistry()


@registry.validator(Length)
def adapt_length(validator: Length) -> Any:
    return Field(
        min_length=None if validator.min < 0 else validator.min,
        max_length=None if validator.max < 0 else validator.max
    )


@registry.validator(Regexp)
def adapt_regexp(validator: Regexp) -> Any:
    return Field(pattern=validator.regex)


@registry.validator(NumberRange)
def adapt_number_range(validator: NumberRange) -> Any:
    return Field(ge=validator.min, le=validator.max)


@registry.validator(ValidDateRange)
def adapt_valid_date_range(validator: ValidDateRange) -> Any:
    ge = validator.min
    if isinstance(ge, relativedelta):
        ge = date.today() + ge
    # NOTE: In order to get the correct behavior for datetimes
    #       we convert to an exclusive end
    # FIXME: Will automatic coercion work for datetime, even
    #        though the datetimes will be timezone aware? If
    #        not we may need to emit a custom AfterValidator instead
    lt = validator.max
    if isinstance(lt, relativedelta):
        lt = date.today() + lt
    if lt is not None:
        lt += relativedelta(days=1)
    return Field(ge=ge, lt=lt)


@registry.validator(Stdnum)
def adapt_stdnum(validator: Stdnum) -> Any:
    def validate_stdnum(value: str | None) -> str | None:
        if value is None:
            return None
        validator.format.validate(value)
        return value
    return AfterValidator(validate_stdnum)


@registry.validator(FileSizeLimit)
def adapt_file_size_limit(validator: FileSizeLimit) -> Any:
    def validate_file_size(value: FileDict) -> FileDict:
        if not value:
            return value  # type: ignore[unreachable]
        if value.get('size', 0) > validator.max_bytes:
            raise ValueError(str(validator.message).format(
                humanize.naturalsize(validator.max_bytes)
            ))
        return value
    return AfterValidator(validate_file_size)


class BaseAdapter(ABC):
    """ Provides utility functions for all adapters. """

    def handle_scalar_field_type(
        self,
        t: TypeForm[Any],
        field: WTField
    ) -> tuple[Any, ...]:
        if not hasattr(field, 'depends_on') and any(
            isinstance(validator, (InputRequired, DataRequired))
            for validator in field.validators
        ):
            # NOTE: This is a bit of a hack to avoid emitting an
            #       Annotated without metadata
            return t, Field()

        default = field.default
        if callable(default):
            default = default()

        if default is None:
            return t | None, Field(default=None)
        if callable(field.default):
            return t, Field(default_factory=field.default)
        return t, Field(default=default)

    def handle_sequence_field_type(
        self,
        t: TypeForm[Any],
        field: WTField
    ) -> Generator[Any]:

        yield list[t]  # type: ignore[valid-type]

        if not hasattr(field, 'depends_on') and any(
            isinstance(validator, (InputRequired, DataRequired))
            for validator in field.validators
        ):
            yield Field(min_length=1)
            return

        if callable(default := field.default):
            yield Field(default_factory=default)
        else:
            yield Field(default=default)

    def adapt_validators(
        self,
        validators: Sequence[Validator[Any, Any]] | None
    ) -> Generator[Any]:
        if not validators:
            return

        if isinstance(validators[0], If):
            validators = validators[0].validators

        for validator in validators:
            if isinstance(validator, (
                # already handled via maybe_optional
                Optional, InputRequired, DataRequired,
                # already special-cased in Email field adapter
                Email,
                # already special-cased in upload field adapter
                WhitelistedMimeType,
            )):
                continue

            yield registry.adapt_validator(validator)

    @abstractmethod
    def __call__(self, field: WTField) -> Generator[Any]:
        raise NotImplementedError


@registry.register_for(
    'StringField',
    'TextAreaField',
    'PasswordField'
)
class StringFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(str, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for('EmailField')
class EmailFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(EmailStr, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for(
    'URLField',
    'VideoURLField'
)
class URLFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(HttpUrl, field)
        # NOTE: Coerce from HttpUrl | None back to str | None
        yield AfterValidator(lambda v: None if v is None else str(v))
        yield from self.adapt_validators(field.validators)


@registry.register_for('DateField')
class DateFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(date, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for(
    'DateTimeLocalField',
    'TimezoneDateTimeField'
)
class DateTimeFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(AwareDatetime, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for('TimeField')
class TimeFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(time, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for('DecimalField')
class DecimalFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(Decimal, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for('IntegerField')
class IntegerFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(int, field)
        yield from self.adapt_validators(field.validators)


@registry.register_for('RadioField')
class RadioFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(Literal[*(  # type: ignore[arg-type]
            value
            for value, _ in field.choices  # type: ignore[attr-defined]
            if value
        )], field)
        yield from self.adapt_validators(field.validators)


@registry.register_for('MultiCheckboxField')
class MultiCheckboxFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_sequence_field_type(Literal[*(  # type: ignore[arg-type]
            value
            for value, _ in field.choices  # type: ignore[attr-defined]
            if value
        )], field)
        yield from self.adapt_validators(field.validators)


class FileUpload(BaseModel):
    filename: str
    data: Base64Bytes


def mimetypes_validator(
    mimetypes: set[str]
) -> Callable[[FileDict], FileDict]:
    def validate_mimetype(value: FileDict) -> FileDict:
        if not value:
            return value  # type: ignore[unreachable]
        if value['mimetype'] not in mimetypes:
            raise ValueError(
                f'Unsupported mimetype. '
                f'Allowed mimetypes are {", ".join(mimetypes)}.'
            )
        return value
    return validate_mimetype


@registry.register_for('UploadField')
class UploadFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_scalar_field_type(FileUpload, field)
        # NOTE: Coerce from FileUpload to FileDict
        yield AfterValidator(
            lambda v: {} if v is None  # type: ignore[typeddict-item]
            else binary_to_dictionary(v.data, v.filename)
        )
        yield AfterValidator(mimetypes_validator(field.mimetypes))  # type: ignore[attr-defined]
        yield from self.adapt_validators(field.validators)


@registry.register_for('UploadMultipleField')
class UploadMultipleFieldAdapter(BaseAdapter):
    def __call__(self, field: WTField) -> Generator[Any]:
        yield from self.handle_sequence_field_type(
            Annotated[
                FileUpload,
                # NOTE: Coerce from FileUpload to FileDict
                AfterValidator(
                    lambda v: {} if v is None
                    else binary_to_dictionary(v.data, v.filename)
                ),
                AfterValidator(mimetypes_validator(field.mimetypes)),
                *self.adapt_validators(field.unbound_field.kwargs['validators'])
            ],
            field
        )


def dependency_fulfilled(self: FieldDependency, obj: object) -> bool:
    result = True
    for dependency in self.dependencies:
        data = getattr(obj, dependency['field_id'])
        choice = dependency['choice']
        invert = dependency['invert']

        if isinstance(data, bool) and choice in ('y', 'n'):
            choice = choice == 'y' and True or False

        result = result and ((data == choice) ^ invert)
    return result


def model_from_form(form: Form) -> type[BaseModel]:
    validators: dict[str, Any] = {}
    maybe_required_dependent_fields = {
        name: field.depends_on
        for name, field in form._fields.items()
        if hasattr(field, 'depends_on')
        if isinstance(field.validators[0], If)
        if any(
            isinstance(v, (InputRequired, DataRequired))
            for v in field.validators[0].validators
        )
    }
    if maybe_required_dependent_fields:
        @model_validator(mode='after')
        def validate_required_dependent_fields(self: Any) -> Any:
            for name, depends_on in maybe_required_dependent_fields.items():
                # if the value is something that will satisfy LaxDataRequired
                # then we accept it regardless of whether the dependency is
                # fulfilled
                value = getattr(self, name)
                if value is False:
                    # NOTE: we need to special-case this since bool is
                    #       an instance of int
                    pass
                elif isinstance(value, (int, float, Decimal)):
                    continue

                if isinstance(value, str) and value.strip():
                    continue

                if dependency_fulfilled(depends_on, self):
                    raise ValueError(
                        f'{name} is required due to your other submitted data'
                    )
            return self

        validators[
            'validate_required_dependent_fields'
        ] = validate_required_dependent_fields

    return create_model(
        f'{form.__class__.__name__}Model',
        __base__=None,
        __module__=form.__class__.__module__,
        __qualname__=None,
        __doc__=None,
        __config__={'frozen': True},
        __validators__=validators,
        __cls_kwargs__=None,
        **{
            name: Annotated[*registry.adapt(field)]
            for name, field in form._fields.items()
            if not isinstance(field, (HiddenField, HoneyPotField))
        }
    )
