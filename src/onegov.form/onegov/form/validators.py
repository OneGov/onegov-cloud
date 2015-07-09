import importlib
import humanize

from mimetypes import types_map
from stdnum.exceptions import ValidationError as StdnumValidationError
from wtforms import ValidationError
from wtforms.fields.html5 import EmailField


class Stdnum(object):
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
            raise ValidationError(field.gettext(u'Invalid input.'))


class FileSizeLimit(object):
    """ Makes sure an uploaded file is not bigger than the given number of
    bytes.

    Expects an :class:`onegov.form.fields.UploadField` instance.

    """

    message = "The file is too large, please provide a file smaller than {}."

    def __init__(self, max_bytes):
        self.max_bytes = max_bytes

    def __call__(self, form, field):
        if field.data:
            if field.data.get('size', 0) > self.max_bytes:
                message = field.gettext(self.message).format(
                    humanize.naturalsize(self.max_bytes)
                )
                raise ValidationError(message)


class WhitelistedMimeType(object):
    """ Makes sure an uploaded file is in a whitelist of allowed mimetypes.

    Expects an :class:`onegov.form.fields.UploadField` instance.
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
    }

    message = "Files of this type are not supported."

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

        ExpectedFileType('*')  # no check, really
        ExpectedFileType('pdf')  # makes sure the given file is a pdf
    """

    def __init__(self, extensions):
        mimetypes = set(
            types_map.get('.' + ext.lstrip('.'), None) for ext in extensions)
        super(ExpectedExtensions, self).__init__(whitelist=mimetypes)


class ValidFormDefinition(object):
    """ Makes sure the given text is a valid onegov.form definition. """

    message = "The form could not be parsed."
    email = "Define at least one required e-mail field ('E-Mail * = @@@')"

    def __init__(self, require_email_field=True):
        self.require_email_field = require_email_field

    def __call__(self, form, field):
        if field.data:
            # XXX circular import
            from onegov.form.parser.core import parse_form

            try:
                form = parse_form(field.data)()
            except AttributeError:
                # TODO inform the user what the error was
                raise ValidationError(field.gettext(self.message))
            else:
                if self.require_email_field:
                    matches = form.match_fields(
                        include_classes=(EmailField, ),
                        required=True,
                        limit=1
                    )

                    if not matches:
                        raise ValidationError(field.gettext(self.email))
