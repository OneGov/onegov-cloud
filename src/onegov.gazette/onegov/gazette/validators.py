from wtforms.validators import ValidationError
from onegov.gazette import _


class UniqueColumnValue(object):
    """ Test if the column value is not already used.

    A form field name can be specified which provided the old value.

    """

    def __init__(self, column, message=None, old_field=None):
        self.column = column
        self.message = message or _("This value already exists.")
        self.old_field = old_field

    def __call__(self, form, field):
        query = form.request.app.session().query(self.column)
        query = query.filter(self.column == field.data)
        if self.old_field and hasattr(form, self.old_field):
            query = query.filter(
                self.column != getattr(form, self.old_field).data
            )
        if query.first():
            raise ValidationError(self.message)
