from __future__ import annotations

from collections import OrderedDict
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.org import OrgApp, _
from onegov.org.layout import ExportCollectionLayout
from onegov.org.models import Export, ExportCollection
from onegov.org.elements import Link


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.html(
    model=ExportCollection,
    permission=Private,
    template='exports.pt')
def view_export_collection(
    self: ExportCollection,
    request: OrgRequest,
    layout: ExportCollectionLayout | None = None
) -> RenderData:

    exports = list(self.exports_for_current_user(request))
    exports.sort(key=lambda e: normalize_for_url(request.translate(e.title)))

    return {
        'layout': layout or ExportCollectionLayout(self, request),
        'title': _('Exports'),
        'exports': exports
    }


@OrgApp.form(
    model=Export,
    permission=Private,
    template='export.pt',
    form=lambda model, request: model.form_class)
def view_export(
    self: Export,
    request: OrgRequest,
    form: Form,
    layout: ExportCollectionLayout | None = None
) -> RenderData | Response:

    layout = layout or ExportCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(self.title, request.link(self)))

    if form.submitted(request):
        f = layout.export_formatter(form.format)  # type:ignore[attr-defined]

        rows = tuple(
            OrderedDict((f(k), f(v)) for k, v in row)
            for row in self.run(form, request.session)
        )

        return form.as_export_response(  # type:ignore[attr-defined]
            rows, title=request.translate(self.title))

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'explanation': self.explanation
    }
