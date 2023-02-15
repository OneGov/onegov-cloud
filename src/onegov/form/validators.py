import humanize
import importlib
import phonenumbers
import re

from cgi import FieldStorage
from mimetypes import types_map
from onegov.form import _
from onegov.form.errors import DuplicateLabelError
from onegov.form.errors import FieldCompileError
from onegov.form.errors import InvalidFormSyntax
from stdnum.exceptions import ValidationError as StdnumValidationError
from wtforms.fields import SelectField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import StopValidation
from wtforms.validators import ValidationError


class Stdnum:
    """ Validates a string using any python-stdnum format.

    See `<https://github.com/arthurdejong/python-stdnum>`_.

    """
    def __init__(self, format):
        module = '.'.join(p for p in format.split('.') if p)
        self.format = importlib.import_module('stdnum.' + module)

    def __call__(self, form, field):
        # only do a check for filled out values, to check for the existance
        # of any value use DataRequired!
        if not field.data:
            return

        try:
            self.format.validate(field.data)
        except StdnumValidationError:
            raise ValidationError(field.gettext('Invalid input.'))


class FileSizeLimit:
    """ Makes sure an uploaded file is not bigger than the given number of
    bytes.

    Expects an :class:`onegov.form.fields.UploadField` or
    :class:`onegov.form.fields.UploadMultipleField` instance.

    """

    message = _(
        "The file is too large, please provide a file smaller than {}."
    )

    def __init__(self, max_bytes):
        self.max_bytes = max_bytes

    def __call__(self, form, field):
        if field.data:
            if field.data.get('size', 0) > self.max_bytes:
                message = field.gettext(self.message).format(
                    humanize.naturalsize(self.max_bytes)
                )
                raise ValidationError(message)


class WhitelistedMimeType:
    """ Makes sure an uploaded file is in a whitelist of allowed mimetypes.

    Expects an :class:`onegov.form.fields.UploadField` or
    :class:`onegov.form.fields.UploadMultipleField` instance.
    """

    whitelist = {
        'application/excel',
        'application/vnd.ms-excel',
        'application/msword',
        'application/pdf',
        'application/zip',
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/x-ms-bmp',
        'text/plain',
        'text/csv'
    }

    message = _("Files of this type are not supported.")

    def __init__(self, whitelist=None):
        if whitelist is not None:
            self.whitelist = whitelist

    def __call__(self, form, field):
        if field.data:
            if field.data['mimetype'] not in self.whitelist:
                raise ValidationError(field.gettext(self.message))


class ExpectedExtensions(WhitelistedMimeType):
    """ Makes sure an uploaded file has one of the expected extensions. Since
    extensions are not something we can count on we look up the mimetype of
    the extension and use that to check.

    Expects an :class:`onegov.form.fields.UploadField` instance.

    Usage::

        ExpectedExtensions(['*'])  # default whitelist
        ExpectedExtensions(['pdf'])  # makes sure the given file is a pdf
    """

    def __init__(self, extensions):
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


class ValidFormDefinition:
    """ Makes sure the given text is a valid onegov.form definition. """

    message = _("The form could not be parsed.")
    email = _("Define at least one required e-mail field ('E-Mail * = @@@')")
    syntax = _("The syntax on line {line} is not valid.")
    duplicate = _("The field '{label}' exists more than once.")
    reserved = _("'{label}' is a reserved name. Please use a different name.")
    required = _("Define at least one required field")
    payment_method = _(
        "The field '{label}' contains a price that requires a credit card "
        "payment. This is only allowed if credit card payments are optional."
    )
    minimum_price = _(
        "A minimum price total can only be set if at least one priced field "
        "is defined."
    )

    def __init__(self,
                 require_email_field=True,
                 reserved_fields=None,
                 require_title_fields=False,
                 validate_prices=True):
        self.require_email_field = require_email_field
        self.reserved_fields = reserved_fields or set()
        self.require_title_fields = require_title_fields
        self.validate_prices = validate_prices

    def __call__(self, form, field):
        if field.data:
            # XXX circular import
            from onegov.form import parse_form

            try:
                parsed_form = parse_form(field.data)()
            except InvalidFormSyntax as e:
                field.render_kw = field.render_kw or {}
                field.render_kw['data-highlight-line'] = e.line
                raise ValidationError(
                    field.gettext(self.syntax).format(line=e.line)
                )
            except DuplicateLabelError as e:
                raise ValidationError(
                    field.gettext(self.duplicate).format(label=e.label)
                )
            except FieldCompileError as e:
                raise ValidationError(e.field_name)
            except AttributeError:
                raise ValidationError(field.gettext(self.message))
            else:
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
                        if form.payment_method.data != 'free':
                            # add the error message to both affected fields
                            error = field.gettext(self.payment_method).format(
                                label=formfield.label.text
                            )
                            # if the payment_method field is below the form
                            # definition field, then validate will not have
                            # been run yet and we can only add process_errors
                            errors = form.payment_method.errors
                            if not isinstance(errors, list):
                                errors = form.payment_method.process_errors
                                assert isinstance(errors, list)

                            errors.append(error)
                            raise ValidationError(error)

                if self.validate_prices and 'minimum_price_total' in form:
                    has_pricing = (
                        hasattr(form, 'currency') and form.currency.data
                        or any(hasattr(formfield, 'pricing')
                               for formfield in parsed_form._fields.values()))

                    if form.minimum_price_total.data and not has_pricing:
                        # add the error message to all affected fields
                        # FIXME: ideally we would get more consistent about
                        #        having a field like 'pricing_method' that
                        #        we can attach this error to. It doesn't
                        #        really make sense to show it on 'currency'
                        error = field.gettext(self.minimum_price)
                        # if the minimum_price_total field is below the form
                        # definition field, then validate will not have
                        # been run yet and we can only add process_errors
                        errors = form.minimum_price_total.errors
                        if not isinstance(errors, list):
                            errors = form.minimum_price_total.process_errors
                            assert isinstance(errors, list)

                        errors.append(error)
                        raise ValidationError(error)


