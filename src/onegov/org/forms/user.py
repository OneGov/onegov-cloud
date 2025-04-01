from __future__ import annotations

import re
from functools import cached_property
from markupsafe import Markup
from onegov.core.utils import is_valid_yubikey_format
from onegov.directory.models.directory import Directory
from onegov.form import Form, merge_forms
from onegov.form import FormDefinition
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import TagsField
from onegov.form.filters import yubikey_identifier
from onegov.org import _
from onegov.org.utils import ticket_directory_groups
from onegov.ticket import handlers
from onegov.user import User, UserGroup
from onegov.ticket import TicketPermission
from onegov.user import UserCollection
from sqlalchemy import and_, or_
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from wtforms.fields.choices import _Choice


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
        choices=[],
    )

    directories = ChosenSelectMultipleField(
        label=_('Directories'),
        choices=[],
        description=_(
            'Directories for which this user group is responsible. '
            'If activated, ticket notifications for this group are '
            'only sent for these directories'
        ),
    )

    @cached_property
    def get_dirs(self) -> tuple[str, ...]:
        return tuple(ticket_directory_groups(self.request.session))

    def on_request(self) -> None:
        if not self.get_dirs:
            self.hide(self.directories)
        else:
            self.directories.choices = [(d, d) for d in self.get_dirs]

        self.users.choices = [
            (str(u.id), u.title)
            for u in UserCollection(self.request.session).query()
        ]
        ticket_choices: list[_Choice] = [
            (key, key)
            for key in handlers.registry.keys()
        ]
        ticket_choices.extend(
            (f'FRM-{form.title}', f'FRM: {form.title}')
            for form in self.request.session.query(FormDefinition)
        )
        ticket_choices.extend(
            (f'DIR-{dir.title}', f'DIR: {dir.title}')
            for dir in self.request.session.query(Directory)
        )
        self.ticket_permissions.choices = sorted(ticket_choices)

        # NOTE: We override this in agency with a boolean field
        if hasattr(self.immediate_notification, 'choices'):
            self.immediate_notification.choices = sorted(ticket_choices)

    def ensure_exclusive_consistency(self) -> bool:
        exclusive_permissions = self.exclusive_permissions
        if not exclusive_permissions:
            return True

        query = self.request.session.query(
            TicketPermission.handler_code,
            TicketPermission.group,
            UserGroup
        ).join(UserGroup)
        if isinstance(self.model, UserGroup):
            # we can't be inconsistent with ourselves
            query.filter(TicketPermission.user_group != self.model)

        query.filter(or_(*(
            and_(
                TicketPermission.handler_code == handler_code,
                TicketPermission.group.isnot_distinct_from(group)
            )
            for handler_code, group in exclusive_permissions
        )))

        query = query.filter(TicketPermission.exclusive.is_(False))
        inconsistencies = query.all()
        if inconsistencies:
            assert isinstance(self.ticket_permissions.errors, list)
            self.ticket_permissions.errors.append(_(
                'The following selected permissions are invalid '
                'because immediate notifications are turned on '
                'in the following groups without a matching '
                'permission for this ticket:<ul>${inconsistencies}</ul>',
                mapping={'inconsistencies': Markup('').join(
                    Markup(
                        '<li>{permission}: <a href="{url}" '
                        'target="_blank">{user_group}</a></li>'
                    ).format(
                        permission=f'{code}: {group}' if group else code,
                        url=self.request.link(user_group),
                        user_group=user_group.title,
                    )
                    for code, group, user_group in inconsistencies
                )},
                markup=True
            ))
            return False
        return True

    def ensure_immediate_notification_consistency(self) -> bool:
        immediate_notifications = self.immediate_notifications
        if not immediate_notifications:
            return True

        non_exclusive = immediate_notifications - self.exclusive_permissions
        if not non_exclusive:
            return True

        query = self.request.session.query(
            TicketPermission.handler_code,
            TicketPermission.group
        )
        if isinstance(self.model, UserGroup):
            # we can't be inconsistent with ourselves
            query.filter(TicketPermission.user_group_id != self.model.id)

        query.filter(or_(*(
            and_(
                TicketPermission.handler_code == handler_code,
                TicketPermission.group.isnot_distinct_from(group)
            )
            for handler_code, group in non_exclusive
        )))

        query = query.filter(TicketPermission.exclusive.is_(True))
        inconsistencies = query.distinct().all()
        if inconsistencies:
            assert isinstance(self.immediate_notification.errors, list)
            self.immediate_notification.errors.append(_(
                'The following selected ticket types require '
                'that ticket permissions are given as well: ${permissions}',
                mapping={'permissions': ', '.join(
                    f'{code}: {group}' if group else code
                    for code, group in inconsistencies
                )},
            ))
            return False
        return True

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
            model.users = users.all()  # type:ignore[assignment]
        else:
            model.users = []  # type:ignore[assignment]

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

    def apply_model(self, model: UserGroup) -> None:
        self.name.data = model.name
        self.users.data = [str(u.id) for u in model.users]
        # FIXME: backref across module boundaries
        assert hasattr(model, 'ticket_permissions')
        self.ticket_permissions.data = [
            f'{permission.handler_code}-{permission.group}'
            if permission.group else permission.handler_code
            for permission in model.ticket_permissions
            if permission.exclusive
        ]
        self.immediate_notification.data = [
            f'{permission.handler_code}-{permission.group}'
            if permission.group else permission.handler_code
            for permission in model.ticket_permissions
            if permission.immediate_notification
        ]
