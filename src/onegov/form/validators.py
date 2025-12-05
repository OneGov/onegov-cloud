from __future__ import annotations

import humanize
import importlib
import phonenumbers

from babel.dates import format_date
from bad_passwords import is_bad_password
from cgi import FieldStorage
from datetime import date
from datetime import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from mimetypes import types_map
from onegov.form import _
from onegov.form.errors import (DuplicateLabelError, InvalidIndentSyntax,
                                EmptyFieldsetError)
from onegov.form.errors import FieldCompileError
from onegov.form.errors import InvalidFormSyntax
from onegov.form.errors import MixedTypeError
from onegov.form.types import BaseFormT, FieldT
from stdnum.exceptions import (
    ValidationError as StdnumValidationError)
from wtforms import DateField, DateTimeLocalField, RadioField, TimeField
from wtforms.fields import SelectField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import StopValidation
from wtforms.validators import ValidationError


from typing import Generic, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from onegov.core.orm import Base
    from onegov.form import Form
    from onegov.form.types import BaseValidator, FieldCondition
    from wtforms import Field, StringField
    from wtforms.form import BaseForm


# HACK: We extend the default type map with additional entries for file endings
#       that sometimes don't have a single agreed upon mimetype, we may need
#       to do something more clever in the future and map single file endings
#       to multiple mime types.
types_map.setdefault('.mp3', 'audio/mpeg')


class If(Generic[BaseFormT, FieldT]):
    """ Wraps a single validator or a list of validators, which will
    only be executed if the supplied condition callback returns `True`.

    """
    def __init__(
        self,
        condition: FieldCondition[BaseFormT, FieldT],
        *validators: BaseValidator[BaseFormT, FieldT]
    ):
        assert len(validators) > 0, 'Need to supply at least one validator'
        self.condition = condition
        self.validators = validators

    def __call__(self, form: BaseFormT, field: FieldT) -> None:
        if not self.condition(form, field):
            return

        for validator in self.validators:
            validator(form, field)


class Stdnum:
    """ Validates a string using any python-stdnum format.

    See `<https://github.com/arthurdejong/python-stdnum>`_.

    """
    def __init__(self, format: str):
        module = '.'.join(p for p in format.split('.') if p)
        self.format = importlib.import_module('stdnum.' + module)

    def __call__(self, form: Form, field: Field) -> None:
        # only do a check for filled out values, to check for the existance
        # of any value use DataRequired!
        if not field.data:
            return

        try:
            self.format.validate(field.data)
        except StdnumValidationError as exception:
            raise ValidationError(
                field.gettext('Invalid input.')
            ) from exception


class FileSizeLimit:
    """ Makes sure an uploaded file is not bigger than the given number of
    bytes.

    Expects an :class:`onegov.form.fields.UploadField` or
    :class:`onegov.form.fields.UploadMultipleField` instance.

    """

    message = _(
        'The file is too large, please provide a file smaller than {}.'
    )

    def __init__(self, max_bytes: int):
        self.max_bytes = max_bytes

    def __call__(self, form: Form, field: Field) -> None:
        if not field.data:
            return

        if isinstance(field.data, list):  # UploadMultipleField
            for data in field.data:
                if not data:
                    continue  # in case of file deletion

                self.validate_filesize(field, data)

        else:
            self.validate_filesize(field, field.data)

    def validate_filesize(self, field: Field, data: dict[Any, Any]) -> None:
        if data.get('size', 0) > self.max_bytes:
            message = field.gettext(self.message).format(
                humanize.naturalsize(self.max_bytes)
            )
            raise ValidationError(message)


MIME_TYPES_PDF = {
    'application/pdf',
}

# for now not allowed by default
MIME_TYPES_JSON = {
    'application/json',
}

MIME_TYPES_DOCUMENT = {
    'application/msword',  # doc
    'application/rtf',
    *MIME_TYPES_PDF,
    'application/vnd.ms-excel',  # xls
    ('application/vnd.openxmlformats-officedocument.'
     'presentationml.presentation'),  # pptx
    ('application/vnd.openxmlformats-officedocument.'
     'spreadsheetml.sheet'),  # xlsx
    ('application/vnd.openxmlformats-officedocument.'
     'wordprocessingml.document'),  # docx
    'application/CDFV2',  # old ms office docs
    'application/x-ole-storage',  # old ms office docs
    'application/CDFV2-unknown'  # old ms office docs
}

