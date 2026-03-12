from __future__ import annotations

from onegov.core.security import Secret
from onegov.org.views.user_groups import add_user_group
from onegov.org.views.user_groups import edit_user_group
from onegov.org.views.user_groups import get_usergroup_form_class
from onegov.org.views.user_groups import view_user_group
from onegov.org.views.user_groups import view_user_groups
from onegov.town6 import TownApp
from onegov.town6.layout import UserGroupCollectionLayout
from onegov.town6.layout import UserGroupLayout
from onegov.user import UserGroup
from onegov.user import UserGroupCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import ManageUserGroupForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=UserGroupCollection,
    template='user_groups.pt',
    permission=Secret
)
def town_view_user_groups(
    self: UserGroupCollection[UserGroup],
    request: TownRequest
) -> RenderData:
    layout = UserGroupCollectionLayout(self, request)
    return view_user_groups(self, request, layout)


@TownApp.form(
    model=UserGroupCollection,
    name='new',
    template='form.pt',
    permission=Secret,
    form=get_usergroup_form_class
)
def town_add_user_group(
    self: UserGroupCollection[UserGroup],
    request: TownRequest,
    form: ManageUserGroupForm
) -> RenderData | Response:
    layout = UserGroupCollectionLayout(self, request)
    return add_user_group(self, request, form, layout)


@TownApp.html(
    model=UserGroup,
    template='user_group.pt',
    permission=Secret
)
def town_view_user_group(
    self: UserGroup,
    request: TownRequest
) -> RenderData:
    layout = UserGroupLayout(self, request)
    return view_user_group(self, request, layout)


@TownApp.form(
    model=UserGroup,
    name='edit',
    template='form.pt',
    permission=Secret,
    form=get_usergroup_form_class
)
def town_edit_user_group(
    self: UserGroup,
    request: TownRequest,
    form: ManageUserGroupForm
) -> RenderData | Response:
    layout = UserGroupLayout(self, request)
    return edit_user_group(self, request, form, layout)
