from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from morepath import redirect
from morepath.request import Response
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.forms import AgencyMutationForm
from onegov.agency.forms import ExtendedAgencyForm
from onegov.agency.forms import MembershipForm
from onegov.agency.forms import MoveAgencyForm
from onegov.agency.layout import AgencyCollectionLayout
from onegov.agency.layout import AgencyLayout
from onegov.agency.models import AgencyMove
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.utils import emails_for_new_ticket
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.templates import render_macro
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.org.elements import Link
from onegov.org.forms.generic import ChangeAdjacencyListUrlForm
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage
from onegov.ticket import TicketCollection
from sqlalchemy.orm import joinedload
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from webob import Response as BaseResponse


def get_agency_form_class(
    model: object,
    request: AgencyRequest
) -> type[ExtendedAgencyForm]:

    if isinstance(model, ExtendedAgency):
        return model.with_content_extensions(ExtendedAgencyForm, request)
    return ExtendedAgency(title='title').with_content_extensions(
        ExtendedAgencyForm, request
    )


def get_membership_form_class(
    model: object,
    request: AgencyRequest
) -> type[MembershipForm]:

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
def view_agencies(
    self: ExtendedAgencyCollection,
    request: AgencyRequest
) -> RenderData:

    pdf_link = None
    root_pdf_modified = request.app.root_pdf_modified
    if root_pdf_modified is not None:
        self.root_pdf_modified = str(root_pdf_modified.timestamp())
        pdf_link = request.link(self, name='pdf')
    layout = AgencyCollectionLayout(self, request)

    return {
        'title': _('Agencies'),
        'agencies': self.roots,
        'pdf_link': pdf_link,
        'layout': layout
    }


@AgencyApp.html(
    model=ExtendedAgencyCollection,
    template='agencies_chart.pt',
    name='chart',
    permission=Public
)
def view_agencies_chart(
    self: ExtendedAgencyCollection,
    request: AgencyRequest
) -> RenderData:

    layout = AgencyCollectionLayout(self, request)
    request.include('d3-charts')

    layout.breadcrumbs.append(
        Link(_('Chart view'), request.link(self, name='chart'))
    )

    return {
        'title': _('Agencies'),
        'agencies': self.roots,
        'layout': layout
    }


@AgencyApp.json(
    model=ExtendedAgencyCollection,
    name='json',
    permission=Public
)
def view_agencies_json(
    self: ExtendedAgencyCollection,
    request: AgencyRequest
) -> RenderData:

    def to_node(agency: ExtendedAgency) -> dict[str, object]:
        node = {
            'id': agency.id,
            'name': agency.title,
            'url': request.link(agency)
        }
        children = [to_node(child) for child in agency.children]
        if children:
            node['children'] = children
        return node

    tree = [to_node(a) for a in self.roots]

    return {
        'tree': [
            {
            'id': 0,
            'url': request.link(self),
            'name': _('Agencies'),
            'children': tree
            }
        ]
    }


@AgencyApp.html(
    model=ExtendedAgencyCollection,
    template='custom_sort.pt',
    name='sort',
    permission=Private
)
def view_agencies_sort(
    self: ExtendedAgencyCollection,
    request: AgencyRequest
) -> RenderData:

    layout = AgencyCollectionLayout(self, request)

    return {
        'title': _('Sort'),
        'layout': layout,
        'items': (
            (
                _('Agencies'),
                layout.move_agency_url_template,
                ((agency.id, agency.title) for agency in self.roots)
            ),
        )
    }


@AgencyApp.html(
    model=ExtendedAgency,
    template='agency.pt',
    permission=Public
)
def view_agency(
    self: ExtendedAgency,
    request: AgencyRequest
) -> RenderData:

    return {
        'title': self.title,
        'agency': self,
        # NOTE: Avoid N+1 query for rendering the person's name
        'memberships': self.memberships.options(
            joinedload(ExtendedAgencyMembership.person)
        ).all(),
        'layout': AgencyLayout(self, request),
        'coordinates': self.coordinates
    }


