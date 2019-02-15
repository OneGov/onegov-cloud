from datetime import datetime
from datetime import timedelta
from morepath import redirect
from morepath.request import Response
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.forms import ExtendedAgencyForm
from onegov.agency.forms import MembershipForm
from onegov.agency.forms import MoveAgencyForm
from onegov.agency.layouts import AgencyCollectionLayout
from onegov.agency.layouts import AgencyLayout
from onegov.agency.models import AgencyMove
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.org.elements import Link


def get_agency_form_class(model, request):
    if isinstance(model, ExtendedAgency):
        return model.with_content_extensions(ExtendedAgencyForm, request)
    return ExtendedAgency(title='title').with_content_extensions(
        ExtendedAgencyForm, request
    )


def get_membership_form_class(model, request):
    if isinstance(model, ExtendedAgencyMembership):
        return model.with_content_extensions(MembershipForm, request)
    return ExtendedAgencyMembership().with_content_extensions(
        MembershipForm, request
    )


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
    form=get_agency_form_class
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
    form=get_agency_form_class
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
    form=get_membership_form_class
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


@AgencyApp.view(
    model=ExtendedAgency,
    name='sort-relationships',
    request_method='POST',
    permission=Private,
)
def sort_relationships(self, request):
    request.assert_valid_csrf_token()
    self.sort_relationships()


@AgencyApp.view(
    model=ExtendedAgency,
    name='sort-children',
    request_method='POST',
    permission=Private,
)
def sort_children(self, request):
    request.assert_valid_csrf_token()
    self.sort_children()


@AgencyApp.form(
    model=ExtendedAgency,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_agency_form_class
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


@AgencyApp.form(
    model=ExtendedAgency,
    name='move',
    template='form.pt',
    permission=Private,
    form=MoveAgencyForm
)
def move_agency(self, request, form):

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Agency moved"))
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Move"), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'helptext': _(
            "Moves the whole agency and all its people and suborganizations "
            "to the given destination."
        ),
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

    @request.after
    def cache_headers(response):
        last_modified = request.app.root_pdf_modified
        if last_modified:
            max_age = 1 * 24 * 60 * 60
            expires = datetime.now() + timedelta(seconds=max_age)
            fmt = '%a, %d %b %Y %H:%M:%S GMT'

            response.headers.add('Cache-Control', f'max-age={max_age}, public')
            response.headers.add('ETag', last_modified.isoformat())
            response.headers.add('Expires', expires.strftime(fmt))
            response.headers.add('Last-Modified', last_modified.strftime(fmt))

    return Response(
        request.app.root_pdf,
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url(request.app.org.name)
        )
    )


@AgencyApp.form(
    model=ExtendedAgencyCollection,
    name='create-pdf',
    template='form.pt',
    permission=Private,
    form=Form
)
def create_root_pdf(self, request, form):

    if form.submitted(request):
        request.app.root_pdf = request.app.pdf_class.from_agencies(
            agencies=self.roots,
            title=request.app.org.name,
            toc=True,
            exclude=request.app.org.hidden_people_fields
        )
        request.success(_("PDF created"))
        return redirect(request.link(self))

    layout = AgencyCollectionLayout(self, request)
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


@AgencyApp.form(
    model=ExtendedAgency,
    name='create-pdf',
    template='form.pt',
    permission=Private,
    form=Form
)
def create_agency_pdf(self, request, form):

    if form.submitted(request):
        self.pdf_file = request.app.pdf_class.from_agencies(
            agencies=[self],
            title=self.title,
            toc=False,
            exclude=request.app.org.hidden_people_fields
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


@AgencyApp.view(
    model=AgencyMove,
    permission=Private,
    request_method='PUT'
)
def execute_agency_move(self, request):
    request.assert_valid_csrf_token()
    self.execute()
