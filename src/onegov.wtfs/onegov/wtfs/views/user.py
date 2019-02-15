from morepath import redirect
from onegov.user import User
from onegov.user import UserCollection
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import UnrestrictedUserForm
from onegov.wtfs.forms import UserForm
from onegov.wtfs.layouts import AddUserLayout
from onegov.wtfs.layouts import EditUserLayout
from onegov.wtfs.layouts import UserLayout
from onegov.wtfs.layouts import UsersLayout
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted
from onegov.wtfs.security import ViewModel


@WtfsApp.html(
    model=UserCollection,
    template='users.pt',
    permission=ViewModel
)
def view_users(self, request):
    """ View the list of users. """
    layout = UsersLayout(self, request)

    return {
        'layout': layout,
        'permission': ViewModel
    }


@WtfsApp.form(
    model=UserCollection,
    name='add-unrestricted',
    template='form.pt',
    permission=AddModelUnrestricted,
    form=UnrestrictedUserForm
)
def add_user_unrestricted(self, request, form):
    """ Create a new user. """
    layout = AddUserLayout(self, request)

    if form.submitted(request):
        user = User()
        form.update_model(user)
        request.session.add(user)
        request.message(_("User added."), 'success')
        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.form(
    model=UserCollection,
    name='add',
    template='form.pt',
    permission=AddModel,
    form=UserForm
)
def add_user(self, request, form):
    """ Create a new user. """

    if request.has_permission(self, AddModelUnrestricted):
        return redirect(request.link(self, name='add-unrestricted'))

    layout = AddUserLayout(self, request)

    if form.submitted(request):
        user = User()
        form.update_model(user)
        request.session.add(user)
        request.message(_("User added."), 'success')
        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.html(
    model=User,
    template='user.pt',
    permission=ViewModel
)
def view_user(self, request):
    """ View a single user. """
    layout = UserLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=User,
    name='edit-unrestricted',
    template='form.pt',
    permission=EditModelUnrestricted,
    form=UnrestrictedUserForm
)
def edit_user_unrestricted(self, request, form):
    """ Edit a user. """

    layout = EditUserLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("User modified."), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url,
    }


@WtfsApp.form(
    model=User,
    name='edit',
    template='form.pt',
    permission=EditModel,
    form=UserForm
)
def edit_user(self, request, form):
    """ Edit a user. """

    if request.has_permission(self, EditModelUnrestricted):
        return redirect(request.link(self, name='edit-unrestricted'))

    layout = EditUserLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("User modified."), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url,
    }


@WtfsApp.view(
    model=User,
    request_method='DELETE',
    permission=DeleteModel
)
def delete_user(self, request):
    """ Delete a user. """

    request.assert_valid_csrf_token()
    self.logout_all_sessions(request)
    UserCollection(request.session).delete(self.username)
    request.message(_("User deleted."), 'success')
