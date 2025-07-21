from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import RateSetCollection
from onegov.pas.forms import RateSetForm
from onegov.pas.layouts import RateSetCollectionLayout
from onegov.pas.layouts import RateSetLayout
from onegov.pas.models import RateSet


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=RateSetCollection,
    template='rate_sets.pt',
    permission=Private
)
def view_rate_sets(
    self: RateSetCollection,
    request: TownRequest
) -> RenderData:

    layout = RateSetCollectionLayout(self, request)

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
        'rate_sets': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=RateSetCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=RateSetForm
)
def add_rate_set(
    self: RateSetCollection,
    request: TownRequest,
    form: RateSetForm
) -> RenderData | Response:

    if form.submitted(request):
        rate_set = self.add(**form.get_useful_data())
        request.success(_('Added a new rate set'))

        return request.redirect(request.link(rate_set))

    layout = RateSetCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New rate set'),
        'form': form,
        'form_width': 'full'
    }


@PasApp.html(
    model=RateSet,
    template='rate_set.pt',
    permission=Private
)
def view_rate_set(
    self: RateSet,
    request: TownRequest
) -> RenderData:

    layout = RateSetLayout(self, request)

    return {
        'layout': layout,
        'rate_set': self,
        'title': layout.title,
    }


@PasApp.form(
    model=RateSet,
    name='edit',
    template='form.pt',
    permission=Private,
    form=RateSetForm
)
def edit_rate_set(
    self: RateSet,
    request: TownRequest,
    form: RateSetForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = RateSetLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=RateSet,
    name='copy-rate-set',
    permission=Private,
    form=RateSetForm,
    template='form.pt'
)
def copy_specific_rate_set(
    self: RateSet,
    request: TownRequest,
    form: RateSetForm
) -> RenderData | Response:
    """ Create a new rate set based on a specific existing one."""

    if form.submitted(request):
        collection = RateSetCollection(request.session)
        rate_set = collection.add(**form.get_useful_data())
        request.success(_('The rate set was copied.'))
        return request.redirect(request.link(rate_set))

    form.process(obj=self)

    layout = RateSetLayout(self, request)
    layout.breadcrumbs.append(Link(_('Copy'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': _('Copy Rate Set'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=RateSet,
    request_method='DELETE',
    permission=Private
)
def delete_rate_set(
    self: RateSet,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = RateSetCollection(request.session)
    collection.delete(self)
