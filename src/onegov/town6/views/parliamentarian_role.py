# from __future__ import annotations
#
# from typing import TYPE_CHECKING
#
# from onegov.core.security import Public, Private
# from onegov.parliament.forms import ParliamentarianRoleForm
# from onegov.parliament.models import RISParliamentarianRole
# from onegov.parliament.views import (
#     view_parliamentarian_role,
#     edit_parliamentarian_role,
#     delete_parliamentarian_role
# )
# from onegov.town6 import TownApp
# from onegov.town6.layout import RISParliamentarianRoleLayout
#
# if TYPE_CHECKING:
#     from webob.response import Response
#
#     from onegov.core.types import RenderData
#     from onegov.town6.request import TownRequest
#
#
# @TownApp.html(
#     model=RISParliamentarianRole,
#     template='parliamentarian_role.pt',
#     permission=Public
# )
# def ris_view_parliamentarian_role(
#     self: RISParliamentarianRole,
#     request: TownRequest
# ) -> RenderData | Response:
#
#     layout = RISParliamentarianRoleLayout(self, request)
#     return view_parliamentarian_role(self, request, layout)
#
#
# @TownApp.form(
#     model=RISParliamentarianRole,
#     name='edit',
#     template='form.pt',
#     permission=Private,
#     form=ParliamentarianRoleForm
# )
# def ris_edit_parliamentarian_role(
#     self: RISParliamentarianRole,
#     request: TownRequest,
#     form: ParliamentarianRoleForm
# ) -> RenderData | Response:
#
#     layout = RISParliamentarianRoleLayout(self, request)
#     return edit_parliamentarian_role(self, request, form, layout)
#
#
# @TownApp.view(
#     model=RISParliamentarianRole,
#     request_method='DELETE',
#     permission=Private
# )
# def ris_delete_parliamentarian_role(
#     self: RISParliamentarianRole,
#     request: TownRequest
# ) -> None:
#
#     return delete_parliamentarian_role(self, request)
