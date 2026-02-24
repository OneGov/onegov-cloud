from __future__ import annotations

from onegov.core.security import Private
from onegov.org.views.editor import get_form_class
from onegov.org.views.editor import handle_page_form, view_topics_sort
from onegov.town6 import TownApp
from onegov.org.models import Editor
from onegov.town6.layout import EditorLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=Editor,
    template='form.pt',
    permission=Private,
    form=get_form_class
)
def town_handle_page_form(
    self: Editor,
    request: TownRequest,
    form: Form
) -> RenderData | Response:
    return handle_page_form(
        self, request, form, EditorLayout(self, request, site_title=None)
    )


@TownApp.html(
    model=Editor,
    template='sort.pt',
    name='sort',
    permission=Private
)
def town_view_topics_sort(
    self: Editor,
    request: TownRequest
) -> RenderData:
    return view_topics_sort(self, request, EditorLayout(self, request, 'sort'))
