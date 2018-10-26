from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.forms import MembershipForm
from onegov.agency.layouts import MembershipLayout
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.org.elements import Link
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection


@AgencyApp.html(
    model=AgencyMembership,
    template='membership.pt',
    permission=Public
)
def view_membership(self, request):

    return {
        'title': self.title,
        'membership': self,
        'layout': MembershipLayout(self, request)
    }


@AgencyApp.form(
    model=AgencyMembership,
    name='edit',
    template='form.pt',
    permission=Private,
    form=MembershipForm
)
def edit_membership(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = MembershipLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))

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
def delete_membership(self, request):

    request.assert_valid_csrf_token()
    AgencyMembershipCollection(request.session).delete(self)
