from morepath import redirect
from morepath.request import Response
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.forms import ExtendedAgencyForm
from onegov.agency.forms import MembershipForm
from onegov.agency.layouts import AgencyCollectionLayout
from onegov.agency.layouts import AgencyLayout
from onegov.agency.models import ExtendedAgency
from onegov.agency.pdf import AgencyPdf
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.org.elements import Link


@AgencyApp.html(
    model=ExtendedAgencyCollection,
    template='agencies.pt',
    permission=Public
)
def view_agencies(self, request):

    pdf_link = None
    if request.app.root_pdf_exists:
        pdf_link = request.link(self, name='pdf')

    return {
        'title': _("Agencies"),
        'agencies': self.roots,
        'pdf_link': pdf_link,
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
def add_root_agency(self, request, form):

    if form.submitted(request):
        agency = self.add_root(**form.get_useful_data())
        request.success(_("Added a new agency"))
        return redirect(request.link(agency))

    layout = AgencyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New agency"),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='new',
    template='form.pt',
    permission=Private,
    form=ExtendedAgencyForm
)
def add_agency(self, request, form):

    if form.submitted(request):
        collection = ExtendedAgencyCollection(request.session)
        agency = collection.add(self, **form.get_useful_data())
        request.success(_("Added a new agency"))
        return redirect(request.link(agency))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New agency"),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='new-membership',
    template='form.pt',
    permission=Private,
    form=MembershipForm
)
def add_membership(self, request, form):

    if form.submitted(request):
        self.add_person(**form.get_useful_data())
        request.success(_("Added a new membership"))
        return redirect(request.link(self))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("New membership"), '#'))

    return {
        'layout': layout,
        'title': _("New membership"),
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
        form.update_model(self)
        request.success(_("Your changes were saved"))
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@AgencyApp.view(
    model=ExtendedAgencyCollection,
    name='pdf',
    permission=Public
)
def get_root_pdf(self, request):

    if not request.app.root_pdf_exists:
        return Response(status='503 Service Unavailable')

    return Response(
        request.app.root_pdf,
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url(request.app.org.name)
        )
    )


@AgencyApp.form(
    model=ExtendedAgency,
    name='create-pdf',
    template='form.pt',
    permission=Private,
    form=Form
)
def create_agency_pdf(self, request, form):

    if form.submitted(request):
        self.pdf_file = AgencyPdf.from_agencies(
            [self],
            request.app.org.name
        )
        request.success(_("PDF created"))
        return redirect(request.link(self))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Create PDF"), '#'))

    return {
        'layout': layout,
        'title': _("Create PDF"),
        'helptext': _(
            "Create a PDF of this agency and all its suborganizations. "
            "This may take a while."
        ),
        'form': form
    }


@AgencyApp.view(
    model=ExtendedAgency,
    request_method='DELETE',
    permission=Private
)
def delete_agency(self, request):

    request.assert_valid_csrf_token()
    ExtendedAgencyCollection(request.session).delete(self)
