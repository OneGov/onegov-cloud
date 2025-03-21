from __future__ import annotations

from onegov.form import Form
from onegov.gazette import _
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired


class EmptyForm(Form):

    pass


class RejectForm(Form):

    comment = TextAreaField(
        label=_('Comment'),
        validators=[
            InputRequired()
        ],
        render_kw={'rows': 4}
    )