MIME_TYPES_XML = {
    'application/xml',
}

MIME_TYPES_ARCHIVE = {
    'application/zip',
}

MIME_TYPES_TEXT_DATA = {
    'text/csv',
    'text/plain',
}

MIME_TYPES_IMAGE = {
    'image/bmp',
    'image/gif',
    'image/jpeg',  # jpeg, jpg
    'image/png',
    'image/svg+xml',
    'image/tiff',
    'image/webp',  # shall we allow it?
    'image/x-ms-bmp',
}

MIME_TYPES_AUDIO = {
    'audio/mp4',
    'audio/mpeg',
    'audio/wav',
    'audio/webm',  # weba
}

MIME_TYPES_VIDEO = {
    'video/mp4',
    'video/mpeg',  # mpg, mpeg
    'video/ogg',
    'video/quicktime',  # mov
    'video/webm',  # webm
    'video/x-msvideo',  # avi
}


class WhitelistedMimeType:
    """ Makes sure an uploaded file is in a whitelist of allowed mimetypes.

    Expects an :class:`onegov.form.fields.UploadField` or
    :class:`onegov.form.fields.UploadMultipleField` instance.
    """

    whitelist: Collection[str] = {
        *MIME_TYPES_DOCUMENT,
        *MIME_TYPES_XML,
        *MIME_TYPES_ARCHIVE,
        *MIME_TYPES_TEXT_DATA,
        *MIME_TYPES_IMAGE,
        *MIME_TYPES_AUDIO,
        *MIME_TYPES_VIDEO,
    }

    message = _('Files of this type are not supported.')

    def __init__(self, whitelist: Collection[str] | None = None):
        if whitelist is not None:
            self.whitelist = whitelist

    def __call__(self, form: Form, field: Field) -> None:
        if not field.data:
            return

        if isinstance(field.data, list):  # UploadMultipleField
            for data in field.data:
                if not data:
                    continue  # in case of file deletion

                self.validate_mimetype(field, data)

        else:
            self.validate_mimetype(field, field.data)

    def validate_mimetype(self, field: Field, data: dict[Any, Any]) -> None:
        if data['mimetype'] not in self.whitelist:
            message = field.gettext(self.message)
            raise ValidationError(field.gettext(message))


class ExpectedExtensions(WhitelistedMimeType):
    """ Makes sure an uploaded file has one of the expected extensions. Since
    extensions are not something we can count on we look up the mimetype of
    the extension and use that to check.

    Expects an :class:`onegov.form.fields.UploadField` instance.

    Usage::

        ExpectedExtensions(['*'])  # default whitelist
        ExpectedExtensions(['pdf'])  # makes sure the given file is a pdf
    """

    def __init__(self, extensions: Sequence[str]):
        # normalize extensions
        if len(extensions) == 1 and extensions[0] == '*':
            mimetypes = None
        else:
            mimetypes = {
                mimetype for ext in extensions
                # we silently discard any extensions we don't know for now
                if (mimetype := types_map.get('.' + ext.lstrip('.'), None))
            }
        super().__init__(whitelist=mimetypes)


class ValidPassword(Length):
    """
    Makes sure the given password is not part of a list of commonly used
    passwords.
    """
    def __init__(
        self,
        min_length: int = 10,
        length_message: str | None = None
    ) -> None:
        assert min_length >= 10
        super().__init__(min=min_length, message=length_message)

    def __call__(self, form: BaseForm, field: StringField) -> None:
        super().__call__(form, field)
        assert field.data is not None
        if is_bad_password(field.data):
            raise ValidationError(_(
                'The password you wanted to use was found on '
                'list of commonly used passwords, please use '
                'a more secure password.'
            ))


