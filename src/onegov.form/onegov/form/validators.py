import importlib

from mimetypes import types_map
from stdnum.exceptions import ValidationError as StdnumValidationError
from wtforms import ValidationError


class Stdnum(object):
    """ Validates a string using any python-stdnum format.

    See `<https://github.com/arthurdejong/python-stdnum>`_.

    """
    def __init__(self, format):
        module = '.'.join(p for p in format.split('.') if p)
        self.format = importlib.import_module('stdnum.' + module)

    def __call__(self, form, field):
        # only do a check for filled out values, to check for the existance
        # of any value use InputRequired!
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

    def __init__(self, max_bytes):
        self.max_bytes = max_bytes

    def __call__(self, form, field):
        if field.data:
            if field.data.get('size', 0) > self.max_bytes:
                raise ValidationError(field.gettext(u'Invalid input.'))


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

    def __init__(self, whitelist=None):
        if whitelist is not None:
            self.whitelist = whitelist

    def __call__(self, form, field):
        if field.data:
            if field.data['mimetype'] not in self.whitelist:
                raise ValidationError(field.gettext(u'Invalid input.'))


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
        mimetypes = set(types_map.get(ext, None) for ext in extensions)
        super(ExpectedExtensions, self).__init__(whitelist=mimetypes)
