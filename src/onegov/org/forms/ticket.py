from onegov.chat import MessageFile
from onegov.form import Form
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.filters import strip_whitespace
from onegov.form.validators import FileSizeLimit
from onegov.org import _
from wtforms import BooleanField, TextAreaField
from wtforms import validators, ValidationError


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


class TicketChatMessageForm(Form):

    text = TextAreaField(
        label=_("Message"),
        description=_("Your message"),
        validators=[validators.InputRequired()],
        filters=(strip_whitespace, ),
        render_kw={'rows': 5})

    def validate_text(self, field):
        if not self.text.data or not self.text.data.strip():
            raise ValidationError(_("The message is empty"))


class InternalTicketChatMessageForm(TicketChatMessageForm):

    notify = BooleanField(label=_("Notify me about replies"))
