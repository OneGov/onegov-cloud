from __future__ import annotations

from onegov.core.security import Private
from onegov.org.views.export import view_export_collection, view_export
from onegov.town6 import TownApp
from onegov.org.models import Export, ExportCollection
from onegov.town6.layout import ExportCollectionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=ExportCollection,
    permission=Private,
    template='exports.pt'
)
def town_view_export_collection(
    self: ExportCollection,
    request: TownRequest
) -> RenderData:
    return view_export_collection(
        self, request, ExportCollectionLayout(self, request))


@TownApp.form(
    model=Export,
    permission=Private,
    template='export.pt',
    form=lambda model, request: model.form_class
)
def town_view_export(
    self: Export,
    request: TownRequest,
    form: Form
) -> RenderData | Response:
    return view_export(
        self, request, form, ExportCollectionLayout(self, request))