@AgencyApp.html(
    model=ExtendedAgency,
    template='custom_sort.pt',
    name='sort',
    permission=Private
)
def view_agency_sort(
    self: ExtendedAgency,
    request: AgencyRequest
) -> RenderData:

    layout = AgencyLayout(self, request)
    return {
        'title': _('Sort'),
        'layout': layout,
        'items': (
            (
                _('Suborganizations'),
                layout.move_agency_url_template,
                ((agency.id, agency.title) for agency in self.children)
            ),
            (
                _('Memberships'),
                layout.move_membership_within_agency_url_template,
                (
                    (
                        membership.id,
                        f'{membership.person.title} - {membership.title}'
                    )
                    for membership in self.memberships
                )
            ),
        )
    }


@AgencyApp.view(
    model=ExtendedAgency,
    permission=Public,
    name='as-nav-item'
)
def view_agency_as_nav_item(
    self: ExtendedAgency,
    request: AgencyRequest
) -> str:
    layout = AgencyCollectionLayout(self, request)

    @request.after
    def push_history_state(response: BaseResponse) -> None:
        response.headers.add(
            'X-IC-PushURL',
            request.class_link(
                ExtendedAgencyCollection, {'browse': str(self.id)})
        )

    return render_macro(
        layout.macros['agency_nav_item_content'],
        request,
        {
            'agency': self,
            'layout': layout,
        }
    )


@AgencyApp.form(
    model=ExtendedAgencyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_agency_form_class
)
def add_root_agency(
    self: ExtendedAgencyCollection,
    request: AgencyRequest,
    form: ExtendedAgencyForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        agency = self.add_root(**form.get_useful_data())
        request.success(_('Added a new agency'))
        return redirect(request.link(agency))

    layout = AgencyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New agency'),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_agency_form_class
)
def add_agency(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: ExtendedAgencyForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        collection = ExtendedAgencyCollection(request.session)
        agency = collection.add(self, **form.get_useful_data())
        request.success(_('Added a new agency'))
        return redirect(request.link(agency))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New agency'),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='new-membership',
    template='form.pt',
    permission=Private,
    form=get_membership_form_class
)
def add_membership(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: MembershipForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        self.add_person(**form.get_useful_data())
        request.success(_('Added a new membership'))
        return redirect(request.link(self))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('New membership'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New membership'),
        'form': form
    }


@AgencyApp.view(
    model=ExtendedAgency,
    name='sort-relationships',
    request_method='POST',
    permission=Private,
)
def sort_relationships(self: ExtendedAgency, request: AgencyRequest) -> None:
    request.assert_valid_csrf_token()
    self.sort_relationships()


@AgencyApp.view(
    model=ExtendedAgency,
    name='sort-children',
    request_method='POST',
    permission=Private,
)
def sort_children(self: ExtendedAgency, request: AgencyRequest) -> None:
    request.assert_valid_csrf_token()
    self.sort_children()


@AgencyApp.form(
    model=ExtendedAgency,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_agency_form_class
)
def edit_agency(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: ExtendedAgencyForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Your changes were saved'))
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'button_text': _('Update')
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='change-url',
    template='form.pt',
    permission=Private,
    form=ChangeAdjacencyListUrlForm
)
def change_agency_url(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: ChangeAdjacencyListUrlForm
) -> RenderData | BaseResponse:

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('Change URL'), '#'))

    form.delete_field('test')

    if form.submitted(request):
        assert form.name.data is not None
        self.name = form.name.data
        request.success(_('Your changes were saved'))
        return redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': layout,
        'form': form,
        'title': _('Change URL'),
        'callout': _(
            'Stable URLs are important. Here you can change the path to your '
            'site independently from the title.'
        ),
    }


@AgencyApp.form(
    model=ExtendedAgency,
    name='move',
    template='form.pt',
    permission=Private,
    form=MoveAgencyForm
)
def move_agency(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: MoveAgencyForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Agency moved'))
        return redirect(request.link(self.proxy()))

    form.apply_model(self)

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('Move'), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'helptext': _(
            'Moves the whole agency and all its people and suborganizations '
            'to the given destination.'
        ),
        'form': form
    }


