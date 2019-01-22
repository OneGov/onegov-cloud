from onegov.chat import MessageFile
from onegov.form import Form
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.filters import strip_whitespace
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
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
        render_kw={'accept': '.pdf,.gif,.jpeg,.jpg,.png,.svg,.txt'},
        validators=[
            validators.Optional(),
            WhitelistedMimeType({
                'application/pdf',
                'image/gif',
                'image/jpeg',
                'image/png',
                'image/svg+xml',
                'text/plain',
            }),
            FileSizeLimit(5 * 1000 * 1000)
        ])
