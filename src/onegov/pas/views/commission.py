from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import CommissionCollection
from onegov.pas.forms import CommissionMembershipAddForm
from onegov.pas.forms import CommissionForm
from onegov.pas.layouts import CommissionCollectionLayout
from onegov.pas.layouts import CommissionLayout
from onegov.pas.models import Commission
from onegov.pas.models import CommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=CommissionCollection,
    template='commissions.pt',
    permission=Private
)
def view_commissions(
    self: CommissionCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = CommissionCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'commissions': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=CommissionCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def add_commission(
    self: CommissionCollection,
    request: 'TownRequest',
    form: CommissionForm
) -> 'RenderData | Response':

    if form.submitted(request):
        commission = self.add(**form.get_useful_data())
        request.success(_("Added a new commission"))

        return request.redirect(request.link(commission))

    layout = CommissionCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New commission"),
        'form': form,
    }


@PasApp.html(
    model=Commission,
    template='commission.pt',
    permission=Private
)
def view_commission(
    self: Commission,
    request: 'TownRequest'
) -> 'RenderData':

    layout = CommissionLayout(self, request)

    return {
        'layout': layout,
        'commission': self,
        'title': layout.title,
    }


@PasApp.form(
    model=Commission,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def edit_commission(
    self: Commission,
    request: 'TownRequest',
    form: CommissionForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = CommissionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=Commission,
    request_method='DELETE',
    permission=Private
)
def delete_commission(
    self: Commission,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = CommissionCollection(request.session)
    collection.delete(self)


@PasApp.form(
    model=Commission,
    name='new-membership',
    template='form.pt',
    permission=Private,
    form=CommissionMembershipAddForm
)
def add_commission_membership(
    self: Commission,
    request: 'TownRequest',
    form: CommissionMembershipAddForm
) -> 'RenderData | Response':

    if form.submitted(request):
        self.memberships.append(
            CommissionMembership(**form.get_useful_data())
        )
        request.success(_("Added a new parliamentarian"))
        return request.redirect(request.link(self))

    layout = CommissionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New parliamentarian"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New parliamentarian"),
        'form': form,
    }