class StrictOptional(Optional):
    """ A copy of wtform's Optional validator, but with a more strict approach
    to optional validation checking.

    See https://github.com/wtforms/wtforms/issues/350

    """

    def is_missing(self, value):
        if isinstance(value, FieldStorage):
            return False

        if not value:
            return True

        if isinstance(value, str):
            return not self.string_check(value)

        return False

    def __call__(self, form, field):
        raw = field.raw_data and field.raw_data[0]
        val = field.data

        # the selectfields have this annyoing habit of coercing all values
        # that are added to them -> this includes the None, which is turned
        # into 'None'
        if isinstance(field, SelectField) and val == 'None':
            val = None

        if self.is_missing(raw) and self.is_missing(val):
            field.errors[:] = []
            raise StopValidation()


class ValidPhoneNumber:
    """ Makes sure the given input is valid phone number.

    Expects an :class:`wtforms.StringField` instance.

    """

    message = _("Not a valid phone number.")

    def __init__(self, country='CH'):
        self.country = country

    def __call__(self, form, field):
        if field.data:
            try:
                number = phonenumbers.parse(field.data, self.country)
            except Exception:
                raise ValidationError(self.message)

            valid = (
                phonenumbers.is_valid_number(number)
                and phonenumbers.is_possible_number(number)
            )
            if not valid:
                raise ValidationError(self.message)


swiss_ssn_rgxp = re.compile(r'756\.\d{4}\.\d{4}\.\d{2}$')


class ValidSwissSocialSecurityNumber:
    """ Makes sure the given input is a valid swiss social security number.

    Expects an :class:`wtforms.StringField` instance.

    """

    message = _("Not a valid swiss social security number.")

    def __call__(self, form, field):
        if field.data:
            if not re.match(swiss_ssn_rgxp, field.data):
                raise ValidationError(self.message)


class UniqueColumnValue:
    """ Test if the given table does not already have a value in the column
    (identified by the field name).

    If the form provides a model with such an attribute, we allow this
    value, too.

    Usage::

        username = StringField(validators=[UniqueColumnValue(User)])

    """

    def __init__(self, table):
        self.table = table

    def __call__(self, form, field):
        if field.name not in self.table.__table__.columns:
            raise RuntimeError("The field name must match a column!")

        if hasattr(form, 'model'):
            if hasattr(form.model, field.name):
                if getattr(form.model, field.name) == field.data:
                    return

        column = getattr(self.table, field.name)
        query = form.request.session.query(column)
        query = query.filter(column == field.data)
        if query.first():
            raise ValidationError(_("This value already exists."))


class InputRequiredIf(InputRequired):
    """ Validator which makes a field required if another field is set and has
    the given value.

    """

    def __init__(self, field_name, field_data, message=None, **kwargs):
        self.field_name = field_name
        self.field_data = field_data
        self.message = message

    def __call__(self, form, field):
        if not hasattr(form, self.field_name):
            raise RuntimeError("No field named '{}' not in form").format(
                self.field_name
            )

        values = (getattr(form, self.field_name).data, self.field_data)
        if any([isinstance(x, bool) or x is None for x in values]):
            required = values[0] is values[1]
        else:
            required = values[0] == values[1]
        if required:
            super(InputRequiredIf, self).__call__(form, field)
        else:
            Optional().__call__(form, field)
