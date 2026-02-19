from __future__ import annotations

from collections import defaultdict
from copy import copy
from onegov.core.crypto import random_password
from onegov.core.directives import query_form_class
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.form import merge_forms, Form
from onegov.form.fields import PanelField
from onegov.org import _, OrgApp
from onegov.org.forms import ChangeUsernameForm, ManageUserForm, NewUserForm
from onegov.org.layout import DefaultMailLayout
from onegov.org.layout import UserLayout
from onegov.org.layout import UserManagementLayout
from onegov.org.utils import can_change_username
from onegov.core.elements import Link, LinkGroup
from onegov.ticket import TicketCollection, Ticket
from onegov.user import Auth, User, UserCollection
from onegov.user.errors import ExistingUserError
from onegov.user.forms import SignupLinkForm
from webob.exc import HTTPForbidden
from wtforms.validators import Optional


from typing import overload, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from typing import TypeVar
    from webob import Response

    FormT = TypeVar('FormT', bound=Form)


@OrgApp.html(model=UserCollection, template='usermanagement.pt',
             permission=Secret)
def view_usermanagement(
    self: UserCollection,
    request: OrgRequest,
    layout: UserManagementLayout | None = None,
    roles: Mapping[str, str] | None = None
) -> RenderData:
    """ Allows the management of organisation users. """

    layout = layout or UserManagementLayout(self, request)

    users = defaultdict(list)
    query = self.query().order_by(User.username)

    for user in query:
        users[user.role].append(user)

    roles = roles or {
        'admin': _('Administrator'),
        'editor': _('Editor'),
        'supporter': _('Supporter'),
        'member': _('Member'),
    }

    # hide roles that are not configured for the current app
    roles_setting = request.app.settings.roles
    roles = {
        role: label
        for role, label in roles.items()
        if hasattr(roles_setting, role)
    }

    filters = {}

    filters['role'] = [
        Link(
            text=request.translate(title),
            active=value in self.filters.get('role', ()),
            url=request.link(self.for_filter(role=value))
        ) for value, title in roles.items()
    ]

    filters['active'] = [
        Link(
            text=request.translate(title),
            active=value in self.filters.get('active', ()),
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    filters['tag'] = [
        Link(
            text=tag,
            active=tag in self.filters.get('tag', ()),
            url=request.link(self.for_filter(tag=tag))
        ) for tag in self.tags
    ]

    filters['source'] = [
        Link(
            text={
                'ldap_kerberos': 'LDAP Kerberos',
                'ldap': 'LDAP',
                'msal': 'AzureAD',
                '': '-'
            }.get(value, value),
            active=value in self.filters.get('source', ()),
            url=request.link(self.for_filter(source=value))
        ) for value in (*self.sources, '')
    ]

    return {
        'layout': layout,
        'title': _('User Management'),
        'roles': roles.keys(),
        'users': users,
        'filters': filters
    }


@OrgApp.form(
    model=UserCollection,
    template='signup_link.pt',
    permission=Secret,
    form=SignupLinkForm,
    name='signup-link'
)
def handle_create_signup_link(
    self: UserCollection,
    request: OrgRequest,
    form: SignupLinkForm,
    layout: UserManagementLayout | None = None
) -> RenderData:

    link = None

    if form.submitted(request):
        auth = Auth(request.app)
        auth.signup_token = form.signup_token(auth)

        link = request.link(auth, 'register')

    layout = layout or UserManagementLayout(self, request)
    layout.breadcrumbs.append(Link(_('New Signup Link'), '#'))
    layout.editbar_links = None  # type:ignore[assignment]

    return {
        'layout': layout,
        'title': _('New Signup Link'),
        'link': link,
        'form': form
    }


@OrgApp.html(model=User, template='user.pt', permission=Secret)
def view_user(
    self: User,
    request: OrgRequest,
    layout: UserLayout | None = None
) -> RenderData:
    """ Shows all objects owned by the given user. """

    layout = layout or UserLayout(self, request)

    linkgroups = [
        fn(request, self) for fn in request.app.config.linkgroup_registry
    ]
    linkgroups.sort(key=lambda group: request.translate(group.title))

    return {
        'layout': layout,
        'title': self.title,
        'linkgroups': linkgroups
    }


@OrgApp.userlinks()
def ticket_links(request: OrgRequest, user: User) -> LinkGroup:
    tickets = TicketCollection(request.session).query()
    tickets = tickets.filter_by(user_id=user.id)
    tickets = tickets.order_by(Ticket.number)

    return LinkGroup(
        title=_('Tickets'),
        links=[
            Link(
                number,
                request.class_link(Ticket, {
                    'handler_code': handler_code,
                    'id': ticket_id
                }),
            )
            for ticket_id, number, handler_code in tickets.with_entities(
                Ticket.id,
                Ticket.number,
                Ticket.handler_code
            ).tuples()
        ]
    )


@overload
def get_manage_user_form(
    self: User,
    request: OrgRequest
) -> type[ManageUserForm]: ...


@overload
def get_manage_user_form(
    self: User,
    request: OrgRequest,
    base: type[FormT]
) -> type[FormT]: ...


def get_manage_user_form(
    self: User,
    request: OrgRequest,
    base: type[Form] = ManageUserForm
) -> type[Form]:

    userprofile_form = query_form_class(request, self, name='userprofile')
    assert userprofile_form
    if can_change_username(self, request):
        class ChangeUsernameCallout(Form):
            username_callout = PanelField(
                text=_(
                    'The username can be changed <a href="${url}">here</a>.',
                    mapping={'url': request.link(self, 'change-username')},
                    markup=True
                ),
                kind='callout'
            )

        base = merge_forms(ChangeUsernameCallout, base)

    class OptionalUserprofile(userprofile_form):  # type:ignore

        hooked = False

        def submitted(self, request: OrgRequest) -> bool:
            # fields only present on the userprofile_form are made optional
            # to make sure that we can always change the active/inactive state
            # of the user and the role the user has
            if not self.hooked:
                for name, field in self._fields.items():
                    if not hasattr(userprofile_form, name):
                        continue

                    if not field.validators:
                        continue

                    # be careful not to change the class itself
                    field.validators = copy(field.validators)
                    field.validators.insert(0, Optional())

                self.hooked = True

            return super().submitted(request)

    return merge_forms(base, OptionalUserprofile)


@OrgApp.form(model=User, template='form.pt', form=get_manage_user_form,
             permission=Secret, name='edit')
def handle_manage_user(
    self: User,
    request: OrgRequest,
    form: ManageUserForm,
    layout: UserManagementLayout | None = None
) -> RenderData | Response:

    if self.source:
        raise HTTPForbidden()

    # XXX the manage user form doesn't have access to the username
    # because it can't be edited, so we need to inject it here
    # for validation purposes (check for a unique yubikey)
    # FIXME: We should probably add this to form.meta instead
    form.current_username = self.username  # type:ignore[attr-defined]

    if not request.app.enable_yubikey:
        form.delete_field('yubikey')

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))

        return request.redirect(request.class_link(
            UserCollection,
            variables={'active': '1'}
        ))

    elif not request.POST:
        form.process(obj=self)

    layout = layout or UserManagementLayout(self, request)
    layout.breadcrumbs.append(Link(self.username, '#'))

    return {
        'layout': layout,
        'title': self.username,
        'form': form
    }


