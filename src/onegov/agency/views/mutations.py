from __future__ import annotations

from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.forms import ApplyMutationForm
from onegov.agency.layout import AgencyLayout
from onegov.agency.layout import ExtendedPersonLayout
from onegov.agency.models import AgencyMutation
from onegov.agency.models import AgencyMutationMessage
from onegov.agency.models import PersonMutation
from onegov.agency.models import PersonMutationMessage
from onegov.core.security import Private
from onegov.org.elements import Link


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from webob import Response


@AgencyApp.form(
    model=AgencyMutation,
    name='apply',
    template='form.pt',
    permission=Private,
    form=ApplyMutationForm
)
def apply_agency_mutation(
    self: AgencyMutation,
    request: AgencyRequest,
    form: ApplyMutationForm
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model()
        assert self.ticket is not None
        request.success(_('Proposed changes applied.'))
        AgencyMutationMessage.create(self.ticket, request, 'applied')
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    else:
        form.apply_model()

    layout = AgencyLayout(self.target, request)
    layout.breadcrumbs.append(Link(_('Apply proposed changes'), '#'))

    return {
        'layout': layout,
        'title': _('Apply proposed changes'),
        'form': form
    }


@AgencyApp.form(
    model=PersonMutation,
    name='apply',
    template='form.pt',
    permission=Private,
    form=ApplyMutationForm
)
def apply_person_mutation(
    self: PersonMutation,
    request: AgencyRequest,
    form: ApplyMutationForm
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model()
        assert self.ticket is not None
        request.success(_('Proposed changes applied.'))
        PersonMutationMessage.create(self.ticket, request, 'applied')
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    else:
        form.apply_model()

    layout = ExtendedPersonLayout(self.target, request)
    layout.breadcrumbs.append(Link(_('Apply proposed changes'), '#'))

    return {
        'layout': layout,
        'title': _('Apply proposed changes'),
        'form': form
    }
