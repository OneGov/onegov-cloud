from __future__ import annotations

from onegov.core.security import Secret

from onegov.org.forms import ChangeUsernameForm, NewUserForm
from onegov.org.views.usermanagement import (
    view_usermanagement, handle_create_signup_link, view_user,
    handle_manage_user, handle_change_username, get_manage_user_form,
    handle_new_user)
from onegov.town6 import TownApp
from onegov.town6.layout import UserManagementLayout, UserLayout
from onegov.user import User, UserCollection
from onegov.user.forms import SignupLinkForm


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from onegov.core.types import RenderData
    from onegov.org.forms import ManageUserForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=UserCollection,
    template='usermanagement.pt',
    permission=Secret
)
def town_view_usermanagement(
    self: UserCollection,
    request: TownRequest,
    roles: Mapping[str, str] | None = None
) -> RenderData:
    return view_usermanagement(
        self, request, UserManagementLayout(self, request), roles=roles)


@TownApp.form(
    model=UserCollection,
    template='signup_link.pt',
    permission=Secret,
    form=SignupLinkForm,
    name='signup-link'
)
def town_handle_create_signup_link(
    self: UserCollection,
    request: TownRequest,
    form: SignupLinkForm
) -> RenderData | Response:
    return handle_create_signup_link(
        self, request, form, UserManagementLayout(self, request))


@TownApp.html(model=User, template='user.pt', permission=Secret)
def town_view_user(self: User, request: TownRequest,
                   layout: UserLayout | None = None) -> RenderData:
    layout = layout or UserLayout(self, request)
    return view_user(self, request, layout)


@TownApp.form(
    model=User,
    template='form.pt',
    form=get_manage_user_form,
    permission=Secret,
    name='edit'
)
def town_handle_manage_user(
    self: User,
    request: TownRequest,
    form: ManageUserForm
) -> RenderData | Response:
    layout = UserManagementLayout(self, request)
    layout.edit_mode = True
    return handle_manage_user(
        self, request, form, layout)


@TownApp.form(
    model=User,
    template='form.pt',
    form=ChangeUsernameForm,
    pass_model=True,
    permission=Secret,
    name='change-username'
)
def town_handle_change_username(
    self: User,
    request: TownRequest,
    form: ChangeUsernameForm
) -> RenderData | Response:
    return handle_change_username(
        self, request, form, UserManagementLayout(self, request))


@TownApp.form(
    model=UserCollection,
    template='newuser.pt',
    form=NewUserForm,
    name='new',
    permission=Secret
)
def town_handle_new_user(
    self: UserCollection,
    request: TownRequest,
    form: NewUserForm
) -> RenderData:
    layout = UserManagementLayout(self, request)
    layout.edit_mode = True
    return handle_new_user(
        self, request, form, layout)
