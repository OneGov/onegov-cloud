import importlib

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


class ExpectedExtensions(object):
    """ Makes sure an uploaded file has one of the expected extensions.

    That doesn't necessarily mean the file is really what it claims to be.
    But that's not the concern of this validator. That is the job of
    :meth:`onegov.form.core.Form.load_file`.

    Usage::

        ExpectedFileType('*')  # no check, really
        ExpectedFileType('pdf')  # makes sure the given file is a pdf
    """

    def __init__(self, extensions):
        self.extensions = ['.' + ext.lstrip('.') for ext in extensions]

    def __call__(self, form, field):
        if not field.data:
            return

        if not field.data.endswith(self.extension):
            raise ValidationError(field.gettext(u'Invalid input.'))
