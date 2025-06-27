from __future__ import annotations

from onegov.core.elements import Link

from onegov.parliament import _
from onegov.parliament.collections import CommissionCollection

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from webob import Response

    from onegov.parliament.forms.commission import CommissionForm
    from onegov.parliament.models import Commission
    from onegov.pas.layouts import (
        PASCommissionCollectionLayout,
        PASCommissionLayout
    )
    from onegov.town6.layout import (
        RISCommissionCollectionLayout,
        RISCommissionLayout
    )
    from onegov.town6.request import TownRequest


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
