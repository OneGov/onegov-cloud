from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.forms.presidential_allowance import (
    QUARTERLY_AMOUNTS,
    PresidentialAllowanceForm,
)
from onegov.pas.layouts.presidential_allowance import (
    PresidentialAllowanceCollectionLayout,
    PresidentialAllowanceFormLayout,
)
from onegov.pas.models.presidential_allowance import (
    PRESIDENT_QUARTERLY,
    PRESIDENT_YEARLY_ALLOWANCE,
    VICE_PRESIDENT_QUARTERLY,
    VICE_PRESIDENT_YEARLY_ALLOWANCE,
    PresidentialAllowance,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.pas.request import PasRequest
    from webob import Response


@PasApp.html(
    model=PresidentialAllowanceCollection,
    template='presidential_allowances.pt',
    permission=Private,
)
def view_presidential_allowances(
    self: PresidentialAllowanceCollection,
    request: PasRequest,
) -> RenderData:

    layout = PresidentialAllowanceCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': layout.title,
        'allowances': self.query().all(),
        'add_link': request.link(self, name='new'),
        'president_yearly': PRESIDENT_YEARLY_ALLOWANCE,
        'president_quarterly': PRESIDENT_QUARTERLY,
        'vice_president_yearly': (VICE_PRESIDENT_YEARLY_ALLOWANCE),
        'vice_president_quarterly': (VICE_PRESIDENT_QUARTERLY),
        'collection_link': request.link(self),
    }


@PasApp.form(
    model=PresidentialAllowanceCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PresidentialAllowanceForm,
)
def add_presidential_allowance(
    self: PresidentialAllowanceCollection,
    request: PasRequest,
    form: PresidentialAllowanceForm,
) -> RenderData | Response:

    if form.submitted(request):
        year = form.year.data
        quarter = form.quarter.data
        settlement_run = form.current_settlement_run
        run_id = settlement_run.id if settlement_run else None
        parl_id, role = form.parsed_recipient
        amount = QUARTERLY_AMOUNTS[role]

        self.add(
            year=year,
            quarter=quarter,
            role=role,
            amount=amount,
            parliamentarian_id=parl_id,
            settlement_run_id=run_id,
        )

        request.success(_('Quarterly allowance added'))
        return request.redirect(request.link(self))

    layout = PresidentialAllowanceFormLayout(self, request)

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'small',
    }


@PasApp.view(
    model=PresidentialAllowance,
    request_method='DELETE',
    permission=Private,
)
def delete_presidential_allowance(
    self: PresidentialAllowance, request: PasRequest
) -> None:

    request.assert_valid_csrf_token()
    request.session.delete(self)
