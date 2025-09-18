from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private, Public
from onegov.org.forms.commission import CommissionForm
from onegov.org import _
from onegov.org.models import RISCommission, RISCommissionCollection
from onegov.parliament.collections import CommissionCollection
from onegov.town6 import TownApp
from onegov.town6.layout import RISCommissionCollectionLayout
from onegov.town6.layout import RISCommissionLayout
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.parliament.models import Commission
    from onegov.pas.layouts import PASCommissionCollectionLayout
    from onegov.pas.layouts import PASCommissionLayout
    from onegov.town6.request import TownRequest
    from webob import Response


def view_commissions(
    self: CommissionCollection,
    request: TownRequest,
    layout: RISCommissionCollectionLayout | PASCommissionCollectionLayout
) -> RenderData | Response:
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
        'commissions': self.query().all(),
        'title': layout.title,
    }


def add_commission(
    self: CommissionCollection,
    request: TownRequest,
    form: CommissionForm,
    layout: RISCommissionCollectionLayout | PASCommissionCollectionLayout
) -> RenderData | Response:

    if form.submitted(request):
        commission = self.add(**form.get_useful_data())
        request.success(_('Added a new commission'))

        return request.redirect(request.link(commission))

    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New commission'),
        'form': form,
        'form_width': 'large'
    }


def view_commission(
    self: Commission,
    request: TownRequest,
    layout: RISCommissionLayout | PASCommissionLayout
) -> RenderData | Response:

    return {
        'layout': layout,
        'commission': self,
        'title': layout.title,
    }


def edit_commission(
    self: Commission,
    request: TownRequest,
    form: CommissionForm,
    layout: RISCommissionLayout | PASCommissionLayout
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


def delete_commission(
    self: Commission,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = CommissionCollection(request.session)
    collection.delete(self)

    request.success(_('The commission has been deleted.'))


@TownApp.html(
    model=RISCommissionCollection,
    template='commissions.pt',
    permission=Public
)
def ris_view_commissions(
    self: RISCommissionCollection,
    request: TownRequest
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_commissions(
        self, request, RISCommissionCollectionLayout(self, request))


@TownApp.form(
    model=RISCommissionCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def ris_add_commission(
    self: RISCommissionCollection,
    request: TownRequest,
    form: CommissionForm
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return add_commission(
        self,
        request,
        form,
        RISCommissionCollectionLayout(self, request)
    )


@TownApp.html(
    model=RISCommission,
    template='commission.pt',
    permission=Public
)
def ris_view_commission(
    self: RISCommission,
    request: TownRequest
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_commission(self, request, RISCommissionLayout(self, request))


@TownApp.form(
    model=RISCommission,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def ris_edit_commission(
    self: RISCommission,
    request: TownRequest,
    form: CommissionForm
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return edit_commission(
        self, request, form, RISCommissionLayout(self, request))


@TownApp.view(
    model=RISCommission,
    request_method='DELETE',
    permission=Private
)
def ris_delete_commission(
    self: RISCommission,
    request: TownRequest
) -> None:
    return delete_commission(self, request)
