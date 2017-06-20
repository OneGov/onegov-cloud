from collections import defaultdict
from copy import copy
from onegov.core.crypto import random_password
from onegov.core.directives import query_form_class
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.form import merge_forms
from onegov.org import _, OrgApp
from onegov.org.forms import ManageUserForm, NewUserForm
from onegov.org.layout import DefaultMailLayout
from onegov.org.layout import UserLayout
from onegov.org.layout import UserManagementLayout
from onegov.org.new_elements import Link, LinkGroup
from onegov.ticket import TicketCollection, Ticket
from onegov.user import User, UserCollection
from onegov.user.errors import ExistingUserError
from wtforms.validators import Optional


@OrgApp.html(model=UserCollection, template='usermanagement.pt',
             permission=Secret)
def view_usermanagement(self, request):
    """ Allows the management of organisation users. """

    layout = UserManagementLayout(self, request)

    users = defaultdict(list)

    for user in self.query().order_by(User.username).all():
        users[user.role].append(user)

    return {
        'layout': layout,
        'title': _("User Management"),
        'users': users
    }


@OrgApp.html(model=User, template='user.pt', permission=Secret)
def view_user(self, request):
    """ Shows all objects owned by the given user. """

    layout = UserLayout(self, request)

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
def ticket_links(request, user):
    tickets = TicketCollection(request.app.session()).query()
    tickets = tickets.filter_by(user_id=user.id)
    tickets = tickets.order_by(Ticket.number)
    tickets = tickets.with_entities(
        Ticket.id, Ticket.number, Ticket.handler_code)

    return LinkGroup(
        title=_("Tickets"),
        links=[
            Link(
                ticket.number,
                request.class_link(Ticket, {
                    'handler_code': ticket.handler_code,
                    'id': ticket.id
                }),
            )
            for ticket in tickets
        ]
    )


def get_manage_user_form(self, request):
    userprofile_form = query_form_class(request, self, name='benutzerprofil')
    assert userprofile_form

    class OptionalUserprofile(userprofile_form):

        hooked = False

        def submitted(self, request):
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

    return merge_forms(ManageUserForm, OptionalUserprofile)


@OrgApp.form(model=User, template='form.pt', form=get_manage_user_form,
             permission=Secret, name='bearbeiten')
def handle_manage_user(self, request, form):

    # XXX the manage user form doesn't have access to the username
    # because it can't be edited, so we need to inject it here
    # for validation purposes (check for a unique yubikey)
    form.current_username = self.username

    if not request.app.settings.org.enable_yubikey:
        form.delete_field('yubikey')

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return request.redirect(request.class_link(UserCollection))

    elif not request.POST:
        form.process(obj=self)

    layout = UserManagementLayout(self, request)
    layout.breadcrumbs.append(Link(self.username, '#'))

    return {
        'layout': layout,
        'title': self.username,
        'form': form
    }


@OrgApp.form(model=UserCollection, template='newuser.pt', form=NewUserForm,
             name='neu', permission=Secret)
def handle_new_user(self, request, form):

    if not request.app.settings.org.enable_yubikey:
        form.delete_field('yubikey')

    layout = UserManagementLayout(self, request)
    layout.breadcrumbs.append(Link(_("New User"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        password = random_password()

        if form.data.get('yubikey'):
            second_factor = {
                'type': 'yubikey',
                'data': form.data['yubikey']
            }
        else:
            second_factor = None

        try:
            user = self.add(
                username=form.username.data,
                password=password,
                role=form.role.data,
                active=form.active.data,
                second_factor=second_factor
            )
        except ExistingUserError:
            form.username.errors.append(
                _("A user with this e-mail address already exists"))
        else:
            if form.send_activation_email.data:
                subject = request.translate(
                    _("An account was created for you")
                )

                content = render_template('mail_new_user.pt', request, {
                    'user': user,
                    'org': request.app.org,
                    'layout': DefaultMailLayout(user, request),
                    'title': subject
                })

                request.app.send_email(
                    subject=subject,
                    receivers=(user.username, ),
                    content=content,
                )

            request.info(_("The user was created successfully"))

            return {
                'layout': layout,
                'title': _("New User"),
                'username': form.username.data,
                'password': password,
                'sent_email': form.send_activation_email.data
            }

    return {
        'layout': layout,
        'title': _("New User"),
        'form': form,
        'password': None,
        'sent_email': False
    }
