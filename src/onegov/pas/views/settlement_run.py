from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.forms import SettlementRunForm
from onegov.pas.layouts import SettlementRunCollectionLayout
from onegov.pas.layouts import SettlementRunLayout
from onegov.pas.models import SettlementRun

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=SettlementRunCollection,
    template='settlement_runs.pt',
    permission=Private
)
def view_settlement_runs(
    self: SettlementRunCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = SettlementRunCollectionLayout(self, request)

    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_("Active"), True),
            (_("Inactive"), False)
        )
    ]

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'settlement_runs': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=SettlementRunCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=SettlementRunForm
)
def add_settlement_run(
    self: SettlementRunCollection,
    request: 'TownRequest',
    form: SettlementRunForm
) -> 'RenderData | Response':

    if form.submitted(request):
        settlement_run = self.add(**form.get_useful_data())
        request.success(_("Added a new settlement run"))

        return request.redirect(request.link(settlement_run))

    layout = SettlementRunCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New settlement run"),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=SettlementRun,
    template='settlement_run.pt',
    permission=Private
)
def view_settlement_run(
    self: SettlementRun,
    request: 'TownRequest'
) -> 'RenderData':

    layout = SettlementRunLayout(self, request)

    return {
        'layout': layout,
        'settlement_run': self,
        'title': layout.title,
    }


@PasApp.form(
    model=SettlementRun,
    name='edit',
    template='form.pt',
    permission=Private,
    form=SettlementRunForm
)
def edit_settlement_run(
    self: SettlementRun,
    request: 'TownRequest',
    form: SettlementRunForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = SettlementRunLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=SettlementRun,
    request_method='DELETE',
    permission=Private
)
def delete_settlement_run(
    self: SettlementRun,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = SettlementRunCollection(request.session)
    collection.delete(self)
