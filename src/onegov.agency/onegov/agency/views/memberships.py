from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.forms import MembershipForm
from onegov.agency.layouts import MembershipLayout
from onegov.agency.models import AgencyMembershipMove
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.org.elements import Link
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection


def get_membership_form_class(model, request):
    return model.with_content_extensions(MembershipForm, request)


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
    form=get_membership_form_class
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


@AgencyApp.view(
    model=AgencyMembershipMove,
    permission=Private,
    request_method='PUT'
)
def move_membership(self, request):
    request.assert_valid_csrf_token()
    self.execute()
