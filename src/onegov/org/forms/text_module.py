from __future__ import annotations

from onegov.form import Form
from onegov.form.filters import strip_whitespace
from onegov.org import _
from onegov.pdf.pdf import TABLE_CELL_CHAR_LIMIT
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Length


class TextModuleForm(Form):

    name = StringField(
        label=_('Name'),
        description=_('Short name to identify the text module'),
        validators=[InputRequired()],
        filters=(strip_whitespace, ))

    text = TextAreaField(
        label=_('Text'),
        validators=[
            InputRequired(),
            Length(max=TABLE_CELL_CHAR_LIMIT)
        ],
        filters=(strip_whitespace, ),
        render_kw={'rows': 10, 'data-max-length': TABLE_CELL_CHAR_LIMIT})
