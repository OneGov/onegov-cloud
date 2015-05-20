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
