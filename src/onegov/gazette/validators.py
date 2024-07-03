from wtforms.validators import ValidationError
from onegov.gazette import _


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from sqlalchemy.sql import ColumnElement
    from wtforms import Field


class UnusedColumnKeyValue:
    """ Test if the value is not used as a key in the given column.

    We assume that we can look up the old value of the field with the given
    name through the form's model when editing. If the values matches, no
    check is done.

    If we can't look up the old value we assume we are creating a new item and
    therefore the check is not done.

    """

    # FIXME: Technically this should be 'ColumnElement[Mapping[str, Any]]'
    #        but I don't think ColumnElement is covariant (it might be in
    #        SQLAlchemy 2.0, so we should try changing it when we upgrade)
    def __init__(self, column: 'ColumnElement[Any]') -> None:
        self.column = column

    def __call__(self, form: 'Form', field: 'Field') -> None:
        if not hasattr(form, 'model'):
            return

        if not hasattr(form.model, field.name):
            return

        data = getattr(form.model, field.name)
        if data != field.data:
            session = form.request.session
            query = session.query(self.column)
            query = query.filter(
                self.column.has_key(data)  # type:ignore[attr-defined]
            )
            if session.query(query.exists()).scalar():
                raise ValidationError(_("This value is in use."))
