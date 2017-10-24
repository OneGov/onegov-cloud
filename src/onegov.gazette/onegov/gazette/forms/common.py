from onegov.form import Form
from onegov.gazette import _
from wtforms import StringField
from wtforms.validators import InputRequired


class EmptyForm(Form):

    pass


class RejectForm(Form):

    comment = StringField(
        label=_("Comment"),
        validators=[
            InputRequired()
        ]
    )
