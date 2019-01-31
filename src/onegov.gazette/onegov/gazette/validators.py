from wtforms.validators import ValidationError
from onegov.gazette import _


class UnusedColumnKeyValue(object):
    """ Test if the value is not used as a key in the given column.

    We assume that we can look up the old value of the field with the given
    name through the form's model when editing. If the values matches, no
    check is done.

    If we can't look up the old value we assume we are creating a new item and
    therefore the check is not done.

    """

    def __init__(self, column):
        self.column = column

    def __call__(self, form, field):
        if hasattr(form, 'model'):
            if hasattr(form.model, field.name):
                data = getattr(form.model, field.name)
                if data != field.data:
                    query = form.request.session.query(self.column)
                    query = query.filter(self.column.has_key(data))  # noqa
                    if query.first():
                        raise ValidationError(_("This value is in use."))
