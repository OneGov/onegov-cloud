from onegov.core.html import html_to_text
from wtforms.validators import ValidationError


class HtmlDataRequired(object):
    """ Checks the field's data contains text inside HTML otherwise stops the
    validation chain.

    """

    field_flags = ('required', )

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        data = html_to_text(field.data or '').strip()
        if not data:
            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message

            raise ValidationError(message)
