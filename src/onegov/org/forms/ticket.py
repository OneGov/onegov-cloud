from __future__ import annotations

from onegov.chat import MessageFile
from onegov.core.security import Private
from onegov.form import Form
from onegov.form.fields import (ChosenSelectField,
                                ChosenSelectMultipleEmailField)
from onegov.form.fields import TextAreaFieldWithTextModules
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.filters import strip_whitespace
from onegov.form.validators import FileSizeLimit, StrictOptional
from onegov.form.widgets import TextAreaWithTextModules
from onegov.org import _
from onegov.pdf.pdf import TABLE_CELL_CHAR_LIMIT
from onegov.user import User
from onegov.user import UserCollection
from wtforms.fields import BooleanField
from wtforms.fields import TextAreaField
from functools import cached_property
from wtforms.validators import InputRequired
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


class TicketNoteForm(Form):

    text = TextAreaFieldWithTextModules(
        label=_('Text'),
        description=_('Your note about this ticket'),
        validators=[
            InputRequired(),
            Length(max=TABLE_CELL_CHAR_LIMIT)
        ],
        filters=(strip_whitespace, ),
        render_kw={'rows': 10, 'data-max-length': TABLE_CELL_CHAR_LIMIT})

    file = UploadFileWithORMSupport(
        label=_('Attachment'),
        file_class=MessageFile,
        validators=[
            Optional(),
            FileSizeLimit(10 * 1000 * 1000)
        ])


class TicketChatMessageForm(Form):

    text = TextAreaField(
        label=_('Message'),
        description=_('Your message'),
        validators=[
            InputRequired(),
            Length(max=TABLE_CELL_CHAR_LIMIT)
        ],
        filters=(strip_whitespace, ),
        render_kw={'rows': 5, 'data-max-length': TABLE_CELL_CHAR_LIMIT})

    def validate_text(self, field: TextAreaField) -> None:
        if not self.text.data or not self.text.data.strip():
            raise ValidationError(_('The message is empty'))


class InternalTicketChatMessageForm(TicketChatMessageForm):

    if TYPE_CHECKING:
        request: OrgRequest

    notify = BooleanField(
        label=_('Notify me about replies'),
        default=True,
    )

    def on_request(self) -> None:
        self.text.widget = TextAreaWithTextModules()
        if self.request.app.org.ticket_always_notify:
            if isinstance(self.notify.render_kw, dict):
                self.notify.render_kw.update({'disabled': True})
            else:
                self.notify.render_kw = {'disabled': True}  # type:ignore
            self.notify.description = _('Setting "Always notify" is active')


class ExtendedInternalTicketChatMessageForm(InternalTicketChatMessageForm):
    """ Extends the form with Email BCC-Fields. """

    email_bcc = ChosenSelectMultipleEmailField(
        label=_('BCC'),
        fieldset=('Email'),
        description=_('You can send a copy of the message to one or more '
                      'recipients'),
        validators=[StrictOptional()],
        choices=[]
    )

    email_attachment = UploadFileWithORMSupport(
        label=_('Attachment'),
        fieldset=_('Email'),
        file_class=MessageFile,
        validators=[
            Optional(),
            FileSizeLimit(10 * 1000 * 1000)
        ]
    )

    @cached_property
    def internal_email_recipients(self) -> tuple[tuple[str, str], ...]:
        query = self.request.session.query(User.username, User.title)
        query = query.filter(User.active)
        return tuple(
            (username, title) for username, title in query if '@' in username
        )

    def on_request(self) -> None:
        super().on_request()
        self.email_bcc.choices = self.internal_email_recipients  # type:ignore


class TicketAssignmentForm(Form):

    user = ChosenSelectField(
        _('User'),
        choices=[],
        validators=[
            InputRequired()
        ],
    )

    @property
    def username(self) -> str | None:
        if self.user.data in (choice[0] for choice in self.user.choices):
            query = self.request.session.query(User.username)
            return query.filter_by(id=self.user.data).scalar()
        return None

    def on_request(self) -> None:
        self.user.choices = [
            (
                str(user.id),
                f'{user.title} ({", ".join(str(g.name) for g in user.groups)})'
                if user.groups
                else user.title
            )
            for user in UserCollection(self.request.session).query()
            if (
                self.request.has_permission(self.model, Private, user)
                and user.active == True
            )
        ]


class TicketChangeTagForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    tag = ChosenSelectField(
        _('Tag'),
        choices=[],
    )

    def on_request(self) -> None:
        choices = self.tag.choices = [
            (tag, tag)
            for item in self.request.app.org.ticket_tags
            for tag in (item.keys() if isinstance(item, dict) else (item,))
        ]
        choices.insert(0, ('', ''))
