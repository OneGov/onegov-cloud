from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.forms import ExtendedAgencyForm
from onegov.agency.layouts import AgencyCollectionLayout
from onegov.agency.layouts import AgencyLayout
from onegov.agency.models import ExtendedAgency
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.org.elements import Link


@AgencyApp.html(
    model=ExtendedAgencyCollection,
    template='agencies.pt',
    permission=Public
)
def view_agencies(self, request):

    return {
        'title': _("Agencies"),
        'agencies': self.roots,
        'layout': AgencyCollectionLayout(self, request)
    }


@AgencyApp.html(
    model=ExtendedAgency,
    template='agency.pt',
    permission=Public
)
def view_agency(self, request):

    return {
        'title': self.title,
        'agency': self,
        'layout': AgencyLayout(self, request)
    }


@AgencyApp.form(
    model=ExtendedAgencyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ExtendedAgencyForm
)
def add_agency(self, request, form):

    if form.submitted(request):
        agency = self.add(**form.get_useful_data())
        request.success(_("Added a new agency"))

        return redirect(request.link(agency))

    layout = AgencyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New agency"),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ExtendedAgencyForm
)
def edit_agency(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }
