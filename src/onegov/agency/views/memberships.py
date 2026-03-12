from __future__ import annotations

from morepath import redirect
from morepath.request import Response
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.forms import MembershipForm
from onegov.agency.layout import MembershipLayout
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models.move import AgencyMembershipMoveWithinPerson
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.org.elements import Link
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from webob import Response as BaseResponse


def get_membership_form_class(
    model: ExtendedAgencyMembership,
    request: AgencyRequest
) -> type[MembershipForm]:
    return model.with_content_extensions(MembershipForm, request)


@AgencyApp.html(
    model=AgencyMembership,
    template='membership.pt',
    permission=Public
)
def view_membership(
    self: AgencyMembership,
    request: AgencyRequest
) -> RenderData:

    return {
        'title': self.title,
        'membership': self,
        'layout': MembershipLayout(self, request)
    }


@AgencyApp.form(
    model=ExtendedAgencyMembership,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_membership_form_class
)
def edit_membership(
    self: ExtendedAgencyMembership,
    request: AgencyRequest,
    form: MembershipForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = MembershipLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@AgencyApp.view(
    model=AgencyMembership,
    request_method='DELETE',
    permission=Private
)
def delete_membership(
    self: AgencyMembership,
    request: AgencyRequest
) -> None:

    request.assert_valid_csrf_token()
    AgencyMembershipCollection(request.session).delete(self)


@AgencyApp.view(
    model=AgencyMembershipMoveWithinAgency,
    permission=Private,
    request_method='PUT'
)
def move_membership_within_agency(
    self: AgencyMembershipMoveWithinAgency,
    request: AgencyRequest
) -> None:
    request.assert_valid_csrf_token()
    self.execute()


@AgencyApp.view(
    model=AgencyMembershipMoveWithinPerson,
    permission=Private,
    request_method='PUT'
)
def move_membership_within_person(
    self: AgencyMembershipMoveWithinPerson,
    request: AgencyRequest
) -> None:
    request.assert_valid_csrf_token()
    self.execute()


@AgencyApp.view(
    model=AgencyMembership,
    name='vcard',
    permission=Public
)
def vcard_export_membership(
    self: AgencyMembership,
    request: AgencyRequest
) -> Response:
    """ Returns the memberships vCard. """

    exclude = [*request.app.org.excluded_person_fields(request), 'notes']

    return Response(
        self.vcard(exclude),
        content_type='text/vcard',
        content_disposition='inline; filename=card.vcf'
    )