class ValidFormDefinition:
    """ Makes sure the given text is a valid onegov.form definition. """

    message = _('The form could not be parsed.')
    email = _("Define at least one required e-mail field ('E-Mail * = @@@')")
    syntax = _('The syntax on line {line} is not valid.')
    indent = _('The indentation on line {line} is not valid. '
               'Please use a multiple of 4 spaces')
    duplicate = _("The field '{label}' exists more than once.")
    reserved = _("'{label}' is a reserved name. Please use a different name.")
    required = _('Define at least one required field')
    payment_method = _(
        "The field '{label}' contains a price that requires a credit card "
        "payment. This is only allowed if credit card payments are optional."
    )
    minimum_price = _(
        'A minimum price total can only be set if at least one priced field '
        'is defined.'
    )
    empty_fieldset = _(
        "The '{label}' group is empty and will not be visible. Either remove "
        "the empty group or add fields to it.")

    def __init__(
        self,
        require_email_field: bool = True,
        reserved_fields: Collection[str] | None = None,
        require_title_fields: bool = False,
        validate_prices: bool = True
    ):
        self.require_email_field = require_email_field
        self.reserved_fields = reserved_fields or set()
        self.require_title_fields = require_title_fields
        self.validate_prices = validate_prices

    def __call__(self, form: Form, field: Field) -> Form | None:
        if not field.data:
            return None

        try:
            parsed_form = self._parse_form(field)
        except InvalidFormSyntax as exception:
            field.render_kw = field.render_kw or {}
            field.render_kw['data-highlight-line'] = exception.line
            raise ValidationError(
                field.gettext(self.syntax).format(line=exception.line)
            ) from exception
        except InvalidIndentSyntax as exception:
            raise ValidationError(
                field.gettext(self.indent).format(line=exception.line)
            ) from exception
        except EmptyFieldsetError as exception:
            raise ValidationError(
                field.gettext(self.empty_fieldset).format(
                    label=exception.field_name)
            ) from exception
        except DuplicateLabelError as exception:
            raise ValidationError(
                field.gettext(self.duplicate).format(label=exception.label)
            ) from exception
        except (FieldCompileError, MixedTypeError) as exception:
            raise ValidationError(
                exception.field_name
            ) from exception
        except AttributeError as exception:
            raise ValidationError(
                field.gettext(self.message)
            ) from exception

        if self.require_email_field:
            if not parsed_form.has_required_email_field:
                raise ValidationError(field.gettext(self.email))

        if self.require_title_fields and not parsed_form.title_fields:
            raise ValidationError(field.gettext(self.required))

        if self.reserved_fields:
            for formfield_id, formfield in parsed_form._fields.items():
                if formfield_id in self.reserved_fields:

                    raise ValidationError(
                        field.gettext(self.reserved).format(
                            label=formfield.label.text
                        )
                    )

        if self.validate_prices and 'payment_method' in form:
            for formfield in parsed_form:
                if not hasattr(formfield, 'pricing'):
                    continue

                if not formfield.pricing.has_payment_rule:
                    continue

                # NOTE: If we end up allowing 'manual' in addition to
                #       'free' we should also check if the application
                #       has a payment_provider set.
                if form['payment_method'].data != 'free':
                    # add the error message to both affected fields
                    error = field.gettext(self.payment_method).format(
                        label=formfield.label.text
                    )
                    # if the payment_method field is below the form
                    # definition field, then validate will not have
                    # been run yet and we can only add process_errors
                    errors = form['payment_method'].errors
                    if not isinstance(errors, list):
                        errors = form['payment_method'].process_errors
                        assert isinstance(errors, list)

                    errors.append(error)
                    raise ValidationError(error)

        if self.validate_prices and 'minimum_price_total' in form:
            has_pricing = (
                hasattr(form, 'currency') and form.currency.data
                or any(hasattr(formfield, 'pricing')
                       for formfield in parsed_form._fields.values()))

            if form['minimum_price_total'].data and not has_pricing:
                # add the error message to all affected fields
                # FIXME: ideally we would get more consistent about
                #        having a field like 'pricing_method' that
                #        we can attach this error to. It doesn't
                #        really make sense to show it on 'currency'
                error = field.gettext(self.minimum_price)
                # if the minimum_price_total field is below the form
                # definition field, then validate will not have
                # been run yet and we can only add process_errors
                errors = form['minimum_price_total'].errors
                if not isinstance(errors, list):
                    errors = form['minimum_price_total'].process_errors
                    assert isinstance(errors, list)

                errors.append(error)
                raise ValidationError(error)

        return parsed_form

    def _parse_form(
        self,
        field: Field,
        enable_edit_checks: bool = True
    ) -> Form:
        # XXX circular import
        from onegov.form import parse_form

        return parse_form(field.data,
                          enable_edit_checks=enable_edit_checks)()


