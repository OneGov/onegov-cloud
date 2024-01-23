from functools import cached_property
from onegov.core.utils import is_valid_yubikey_format
from onegov.form import Form, merge_forms
from onegov.form import FormDefinition
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import TagsField
from onegov.form.filters import yubikey_identifier
from onegov.org import _
from onegov.org.utils import ticket_directory_groups
from onegov.ticket import handlers
from onegov.user import User
from onegov.ticket import TicketPermission
from onegov.user import UserCollection
from re import match
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


AVAILABLE_ROLES = [
    ('admin', _("Admin")),
    ('editor', _("Editor")),
    ('member', _("Member"))
]


class ManageUserForm(Form):
    """ Defines the edit user form. """

    state = RadioField(
        label=_("State"),
        fieldset=_("General"),
        default='active',
        choices=(
            ('active', _("Active")),
            ('inactive', _("Inactive"))
        ),
    )

    role = RadioField(
        label=_("Role"),
        fieldset=_("General"),
        choices=AVAILABLE_ROLES,
        default='member',
    )

    tags = TagsField(
        label=_("Tags"),
        fieldset=_("General"),
    )

    yubikey = StringField(
        label=_("Yubikey"),
        fieldset=_("General"),
        description=_("Plug your YubiKey into a USB slot and press it."),
        filters=(yubikey_identifier, ),
        render_kw={'autocomplete': 'off'}
    )

    @property
    def active(self):
        return self.state.data == 'active'

    @active.setter
    def active(self, value):
        self.state.data = value and 'active' or 'inactive'

    def on_request(self):
        self.request.include('tags-input')

    def populate_obj(self, model):
        if (
            model.role != self.role.data
            or model.active != self.active
        ):
            model.logout_all_sessions(self.request.app)

        super().populate_obj(model)
        model.active = self.active

    def process_obj(self, model):
        super().process_obj(model)
        self.active = model.active

    def validate_yubikey(self, field):
        if not self.active:
            return

        if not field.data:
            if not self.request.app.enable_yubikey:
                return

            if self.role.data in ('admin', 'editor'):
                raise ValidationError(_(
                    "Administrators and editors must use a Yubikey"
                ))
            else:
                return

        if not is_valid_yubikey_format(field.data):
            raise ValidationError(_("Invalid Yubikey"))

        users = UserCollection(self.request.session)
        user = users.by_yubikey(field.data)

        if not hasattr(self, 'current_username'):
            raise NotImplementedError()

        if user and user.username != self.current_username:
            raise ValidationError(
                _("This Yubikey is already used by ${username}", mapping={
                    'username': user.username
                })
            )


class PartialNewUserForm(Form):
    """ Defines parts of the new user form not found in the manage user form.

    """

    username = EmailField(
        label=_("E-Mail"),
        description=_("The users e-mail address (a.k.a. username)"),
        validators=[InputRequired(), Email()]
    )

    send_activation_email = BooleanField(
        label=_("Send Activation E-Mail with Instructions"),
        default=True
    )

    @property
    def current_username(self):
        return self.username.data

    def validate_username(self, field):
        users = UserCollection(self.request.session)

        if users.by_username(field.data):
            raise ValidationError(
                _("A user with this e-mail address exists already"))


NewUserForm = merge_forms(PartialNewUserForm, ManageUserForm)


class ManageUserGroupForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ]
    )

    users = ChosenSelectMultipleField(
        label=_('Users'),
        choices=[],
        description=_(
            'Users can only be in one group. '
            'If they already belong to another group '
            'and get added here, they will automatically '
            'get removed from the other group.'
        )
    )

    ticket_permissions = ChosenSelectMultipleField(
        label=_('Ticket permissions'),
        description=_(
            'Restricts access and gives permission to these ticket categories'
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

    def on_request(self):
        if not self.get_dirs:
            self.hide(self.directories)
        else:
            self.directories.choices = tuple((d, d) for d in self.get_dirs)

        self.users.choices = [
            (str(u.id), u.title)
            for u in UserCollection(self.request.session).query()
        ]
        ticket_choices = [(f'{key}-', key) for key in handlers.registry.keys()]
        ticket_choices.extend([
            (f'FRM-{form.title}', f'FRM: {form.title}')
            for form in self.request.session.query(FormDefinition)
        ])
        self.ticket_permissions.choices = sorted(ticket_choices)

    def update_model(self, model):
        session = self.request.session

        # Logout the new and old users
        user_ids = {str(r.id) for r in model.users.with_entities(User.id)}
        user_ids |= set(self.users.data)
        users = UserCollection(session).query()
        users = users.filter(User.id.in_(user_ids)).all()
        for user in users:
            if user != self.request.current_user:
                user.logout_all_sessions(self.request.app)

        # Update model
        users = UserCollection(session).query()
        users = users.filter(User.id.in_(self.users.data)).all()
        model.name = self.name.data
        model.users = users

        # Update ticket permissions
        for permission in model.ticket_permissions:
            session.delete(permission)
        for permission in self.ticket_permissions.data:
            match_ = match(r'(.[^-]*)-(.*)', permission)
            if match_:
                handler_code, group = match_.groups()
                session.add(
                    TicketPermission(
                        handler_code=handler_code,
                        group=group or None,
                        user_group=model
                    )
                )
        # initialize meta field with empty dict
        if not model.meta:
            model.meta = {}
        model.meta['directories'] = self.directories.data

    def apply_model(self, model):
        self.name.data = model.name
        self.users.data = [str(u.id) for u in model.users]
        self.ticket_permissions.data = [
            f'{permission.handler_code}-{permission.group or ""}'
            for permission in model.ticket_permissions
        ]

        if model.meta:
            self.directories.data = model.meta.get('directories', '')
