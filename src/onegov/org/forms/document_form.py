from onegov.form import Form
from onegov.form.fields import HtmlField, UploadField
from onegov.form.validators import FileSizeLimit, WhitelistedMimeType
from onegov.org import _
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired


class DocumentForm(Form):

    title = StringField(
        label=_('Title'),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes briefly what this entry is about'),
        validators=[],
        render_kw={'rows': 4})

    text = HtmlField(
        label=_('Main Text help'))

    form_pdf = UploadField(
        label=_('Form PDF'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
    )

    group = StringField(
        label=_('Group'),
        description=_('Used to group this link in the overview')
    )
