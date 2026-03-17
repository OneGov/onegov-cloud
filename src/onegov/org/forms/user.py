from __future__ import annotations

import re

from functools import cached_property
from onegov.core.utils import is_valid_yubikey_format
from onegov.directory.models.directory import Directory
from onegov.form import Form, merge_forms
from onegov.form import FormDefinition
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PanelField
from onegov.form.fields import TagsField
from onegov.form.filters import yubikey_identifier
from onegov.org import _, log
from onegov.reservation import Resource
from onegov.ticket import handlers, Ticket, TicketPermission
from onegov.user import Auth, User, UserCollection, UserGroup
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from onegov.org.request import OrgRequest
    from onegov.user.auth.second_factor import AnySecondFactor
    from wtforms.fields.choices import _Choice
    from wtforms.meta import _MultiDictLike


AVAILABLE_ROLES = [
    ('admin', _('Admin')),
    ('editor', _('Editor')),
    ('supporter', _('Supporter')),
    ('member', _('Member')),
]

TICKET_PERMISSION_RE = re.compile(r'(?P<handler>[^-]+)(?:-(?P<group>.+))?')


class ManageUserForm(Form):
    """ Defines the edit user form. """

    if TYPE_CHECKING:
        request: OrgRequest

    state = RadioField(
        label=_('State'),
        fieldset=_('General'),
        default='active',
        choices=(
            ('active', _('Active')),
            ('inactive', _('Inactive'))
        ),
    )

    role = RadioField(
        label=_('Role'),
        fieldset=_('General'),
        choices=AVAILABLE_ROLES,
        default='member',
    )

    tags = TagsField(
        label=_('Tags'),
        fieldset=_('General'),
    )

    yubikey = StringField(
        label=_('Yubikey'),
        fieldset=_('General'),
        description=_('Plug your YubiKey into a USB slot and press it.'),
        filters=(yubikey_identifier, ),
        render_kw={'autocomplete': 'off'}
    )

    @property
    def active(self) -> bool:
        return self.state.data == 'active'

    @active.setter
    def active(self, value: bool) -> None:
        self.state.data = value and 'active' or 'inactive'

    def on_request(self) -> None:
        # hide roles that are not configured for the current app
        roles_setting = self.request.app.settings.roles
        self.role.choices = [
            (role, label)
            for role, label in AVAILABLE_ROLES
            if hasattr(roles_setting, role)
        ]
        self.request.include('tags-input')

    def populate_obj(self, model: User) -> None:  # type:ignore
        if (
            model.role != self.role.data
            or model.active != self.active
        ):
            model.logout_all_sessions(self.request.app)

        super().populate_obj(model)
        model.active = self.active

    def process_obj(self, model: User) -> None:  # type:ignore
        super().process_obj(model)
        self.active = model.active

    def validate_yubikey(self, field: StringField) -> None:
        if not self.active:
            return

        if not field.data:
            if not self.request.app.enable_yubikey:
                return

            if self.role.data in ('admin', 'editor'):
                raise ValidationError(_(
                    'Administrators and editors must use a Yubikey'
                ))
            else:
                return

        if not is_valid_yubikey_format(field.data):
            raise ValidationError(_('Invalid Yubikey'))

        users = UserCollection(self.request.session)
        user = users.by_yubikey(field.data)

        if not hasattr(self, 'current_username'):
            raise NotImplementedError()

        if user and user.username != self.current_username:
            raise ValidationError(
                _('This Yubikey is already used by ${username}', mapping={
                    'username': user.username
                })
            )


