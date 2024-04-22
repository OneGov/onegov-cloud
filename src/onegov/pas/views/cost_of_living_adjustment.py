from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import CostOfLivingAdjustmentCollection
from onegov.pas.forms import CostOfLivingAdjustmentForm
from onegov.pas.layouts import CostOfLivingAdjustmentCollectionLayout
from onegov.pas.layouts import CostOfLivingAdjustmentLayout
from onegov.pas.models import CostOfLivingAdjustment

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=CostOfLivingAdjustmentCollection,
    template='cost_of_living_adjustments.pt',
    permission=Private
)
def view_cost_of_living_adjustments(
    self: CostOfLivingAdjustmentCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = CostOfLivingAdjustmentCollectionLayout(self, request)

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
        'cost_of_living_adjustments': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=CostOfLivingAdjustmentCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=CostOfLivingAdjustmentForm
)
def add_cost_of_living_adjustment(
    self: CostOfLivingAdjustmentCollection,
    request: 'TownRequest',
    form: CostOfLivingAdjustmentForm
) -> 'RenderData | Response':

    if form.submitted(request):
        cost_of_living_adjustment = self.add(**form.get_useful_data())
        request.success(_("Added a new cost of living adjustment"))

        return request.redirect(request.link(cost_of_living_adjustment))

    layout = CostOfLivingAdjustmentCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New cost of living adjustment"),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=CostOfLivingAdjustment,
    template='cost_of_living_adjustment.pt',
    permission=Private
)
def view_cost_of_living_adjustment(
    self: CostOfLivingAdjustment,
    request: 'TownRequest'
) -> 'RenderData':

    layout = CostOfLivingAdjustmentLayout(self, request)

    return {
        'layout': layout,
        'cost_of_living_adjustment': self,
        'title': layout.title,
    }


@PasApp.form(
    model=CostOfLivingAdjustment,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CostOfLivingAdjustmentForm
)
def edit_cost_of_living_adjustment(
    self: CostOfLivingAdjustment,
    request: 'TownRequest',
    form: CostOfLivingAdjustmentForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = CostOfLivingAdjustmentLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=CostOfLivingAdjustment,
    request_method='DELETE',
    permission=Private
)
def delete_cost_of_living_adjustment(
    self: CostOfLivingAdjustment,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = CostOfLivingAdjustmentCollection(request.session)
    collection.delete(self)
