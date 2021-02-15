from onegov.core.security import Secret

from onegov.org.views.usermanagement import view_usermanagement, \
    handle_create_signup_link, view_user, handle_manage_user, \
    get_manage_user_form, handle_new_user
from onegov.town6 import _, TownApp
from onegov.org.forms import NewUserForm
from onegov.user import Auth, User, UserCollection
from onegov.user.forms import SignupLinkForm


@TownApp.html(model=UserCollection, template='usermanagement.pt',
             permission=Secret)
def town_view_usermanagement(self, request):
    return view_usermanagement(self, request)


@TownApp.form(
    model=UserCollection,
    template='signup_link.pt',
    permission=Secret,
    form=SignupLinkForm,
    name='signup-link')
def town_handle_create_signup_link(self, request, form):
    return handle_create_signup_link(self, request, form)


@TownApp.html(model=User, template='user.pt', permission=Secret)
def town_view_user(self, request):
    return view_user(self, request)


@TownApp.form(model=User, template='form.pt', form=get_manage_user_form,
             permission=Secret, name='edit')
def town_handle_manage_user(self, request, form):
    return handle_manage_user(self, request, form)


@TownApp.form(model=UserCollection, template='newuser.pt',
             form=NewUserForm, name='new', permission=Secret)
def town_handle_new_user(self, request, form):
    return handle_new_user(self, request, form)
