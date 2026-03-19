from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.forms.presidential_allowance import (
    PresidentialAllowanceForm,
)
from onegov.pas.layouts.default import DefaultLayout
from onegov.pas.models import PASParliamentarianRole
from onegov.pas.models.presidential_allowance import (
    PRESIDENT_QUARTERLY,
    VICE_PRESIDENT_QUARTERLY,
    PresidentialAllowance,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.pas.request import PasRequest
    from webob import Response


def get_current_role_holder(
    request: PasRequest, role: str
) -> PASParliamentarianRole | None:
    from datetime import date

    today = date.today()
    return (
        request.session.query(PASParliamentarianRole)
        .filter(
            PASParliamentarianRole.role == role,
            (
                PASParliamentarianRole.start.is_(None)
                | (PASParliamentarianRole.start <= today)
            ),
            (
                PASParliamentarianRole.end.is_(None)
                | (PASParliamentarianRole.end >= today)
            ),
        )
        .first()
    )


@PasApp.html(
    model=PresidentialAllowanceCollection,
    template='presidential_allowances.pt',
    permission=Private,
)
def view_presidential_allowances(
    self: PresidentialAllowanceCollection,
    request: PasRequest,
) -> RenderData:

    layout = DefaultLayout(self, request)

    president_role = get_current_role_holder(request, 'president')
    vice_president_role = get_current_role_holder(request, 'vice_president')

    return {
        'layout': layout,
        'title': _('Presidential allowances'),
        'allowances': self.query().all(),
        'add_link': request.link(self, name='new'),
        'president': (
            president_role.parliamentarian if president_role else None
        ),
        'vice_president': (
            vice_president_role.parliamentarian
            if vice_president_role
            else None
        ),
        'president_quarterly': PRESIDENT_QUARTERLY,
        'vice_president_quarterly': VICE_PRESIDENT_QUARTERLY,
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
        settlement_run = form.current_settlement_run

        president_role = get_current_role_holder(request, 'president')
        vice_president_role = get_current_role_holder(
            request, 'vice_president'
        )

        added = 0
        if president_role:
            self.add(
                year=year,
                role='president',
                amount=PRESIDENT_QUARTERLY,
                parliamentarian_id=(president_role.parliamentarian_id),
                settlement_run_id=(
                    settlement_run.id if settlement_run else None
                ),
            )
            added += 1

        if vice_president_role:
            self.add(
                year=year,
                role='vice_president',
                amount=VICE_PRESIDENT_QUARTERLY,
                parliamentarian_id=(vice_president_role.parliamentarian_id),
                settlement_run_id=(
                    settlement_run.id if settlement_run else None
                ),
            )
            added += 1

        if added:
            request.success(_('Quarterly allowance added'))
        else:
            request.warning(_('No president or vice president found'))

        return request.redirect(request.link(self))

    layout = DefaultLayout(self, request)

    president_role = get_current_role_holder(request, 'president')
    vice_president_role = get_current_role_holder(request, 'vice_president')

    callout = ''
    if president_role:
        p = president_role.parliamentarian
        callout += request.translate(
            _(
                'President: ${name} (CHF ${amount})',
                mapping={
                    'name': (f'{p.first_name} {p.last_name}'),
                    'amount': str(PRESIDENT_QUARTERLY),
                },
            )
        )
    if vice_president_role:
        vp = vice_president_role.parliamentarian
        if callout:
            callout += '<br>'
        callout += request.translate(
            _(
                'Vice president: ${name} (CHF ${amount})',
                mapping={
                    'name': (f'{vp.first_name} {vp.last_name}'),
                    'amount': str(VICE_PRESIDENT_QUARTERLY),
                },
            )
        )

    return {
        'layout': layout,
        'title': _('Add quarterly allowance'),
        'form': form,
        'callout': callout or None,
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