@AgencyApp.view(
    model=ExtendedAgencyCollection,
    name='pdf',
    permission=Public
)
def get_root_pdf(
    self: ExtendedAgencyCollection,
    request: AgencyRequest
) -> Response:

    last_modified = request.app.root_pdf_modified
    if last_modified is None:
        return Response(status='503 Service Unavailable')

    @request.after
    def cache_headers(response: BaseResponse) -> None:
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
def create_root_pdf(
    self: ExtendedAgencyCollection,
    request: AgencyRequest,
    form: Form
) -> RenderData | BaseResponse:

    org = request.app.org
    page_break_level = int(org.meta.get(
        'page_break_on_level_root_pdf', 1))

    org = request.app.org
    if form.submitted(request):
        request.app.root_pdf = request.app.pdf_class.from_agencies(
            agencies=self.roots,
            title=org.name,
            toc=True,
            exclude=org.hidden_people_fields,
            page_break_on_level=page_break_level,
            link_color=org.meta.get('pdf_link_color'),
            underline_links=org.meta.get('pdf_underline_links', False)
        ).getvalue()
        request.success(_('PDF created'))
        return redirect(request.link(self))

    layout = AgencyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Create PDF'), '#'))

    return {
        'layout': layout,
        'title': _('Create PDF'),
        'helptext': _(
            'Create a PDF of this agency and all its suborganizations. '
            'This may take a while.'
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
def create_agency_pdf(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: Form
) -> RenderData | BaseResponse:

    org = request.app.org
    page_break_level = int(org.meta.get(
        'page_break_on_level_org_pdf', 1))
    if form.submitted(request):
        self.pdf_file = request.app.pdf_class.from_agencies(
            agencies=[self],
            title=self.title,
            toc=False,
            exclude=org.hidden_people_fields,
            page_break_on_level=page_break_level,
            link_color=org.meta.get('pdf_link_color'),
            underline_links=org.meta.get('pdf_underline_links', False)
        )
        request.success(_('PDF created'))
        return redirect(request.link(self))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('Create PDF'), '#'))

    return {
        'layout': layout,
        'title': _('Create PDF'),
        'helptext': _(
            'Create a PDF of this agency and all its suborganizations. '
            'This may take a while.'
        ),
        'form': form
    }


@AgencyApp.view(
    model=ExtendedAgency,
    request_method='DELETE',
    permission=Private
)
def delete_agency(self: ExtendedAgency, request: AgencyRequest) -> None:
    if not self.deletable(request):
        request.alert(
            _("Agency with memberships or suborganizations can't be deleted")
        )
        return
    request.assert_valid_csrf_token()
    ExtendedAgencyCollection(request.session).delete(self)


@AgencyApp.view(
    model=AgencyMove,
    permission=Private,
    request_method='PUT'
)
def execute_agency_move(self: AgencyMove, request: AgencyRequest) -> None:
    request.assert_valid_csrf_token()
    self.execute()


@AgencyApp.form(
    model=ExtendedAgency,
    name='report-change',
    template='form.pt',
    permission=Public,
    form=AgencyMutationForm
)
def report_agency_change(
    self: ExtendedAgency,
    request: AgencyRequest,
    form: AgencyMutationForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        assert form.submitter_email.data is not None
        session = request.session
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='AGN',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(self.id),
                    'submitter_email': form.submitter_email.data,
                    'submitter_message': form.submitter_message.data,
                    'proposed_changes': form.proposed_changes
                }
            )
            TicketMessage.create(ticket, request, 'opened', 'external')
            ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_('Your ticket has been opened'),
            receivers=(form.submitter_email.data, ),
            ticket=ticket
        )

        for email in emails_for_new_ticket(self, request):
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened_info.pt',
                subject=_('New ticket'),
                ticket=ticket,
                receivers=(email, ),
                content={
                    'model': ticket
                }
            )

        request.app.send_websocket(
            channel=request.app.websockets_private_channel,
            message={
                'event': 'browser-notification',
                'title': request.translate(_('New ticket')),
                'created': ticket.created.isoformat()
            }
            # FIXME: set groupids to all groups which are linked
            #        to this agency or the first parent agency with
            #        links to one or more groups, to mirror email
            #        notifications.
        )

        request.success(_('Thank you for your submission!'))
        return redirect(request.link(ticket, 'status'))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_('Report change'), '#'))

    return {
        'layout': layout,
        'title': _('Report change'),
        'lead': self.title,
        'form': form
    }
