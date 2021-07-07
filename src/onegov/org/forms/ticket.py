from onegov.chat import MessageFile
from onegov.core.security import Private
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.filters import strip_whitespace
from onegov.form.validators import FileSizeLimit
from onegov.org import _
from onegov.pdf.pdf import TABLE_CELL_CHAR_LIMIT
from onegov.user import UserCollection
from wtforms import BooleanField
from wtforms import TextAreaField
from wtforms import ValidationError
from wtforms import validators


class TicketNoteForm(Form):

    text = TextAreaField(
        label=_("Text"),
        description=_("Your note about this ticket"),
        validators=[
            validators.InputRequired(),
            validators.Length(max=TABLE_CELL_CHAR_LIMIT)
        ],
        filters=(strip_whitespace, ),
        render_kw={'rows': 10, 'data-max-length': TABLE_CELL_CHAR_LIMIT})

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
        validators=[
            validators.InputRequired(),
            validators.Length(max=TABLE_CELL_CHAR_LIMIT)
        ],
        filters=(strip_whitespace, ),
        render_kw={'rows': 5, 'data-max-length': TABLE_CELL_CHAR_LIMIT})

    def validate_text(self, field):
        if not self.text.data or not self.text.data.strip():
            raise ValidationError(_("The message is empty"))


class InternalTicketChatMessageForm(TicketChatMessageForm):

    notify = BooleanField(
        label=_("Notify me about replies"),
    )

    def on_request(self):
        if self.request.app.org.ticket_always_notify:
            if isinstance(self.notify.render_kw, dict):
                self.notify.render_kw.update({'disabled': True})
            else:
                self.notify.render_kw = {'disabled': True}
            self.notify.description = _('Setting "Always notify" is active')


class TicketAssignmentForm(Form):

    user = ChosenSelectField(
        _('User'),
        choices=[],
        validators=[
            validators.InputRequired()
        ],
    )

    def on_request(self):
        self.user.choices = [
            (
                str(user.id),
                f'{user.title} ({user.group.name})' if user.group
                else user.title
            )
            for user in UserCollection(self.request.session).query()
            if self.request.has_permission(self.model, Private, user)
        ]