@OrgApp.form(
    model=User,
    template='form.pt',
    form=ChangeUsernameForm,
    pass_model=True,
    permission=Secret,
    name='change-username'
)
def handle_change_username(
    self: User,
    request: OrgRequest,
    form: ChangeUsernameForm,
    layout: UserManagementLayout | None = None
) -> RenderData | Response:

    if not can_change_username(self, request, form.factors):
        raise HTTPForbidden()

    if form.submitted(request):
        assert form.new_username.data is not None
        old_username = self.username
        new_username = form.new_username.data

        self.logout_all_sessions(request.app)
        self.username = new_username

        # Run application-specific callback
        request.app.settings.user.change_username_callback(self, request)
        request.success(_(
            'Succesfully changed ${old_username} to ${new_username}',
            mapping={
                'old_username': old_username,
                'new_username': new_username
            }
        ))

        return request.redirect(request.class_link(
            UserCollection,
            variables={'active': '1'}
        ))

    layout = layout or UserManagementLayout(self, request)
    layout.breadcrumbs.extend((
        Link(self.username, request.link(self)),
        Link(_('Change username'), '#')
    ))

    return {
        'layout': layout,
        'title': _('Change username'),
        'form': form
    }


@OrgApp.form(model=UserCollection, template='newuser.pt',
             form=NewUserForm, name='new', permission=Secret)
def handle_new_user(
    self: UserCollection,
    request: OrgRequest,
    form: NewUserForm,
    layout: UserManagementLayout | None = None
) -> RenderData:

    if not request.app.enable_yubikey:
        form.delete_field('yubikey')

    layout = layout or UserManagementLayout(self, request)
    layout.breadcrumbs.append(Link(_('New User'), '#'))
    layout.editbar_links = None  # type:ignore[assignment]

    if form.submitted(request):
        assert form.username.data is not None
        password = random_password()

        if form.data.get('yubikey'):
            second_factor = {
                'type': 'yubikey',
                'data': form.data['yubikey'][:12]
            }
        else:
            second_factor = None

        try:
            user = self.add(
                username=form.username.data,
                password=password,
                role=form.role.data,
                active=form.active,
                second_factor=second_factor,
            )
        except ExistingUserError:
            assert isinstance(form.username.errors, list)
            form.username.errors.append(
                _('A user with this e-mail address already exists'))
        else:
            if form.send_activation_email.data:
                subject = request.translate(
                    _('An account was created for you')
                )

                content = render_template('mail_new_user.pt', request, {
                    'user': user,
                    'org': request.app.org,
                    'layout': DefaultMailLayout(user, request),
                    'title': subject
                })

                request.app.send_transactional_email(
                    subject=subject,
                    receivers=(user.username, ),
                    content=content,
                )

            request.info(_('The user was created successfully'))

            return {
                'layout': layout,
                'title': _('New User'),
                'username': form.username.data,
                'password': password,
                'sent_email': form.send_activation_email.data
            }

    return {
        'layout': layout,
        'title': _('New User'),
        'form': form,
        'password': None,  # nosec: B105
        'sent_email': False
    }
