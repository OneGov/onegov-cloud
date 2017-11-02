from wtforms.validators import ValidationError
from onegov.gazette import _


class UniqueColumnValue(object):
    """ Test if value is not already present in the given table column.

    We assume that we can look up the old value of the field with the given
    name through the form's model when editing. If the values matches, no
    check is done.

    If we can't look up the old value we assume we are creating a new item and
    therefore the check is done.

    """

    def __init__(self, table, message=None):
        self.table = table

    def __call__(self, form, field):
        if hasattr(form, 'model'):
            if hasattr(form.model, field.name):
                if getattr(form.model, field.name) == field.data:
                    return

        column = getattr(self.table, field.name)
        query = form.request.app.session().query(column)
        query = query.filter(column == field.data)
        if query.first():
            raise ValidationError(_("This value already exists."))


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
                    query = form.request.app.session().query(self.column)
                    query = query.filter(self.column.has_key(data))  # noqa
                    if query.first():
                        raise ValidationError(_("This value is in use."))