class ValidFilterFormDefinition(ValidFormDefinition):
    invalid_field_type = _("Invalid field type for field '{label}'. For "
                           "filters only 'select' or 'multiple select' "
                           "fields are allowed.")

    def __call__(self, form: Form, field: Field) -> Form | None:
        from onegov.form.fields import MultiCheckboxField

        parsed_form = super().__call__(form, field)
        if parsed_form is None:
            return None

        # limit the definition to MultiCheckboxField, RadioField which can
        # be used for filter definition
        errors = None
        for field in parsed_form._fields.values():
            if not isinstance(field, (MultiCheckboxField, RadioField)):
                error = field.gettext(self.invalid_field_type.format(
                    label=field.label.text))
                errors = form['definition'].errors
                if not isinstance(errors, list):
                    errors = form['definition'].process_errors
                    assert isinstance(errors, list)
                errors.append(error)

        if errors:
            raise ValidationError()

        return parsed_form


class ValidSurveyDefinition(ValidFormDefinition):
    """ Makes sure the given text is a valid onegov.form definition for
    surveys.
    """

    def __init__(self, require_email_field: bool = False):
        super().__init__(require_email_field)

    invalid_field_type = _("Invalid field type for field '${label}'. Please "
                           "use the plus-icon to add allowed field types.")

    def __call__(self, form: Form, field: Field) -> Form | None:
        from onegov.form.fields import UploadField

        parsed_form = super().__call__(form, field)
        if parsed_form is None:
            return None

        # Exclude fields that are not allowed in surveys
        errors = None
        for field in parsed_form._fields.values():
            if isinstance(field, (UploadField, DateField, TimeField,
                                  DateTimeLocalField)):
                error = field.gettext(self.invalid_field_type %
                                      {'label': field.label.text})
                errors = form['definition'].errors
                if not isinstance(errors, list):
                    errors = form['definition'].process_errors
                    assert isinstance(errors, list)
                errors.append(error)

        if errors:
            raise ValidationError()

        return parsed_form


class LaxDataRequired(DataRequired):
    """ A copy of wtform's DataRequired validator, but with a more lax approach
    to required validation checking. It accepts some specific falsy values,
    such as numeric falsy values, that would otherwise fail DataRequired.

    This is necessary in order for us to validate stored submissions, which
    get validated after the initial submission in order to avoid losing file
    uploads.

    """

    def __call__(self, form: BaseForm, field: Field) -> None:
        if field.data is False:
            # guard against False, False is an instance of int, since
            # bool derives from int, so we need to check this first
            pass
        elif isinstance(field.data, (int, float, Decimal)):
            # we just accept any numeric data regardless of amount
            return

        # fall back to wtform's validator
        super().__call__(form, field)


class StrictOptional(Optional):
    """ A copy of wtform's Optional validator, but with a more strict approach
    to optional validation checking.

    See https://github.com/wtforms/wtforms/issues/350

    """

    def is_missing(self, value: object) -> bool:
        if isinstance(value, FieldStorage):
            return False

        if not value:
            return True

        if isinstance(value, str):
            return not self.string_check(value)

        return False

    def __call__(self, form: BaseForm, field: Field) -> None:
        raw = field.raw_data and field.raw_data[0]
        val = field.data

        # the selectfields have this annyoing habit of coercing all values
        # that are added to them -> this includes the None, which is turned
        # into 'None'
        if isinstance(field, SelectField) and val == 'None':
            val = None

        if self.is_missing(raw) and self.is_missing(val):
            field.errors = []
            raise StopValidation()


class ValidPhoneNumber:
    """ Makes sure the given input is valid phone number.

    Expects an :class:`wtforms.StringField` instance.

    """

    message = _('Not a valid phone number.')

    def __init__(
        self,
        country: str = 'CH',
        country_whitelist: Collection[str] | None = None
    ):
        if country_whitelist:
            assert country in country_whitelist

        self.country = country
        self.country_whitelist = country_whitelist

    def __call__(self, form: Form, field: Field) -> None:
        if not field.data:
            return

        try:
            number = phonenumbers.parse(field.data, self.country)
        except Exception as exception:
            raise ValidationError(self.message) from exception

        if self.country_whitelist:
            region = phonenumbers.region_code_for_number(number)
            if region not in self.country_whitelist:
                # FIXME: Better error message?
                raise ValidationError(self.message)

        if not (
            phonenumbers.is_valid_number(number)
            and phonenumbers.is_possible_number(number)
        ):
            raise ValidationError(self.message)


