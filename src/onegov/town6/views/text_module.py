from __future__ import annotations

from onegov.chat import TextModule
from onegov.chat import TextModuleCollection
from onegov.core.security import Private
from onegov.org.forms import TextModuleForm
from onegov.org.views.text_module import add_text_module
from onegov.org.views.text_module import edit_text_module
from onegov.org.views.text_module import view_text_module
from onegov.org.views.text_module import view_text_modules
from onegov.town6 import TownApp
from onegov.town6.layout import TextModulesLayout
from onegov.town6.layout import TextModuleLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=TextModuleCollection,
    template='text_modules.pt',
    permission=Private
)
def town_view_text_moduless(
    self: TextModuleCollection,
    request: TownRequest
) -> RenderData:
    layout = TextModulesLayout(self, request)
    return view_text_modules(self, request, layout)


@TownApp.form(
    model=TextModuleCollection,
    name='add',
    template='form.pt',
    permission=Private,
    form=TextModuleForm
)
def town_add_text_module(
    self: TextModuleCollection,
    request: TownRequest,
    form: TextModuleForm
) -> RenderData | Response:
    layout = TextModulesLayout(self, request)
    return add_text_module(self, request, form, layout)


@TownApp.html(
    model=TextModule,
    template='text_module.pt',
    permission=Private
)
def town_view_text_module(
    self: TextModule,
    request: TownRequest
) -> RenderData:
    layout = TextModuleLayout(self, request)
    return view_text_module(self, request, layout)


@TownApp.form(
    model=TextModule,
    name='edit',
    template='form.pt',
    permission=Private,
    form=TextModuleForm
)
def town_edit_text_module(
    self: TextModule,
    request: TownRequest,
    form: TextModuleForm
) -> RenderData | Response:
    layout = TextModuleLayout(self, request)
    return edit_text_module(self, request, form, layout)
