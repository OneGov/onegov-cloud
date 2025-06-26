from __future__ import annotations

from webob.exc import HTTPNotFound

from onegov.core.security import Private, Public
from onegov.parliament.collections.commission import RISCommissionCollection
from onegov.parliament.forms.commission import CommissionForm
from onegov.parliament.models import RISCommission
from onegov.parliament.views.commission import (
    view_commissions,
    add_commission,
    view_commission,
    edit_commission,
    delete_commission
)
from onegov.town6 import TownApp

from typing import TYPE_CHECKING

from onegov.town6.layout import (RISCommissionCollectionLayout,
                                 RISCommissionLayout)

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


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
