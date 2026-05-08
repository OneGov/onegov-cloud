from __future__ import annotations

from onegov.core.security import Secret
from onegov.org.views.usermanagement import get_manage_user_form
from onegov.org.views.usermanagement import view_usermanagement
from onegov.town6.views.usermanagement import town_handle_manage_user
from onegov.org.views.usermanagement import handle_new_user
from onegov.pas import _
from onegov.pas.app import PasApp
from onegov.pas.forms.user import ManageUserFormCustom
from onegov.pas.forms.user import NewUserFormCustom
from onegov.pas.layouts.user import UserManagementLayout
from onegov.user import User
from onegov.user import UserCollection


from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms.user import NewUserForm
    from onegov.pas.request import PasRequest
    from webob import Response


@PasApp.html(
    model=UserCollection, template='usermanagement.pt', permission=Secret
)
def view_usermanagement_custom(
    self: UserCollection, request: PasRequest
) -> RenderData:

    roles = {
        'admin': _('Administrator'),
        'parliamentarian': _('Parliamentarian'),
        'commission_president': _('Commission President'),
    }
    return view_usermanagement(
        self, request, UserManagementLayout(self, request), roles=roles
    )


def get_manage_user_form_custom(
    self: User, request: PasRequest
) -> type[ManageUserFormCustom]:
    return get_manage_user_form(self, request, base=ManageUserFormCustom)


@PasApp.form(
    model=User,
    template='form.pt',
    form=get_manage_user_form_custom,
    permission=Secret,
    name='edit',
)
def handle_manage_user_custom(
    self: User, request: PasRequest, form: ManageUserFormCustom
) -> RenderData | Response:
    return town_handle_manage_user(self, request, form)


@PasApp.form(
    model=UserCollection,
    template='newuser.pt',
    form=NewUserFormCustom,
    name='new',
    permission=Secret,
)
def handle_new_user_custom(
    self: UserCollection, request: PasRequest, form: NewUserFormCustom
) -> RenderData | Response:
    return handle_new_user(
        self,
        request,
        cast('NewUserForm', form),
        UserManagementLayout(self, request),
    )