class ChangeUsernameForm(Form):
    """ Defines the change username form. """

    if TYPE_CHECKING:
        model: User
        request: OrgRequest

    old_username = PanelField(
        label=_('Current E-Mail'),
        text='',
        kind='',
        hide_label=False,
    )

    new_username = EmailField(
        label=_('New E-Mail'),
        validators=[InputRequired(), Email()]
    )

    yubikey = StringField(
        label=_('Yubikey'),
        fieldset=_('Confirm action via your second factor'),
        description=_('Plug your YubiKey into a USB slot and press it.'),
        validators=[InputRequired()],
        render_kw={'autocomplete': 'off'}
    )

    totp = StringField(
        label=_('Code'),
        fieldset=_('Confirm action via your second factor'),
        description=_('Enter the six digit code from your authenticator app.'),
        validators=[InputRequired()],
        render_kw={'autocomplete': 'one-time-code'}
    )

    def process(
        self,
        formdata: _MultiDictLike | None = None,
        obj: object | None = None,
        data: Mapping[str, Any] | None = None,
        extra_filters: Mapping[str, Sequence[Any]] | None = None,
        **kwargs: Any
    ) -> None:

        # NOTE: We only pass on formdata, since
        super().process(
            formdata=formdata,
            obj=None,
            data=None,
            extra_filters=extra_filters,
        )

        if isinstance(obj, User):
            self.model = obj
            self.old_username.text = obj.username

    def populate_obj(self, obj: User) -> None:  # type: ignore[override]
        assert self.new_username.data is not None
        request = self.request
        obj.logout_all_sessions(request.app)
        obj.username = self.new_username.data
        # Run application-specific callback
        request.app.settings.user.change_username_callback(obj, request)

    def on_request(self) -> None:
        user = self.request.current_user
        assert user is not None
        if (user.second_factor or {}).get('type') == 'yubikey':
            self.delete_field('totp')
        else:
            self.delete_field('yubikey')

    def validate_new_username(self, field: EmailField) -> None:
        assert field.data is not None
        if self.model.username == field.data.lower():
            raise ValidationError(_(
                'The new username must be different from the old username '
                '(the username is case-insensitive)'
            ))
        if UserCollection(self.request.session).by_username(field.data):
            raise ValidationError(
                _('A user with this e-mail address exists already'))

    @cached_property
    def factors(self) -> dict[str, AnySecondFactor]:
        return Auth.from_request(self.request).factors

    def check_factor(self, factor: AnySecondFactor, value: str) -> bool:
        assert hasattr(factor, 'is_valid')
        user = self.request.current_user
        assert user is not None
        try:
            return factor.is_valid(self.request, user, value)
        except Exception:
            log.info(
                f'Second factor exception for user {user.username}:',
                exc_info=True
            )
            return False

    def validate_yubikey(self, field: StringField) -> None:
        assert field.data is not None
        factor = self.factors['yubikey']
        if not self.check_factor(factor, field.data):
            client = self.request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (Yubikey change-username)')
            raise ValidationError(_('Wrong yubikey.'))

    def validate_totp(self, field: StringField) -> None:
        assert field.data is not None
        factor = self.factors['totp']
        if not self.check_factor(factor, field.data):
            client = self.request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (TOTP change-username)')
            raise ValidationError(_('Invalid or expired TOTP provided.'))


class PartialNewUserForm(Form):
    """ Defines parts of the new user form not found in the manage user form.

    """

    username = EmailField(
        label=_('E-Mail'),
        description=_('The users e-mail address (a.k.a. username)'),
        validators=[InputRequired(), Email()]
    )

    send_activation_email = BooleanField(
        label=_('Send Activation E-Mail with Instructions'),
        default=True
    )

    @property
    def current_username(self) -> str:
        assert self.username.data is not None
        return self.username.data

    def validate_username(self, field: EmailField) -> None:
        assert field.data is not None
        if UserCollection(self.request.session).by_username(field.data):
            raise ValidationError(
                _('A user with this e-mail address exists already'))


if TYPE_CHECKING:
    class NewUserForm(PartialNewUserForm, ManageUserForm):
        pass
else:
    NewUserForm = merge_forms(PartialNewUserForm, ManageUserForm)


class ManageUserGroupForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ]
    )

    users = ChosenSelectMultipleField(
        label=_('Users'),
        choices=[],
    )

    ticket_permissions = ChosenSelectMultipleField(
        label=_('Ticket permissions'),
        description=_(
            'Restricts access and gives permission to these ticket categories'
        ),
        choices=[],
    )

    immediate_notification = ChosenSelectMultipleField(
        label=_(
            'Immediate e-mail notification to members upon ticket submission'
        ),
        description=_(
            'Also gives permission to these ticket categories, '
            'but does not restrict access to other groups.'
        ),
        choices=[],
    )

    shared_email = StringField(
        label=_('Shared e-mail address for ticket submission notifications'),
        description=_(
            'When specified, notifications for new tickets will be sent to '
            'this e-mail address, instead of to individual members. Requires '
            'that immediate e-mail notifications are turned on for at least '
            'one kind of ticket.'
        )
    )

    def on_request(self) -> None:
        self.users.choices = [
            (str(u.id), u.title)
            for u in UserCollection(self.request.session).query()
        ]
        ticket_choices: list[_Choice] = [
            (key, key)
            for key in handlers.registry.keys()
        ]
        ticket_choices.extend(
            (f'DIR-{group}', f'DIR: {group}')
            for group, in self.request.session.query(
                Directory.title.label('group')
            # some groups may get deleted, but as long as there are tickets
            # we need a corresponding permission
            ).union(
                self.request.session.query(
                    Ticket.group.label('group')
                )
                .filter(Ticket.handler_code == 'DIR')
                .filter(Ticket.group.isnot(None))
                .distinct()
            ).order_by('group').distinct()
        )
        ticket_choices.extend(
            (f'FRM-{group}', f'FRM: {group}')
            for group, in self.request.session.query(
                FormDefinition.title.label('group')
            # some groups may get deleted, but as long as there are tickets
            # we need a corresponding permission
            ).union(
                self.request.session.query(Ticket.group.label('group'))
                .filter(Ticket.handler_code == 'FRM')
                .filter(Ticket.group.isnot(None))
                .distinct()
            ).order_by('group').distinct()
        )
        ticket_choices.extend(
            (f'RSV-{group}', f'RSV: {group}')
            for group, in self.request.session.query(
                Resource.title.label('group')
            # some groups may get deleted, but as long as there are tickets
            # we need a corresponding permission
            ).union(
                self.request.session.query(
                    Ticket.group.label('group')
                )
                .filter(Ticket.handler_code == 'RSV')
                .filter(Ticket.group.isnot(None))
                .distinct()
            ).order_by('group').distinct()
        )
        ticket_choices.sort()
        self.ticket_permissions.choices = ticket_choices
        if isinstance(self.immediate_notification, ChosenSelectMultipleField):
            self.immediate_notification.choices = ticket_choices[:]

    @property
    def exclusive_permissions(self) -> set[tuple[str, str | None]]:
        return {
            (match.group(1), match.group(2))
            for permission in self.ticket_permissions.data or ()
            if (match := TICKET_PERMISSION_RE.match(permission))
        }

    @property
    def immediate_notifications(self) -> set[tuple[str, str | None]]:
        if not isinstance(self.immediate_notification.data, list):
            return set()

        return {
            (match.group(1), match.group(2))
            for permission in self.immediate_notification.data
            if (match := TICKET_PERMISSION_RE.match(permission))
        }

    def update_model(self, model: UserGroup) -> None:
        session = self.request.session

        # Logout the new and old users
        user_ids = {str(r.id) for r in model.users.with_entities(User.id)}
        user_ids |= set(self.users.data or ())
        users = UserCollection(session).query()
        users = users.filter(User.id.in_(user_ids))
        for user in users:
            if user != self.request.current_user:
                user.logout_all_sessions(self.request.app)

        # Update model
        model.name = self.name.data

        if self.users.data:
            users = UserCollection(session).query()
            users = users.filter(User.id.in_(self.users.data))
            model.users = users.all()
        else:
            model.users = []

        exclusive_permissions = self.exclusive_permissions
        immediate_notifications = self.immediate_notifications
        missing = exclusive_permissions | immediate_notifications

        # Update ticket permissions
        # FIXME: backref across module boundaries
        assert hasattr(model, 'ticket_permissions')
        permissions = []
        permission: TicketPermission
        for permission in model.ticket_permissions:
            key = (permission.handler_code, permission.group)
            exclusive = key in exclusive_permissions
            notification = key in immediate_notifications
            if not exclusive and not notification:
                # no permission object should exist
                session.delete(permission)
                continue

            # so we don't add this permission twice
            missing.discard(key)
            permission.exclusive = exclusive
            permission.immediate_notification = notification
            permissions.append(permission)

        for key in missing:
            handler_code, group = key
            permission = TicketPermission(
                handler_code=handler_code,
                group=group or None,
                user_group=model,
                exclusive=key in exclusive_permissions,
                immediate_notification=key in immediate_notifications,
            )
            session.add(permission)
            permissions.append(permission)

        model.ticket_permissions = permissions

        if getattr(self, 'shared_email', None):
            if shared_email := self.shared_email.data:
                if not model.meta:
                    model.meta = {}
                model.meta['shared_email'] = shared_email
            elif model.meta and 'shared_email' in model.meta:
                del model.meta['shared_email']

    def apply_model(self, model: UserGroup) -> None:
        self.name.data = model.name
        self.users.data = [str(u.id) for u in model.users]
        self.ticket_permissions.data = [
            f'{permission.handler_code}-{permission.group}'
            if permission.group else permission.handler_code
            for permission in model.ticket_permissions
            if permission.exclusive
        ]
        if isinstance(self.immediate_notification, ChosenSelectMultipleField):
            self.immediate_notification.data = [
                f'{permission.handler_code}-{permission.group}'
                if permission.group else permission.handler_code
                for permission in model.ticket_permissions
                if permission.immediate_notification
            ]

        if getattr(self, 'shared_email', None) and model.meta:
            self.shared_email.data = model.meta.get('shared_email')
