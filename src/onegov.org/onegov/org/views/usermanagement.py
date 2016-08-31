import morepath

from collections import defaultdict
from onegov.core.crypto import random_password
from onegov.core.security import Secret
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import ManageUserForm, NewUserForm
from onegov.org.layout import UserManagementLayout
from onegov.user import User, UserCollection
from onegov.user.errors import ExistingUserError


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


@OrgApp.form(model=User, template='form.pt', form=ManageUserForm,
             permission=Secret)
def handle_manage_user(self, request, form):

    if not request.app.settings.org.enable_yubikey:
        form.delete_field('yubikey')

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.class_link(UserCollection))
    else:
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

        try:
            self.add(
                username=form.username.data,
                password=password,
                role=form.role.data,
                active=form.active.data
            )
        except ExistingUserError:
            form.username.errors.append(
                _("A user with this e-mail address already exists"))
        else:
            request.info(_("The user was created successfully"))

            return {
                'layout': layout,
                'title': _("New User"),
                'username': form.username.data,
                'password': password
            }

    return {
        'layout': layout,
        'title': _("New User"),
        'form': form
    }
