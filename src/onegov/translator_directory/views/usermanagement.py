from __future__ import annotations

from onegov.core.security import Secret
from onegov.org.views.usermanagement import get_manage_user_form
from onegov.town6.views.usermanagement import town_handle_manage_user
from onegov.town6.views.usermanagement import town_view_usermanagement
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.user import ManageUserFormCustom
from onegov.user import User
from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.html(
    model=UserCollection,
    template='usermanagement.pt',
    permission=Secret
)
def view_usermanagement_custom(
    self: UserCollection,
    request: TranslatorAppRequest
) -> RenderData:

    roles = {
        'admin': _('Administrator'),
        'editor': _('Editor'),
        'member': _('Member'),
        'translator': _('Translator'),
    }
    return town_view_usermanagement(self, request, roles=roles)


def get_manage_user_form_custom(
    self: User,
    request: TranslatorAppRequest
) -> type[ManageUserFormCustom]:
    return get_manage_user_form(self, request, base=ManageUserFormCustom)


@TranslatorDirectoryApp.form(
    model=User,
    template='form.pt',
    form=get_manage_user_form_custom,
    permission=Secret,
    name='edit'
)
def handle_manage_user_custom(
    self: User,
    request: TranslatorAppRequest,
    form: ManageUserFormCustom
) -> RenderData | Response:
    return town_handle_manage_user(self, request, form)
