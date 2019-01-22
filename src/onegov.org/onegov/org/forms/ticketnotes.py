from onegov.chat import MessageFile
from onegov.form import Form
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.filters import strip_whitespace
from onegov.form.validators import FileSizeLimit
from onegov.org import _
from wtforms import TextAreaField
from wtforms import validators


class TicketNoteForm(Form):

    text = TextAreaField(
        label=_("Text"),
        description=_("Your note about this ticket"),
        validators=[validators.InputRequired()],
        filters=(strip_whitespace, ),
        render_kw={'rows': 10})

    file = UploadFileWithORMSupport(
        label=_("Attachment"),
        file_class=MessageFile,
        validators=[
            validators.Optional(),
            FileSizeLimit(10 * 1000 * 1000)
        ])
