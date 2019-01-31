from morepath import redirect
from onegov.core.security import Secret
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import UserGroupForm
from onegov.wtfs.layouts import AddUserGroupLayout
from onegov.wtfs.layouts import EditUserGroupLayout
from onegov.wtfs.layouts import UserGroupLayout
from onegov.wtfs.layouts import UserGroupsLayout
from webob.exc import HTTPConflict


@WtfsApp.html(
    model=UserGroupCollection,
    template='user_groups.pt',
    permission=Secret
)
def view_user_groups(self, request):
    """ View the list of user groups.

    This view is only visible by an admin.

    """
    layout = UserGroupsLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=UserGroupCollection,
    name='add',
    template='form.pt',
    permission=Secret,
    form=UserGroupForm
)
def add_user_group(self, request, form):
    """ Create a new user group.

    This view is only visible by an admin.

    """
    layout = AddUserGroupLayout(self, request)

    if form.submitted(request):
        user_group = UserGroup()
        form.update_model(user_group)
        request.session.add(user_group)
        request.message(_("User group added."), 'success')
        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.html(
    model=UserGroup,
    template='user_group.pt',
    permission=Secret
)
def view_user_group(self, request):
    """ View the a single user group.

    This view is only visible by an admin.

    """
    layout = UserGroupLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=UserGroup,
    name='edit',
    template='form.pt',
    permission=Secret,
    form=UserGroupForm
)
def edit_user_group(self, request, form):
    """ Edit a user group.

    This view is only visible by an admin.

    """

    layout = EditUserGroupLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("User group modified."), 'success')
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
    model=UserGroup,
    request_method='DELETE',
    permission=Secret
)
def delete_user_group(self, request):
    """ Delete a user group.

    This view is only visible by an admin.

    """

    request.assert_valid_csrf_token()
    if self.municipality:
        raise HTTPConflict()
    UserGroupCollection(request.session).delete(self)
    request.message(_("User group deleted."), 'success')
