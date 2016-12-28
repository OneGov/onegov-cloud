from collections import defaultdict
from onegov.core.crypto import random_password
from onegov.core.directives import query_form_class
from onegov.core.security import Secret
from onegov.form import merge_forms
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


def get_manage_user_form(self, request):
    userprofile_form = query_form_class(request, self, name='benutzerprofil')
    assert userprofile_form

    return merge_forms(ManageUserForm, userprofile_form)


@OrgApp.form(model=User, template='form.pt', form=get_manage_user_form,
             permission=Secret)
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
