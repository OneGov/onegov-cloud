from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.forms import LegislativePeriodForm
from onegov.pas.layouts import LegislativePeriodCollectionLayout
from onegov.pas.layouts import LegislativePeriodLayout
from onegov.pas.models import LegislativePeriod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=LegislativePeriodCollection,
    template='legislative_periods.pt',
    permission=Private
)
def view_legislative_periods(
    self: LegislativePeriodCollection,
    request: TownRequest
) -> RenderData:

    layout = LegislativePeriodCollectionLayout(self, request)

    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'legislative_periods': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=LegislativePeriodCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=LegislativePeriodForm
)
def add_legislative_period(
    self: LegislativePeriodCollection,
    request: TownRequest,
    form: LegislativePeriodForm
) -> RenderData | Response:

    if form.submitted(request):
        legislative_period = self.add(**form.get_useful_data())
        request.success(_('Added a new legislative period'))

        return request.redirect(request.link(legislative_period))

    layout = LegislativePeriodCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New legislative period'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=LegislativePeriod,
    template='legislative_period.pt',
    permission=Private
)
def view_legislative_period(
    self: LegislativePeriod,
    request: TownRequest
) -> RenderData:

    layout = LegislativePeriodLayout(self, request)

    return {
        'layout': layout,
        'legislative_period': self,
        'title': layout.title,
    }


@PasApp.form(
    model=LegislativePeriod,
    name='edit',
    template='form.pt',
    permission=Private,
    form=LegislativePeriodForm
)
def edit_legislative_period(
    self: LegislativePeriod,
    request: TownRequest,
    form: LegislativePeriodForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = LegislativePeriodLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=LegislativePeriod,
    request_method='DELETE',
    permission=Private
)
def delete_legislative_period(
    self: LegislativePeriod,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = LegislativePeriodCollection(request.session)
    collection.delete(self)