class ValidSwissSocialSecurityNumber:
    """ Makes sure the given input is a valid swiss social security number.

    Expects an :class:`wtforms.StringField` instance.

    """

    message = _('Not a valid swiss social security number.')

    def __init__(self) -> None:
        self.stdnum_validator = Stdnum(format='ch.ssn')

    def __call__(self, form: Form, field: Field) -> None:
        if not field.data:
            return

        try:
            self.stdnum_validator(form, field)
        except ValidationError:
            raise ValidationError(self.message) from None


class UniqueColumnValue:
    """ Test if the given table does not already have a value in the column
    (identified by the field name).

    If the form provides a model with such an attribute, we allow this
    value, too.

    Usage::

        username = StringField(validators=[UniqueColumnValue(User)])

    """

    def __init__(self, table: type[Base]):
        self.table = table

    def __call__(self, form: Form, field: Field) -> None:
        if field.name not in self.table.__table__.columns:  # type:ignore
            raise RuntimeError('The field name must match a column!')

        if hasattr(form, 'model'):
            if hasattr(form.model, field.name):
                if getattr(form.model, field.name) == field.data:
                    return

        column = getattr(self.table, field.name)
        query = form.request.session.query(column)
        query = query.filter(column == field.data)
        if query.first():
            raise ValidationError(_('This value already exists.'))


class InputRequiredIf(InputRequired):
    """ Validator which makes a field required if another field is set and has
    the given value.

    """

    def __init__(
        self,
        field_name: str,
        field_data: object,
        message: str | None = None
    ):
        self.field_name = field_name
        self.field_data = field_data
        self.message = message

    def __call__(self, form: BaseForm, field: Field) -> None:
        if self.field_name not in form:
            raise RuntimeError(f"No field named '{self.field_name}' in form")

        field_data = form[self.field_name].data
        filter_data = self.field_data
        if (
            field_data is None or filter_data is None
            or isinstance(field_data, bool)
            or isinstance(filter_data, bool)
        ):
            required = field_data is filter_data

        elif isinstance(filter_data, str) and filter_data.startswith('!'):
            required = field_data != filter_data[1:]
        else:
            required = field_data == filter_data

        if required:
            super().__call__(form, field)
        else:
            Optional().__call__(form, field)


class ValidDateRange:
    """
    Makes sure the selected date is in a valid range.

    The default error message can be overriden and be parametrized
    with ``min_date`` and ``max_date`` if both are supplied or just
    with ``date`` if only one of them is specified.

    """

    between_message = _('Needs to be between {min_date} and {max_date}.')
    after_message = _('Needs to be on or after {date}.')
    before_message = _('Needs to be on or before {date}.')

    def __init__(
        self,
        min: date | relativedelta | None = None,
        max: date | relativedelta | None = None,
        message: str | None = None
    ):
        self.min = min
        self.max = max
        if message is not None:
            self.message = message
        elif min is None:
            assert max is not None, 'Need to supply either min or max'
            self.message = self.before_message
        elif max is None:
            self.message = self.after_message
        else:
            self.message = self.between_message

    @property
    def min_date(self) -> date | None:
        if isinstance(self.min, relativedelta):
            return date.today() + self.min
        return self.min

    @property
    def max_date(self) -> date | None:
        if isinstance(self.max, relativedelta):
            return date.today() + self.max
        return self.max

    def __call__(self, form: Form, field: Field) -> None:
        if field.data is None:
            return

        value = field.data
        if isinstance(value, datetime):
            value = value.date()
        assert isinstance(value, date)

        if hasattr(form, 'request'):
            locale = form.request.locale
        else:
            locale = 'de_CH'

        min_date = self.min_date
        max_date = self.max_date
        if min_date is not None and max_date is not None:
            # FIXME: To be properly I18n just like with `Layout.format_date`
            #        the date format should depend on the locale.
            if not (min_date <= value <= max_date):
                min_str = format_date(
                    min_date, format='dd.MM.yyyy', locale=locale)
                max_str = format_date(
                    max_date, format='dd.MM.yyyy', locale=locale)
                raise ValidationError(field.gettext(self.message).format(
                    min_date=min_str, max_date=max_str
                ))

        elif min_date is not None and value < min_date:
            min_str = format_date(min_date, format='dd.MM.yyyy', locale=locale)
            raise ValidationError(
                field.gettext(self.message).format(date=min_str)
            )

        elif max_date is not None and value > max_date:
            max_str = format_date(max_date, format='dd.MM.yyyy', locale=locale)
            raise ValidationError(
                field.gettext(self.message).format(date=max_str)
            )
