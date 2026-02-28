from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import groupby
from morepath import redirect
from morepath.request import Response
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.excel_export import export_person_xlsx
from onegov.agency.forms import PersonMutationForm
from onegov.agency.layout import ExtendedPersonCollectionLayout
from onegov.agency.layout import ExtendedPersonLayout
from onegov.agency.models import ExtendedPerson
from onegov.agency.utils import emails_for_new_ticket
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.form import Form
from onegov.org.elements import Link
from onegov.agency.forms.person import AgencyPersonForm
from onegov.org.mail import send_ticket_mail
from onegov.org.models import AtoZ
from onegov.org.models import TicketMessage
from onegov.org.views.people import (
    handle_delete_person as org_handle_delete_person)
from onegov.ticket import TicketCollection
from unidecode import unidecode
from uuid import uuid4


from typing import NamedTuple
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from onegov.ticket import Ticket
    from webob import Response as BaseResponse
    from onegov.agency.forms.person import AuthenticatedPersonMutationForm


class FilterOption(NamedTuple):
    title: str
    value: str
    selected: bool


def get_person_form_class(
    model: object,
    request: AgencyRequest
) -> type[AgencyPersonForm]:

    if isinstance(model, ExtendedPerson):
        return model.with_content_extensions(AgencyPersonForm, request)
    return ExtendedPerson().with_content_extensions(AgencyPersonForm, request)


@AgencyApp.html(
    model=ExtendedPersonCollection,
    template='extended_people.pt',
    permission=Public
)
def view_people(
    self: ExtendedPersonCollection,
    request: AgencyRequest
) -> RenderData:

    people_xlsx_link = None
    last_modified = request.app.people_xlsx_modified
    if last_modified is not None:
        self.xlsx_modified = str(last_modified.timestamp())
        people_xlsx_link = request.link(self, name='people-xlsx')

    if not request.is_logged_in:
        self.exclude_hidden = True

    letters = [
        Link(
            text=letter.upper(),
            url=request.link(
                self.for_filter(
                    letter=letter if (letter != self.letter) else None
                )
            ),
            active=(letter == self.letter),
        ) for letter in self.used_letters
    ]

    agencies = [
        FilterOption(
            title=agency,
            value=request.link(self.for_filter(agency=agency)),
            selected=(agency == self.agency),
        ) for agency in self.used_agencies
    ]
    agencies.insert(
        0,
        FilterOption(
            title='',
            value=request.link(self.for_filter(agency=None)),
            selected=(self.agency is None),
        )
    )

    people = self.batch

    class AtoZPeople(AtoZ[ExtendedPerson]):

        def get_title(self, item: ExtendedPerson) -> str:
            return item.title

        def get_items(self) -> tuple[ExtendedPerson, ...]:
            return people

        def get_items_by_letter(self) -> dict[str, tuple[ExtendedPerson, ...]]:
            items_by_letter = OrderedDict()
            for letter, items in groupby(self.get_items(), self.sortkey):
                items_by_letter[unidecode(letter)] = tuple(items)
            return items_by_letter

    people_by_letter = AtoZPeople(request).get_items_by_letter()

    return {
        'title': _('People'),
        'layout': ExtendedPersonCollectionLayout(self, request),
        'letters': letters,
        'agencies': agencies,
        'people': people_by_letter.items(),
        'people_xlsx_link': people_xlsx_link
    }


@AgencyApp.form(
    model=ExtendedPersonCollection,
    name='create-people-xlsx',
    permission=Private,
    template='form.pt',
    form=Form
)
def create_people_xlsx(
    self: ExtendedPersonCollection,
    request: AgencyRequest,
    form: Form
) -> RenderData | BaseResponse:

    if form.submitted(request):
        request.app.people_xlsx = export_person_xlsx(
            request.session
        ).getvalue()
        if request.app.people_xlsx_exists:
            request.success(_('Excel file created'))
            return redirect(request.link(self))
        else:
            request.success(_('Excel could not be created'))
            return redirect(request.link(self, name='create-people-xlsx'))

    layout = ExtendedPersonCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': _('Create Excel'),
        'helptext': _(
            'Create an Excel of persons and their memberships. '
            'This may take a while.'
        ),
        'form': form
    }


@AgencyApp.view(
    model=ExtendedPersonCollection,
    name='people-xlsx',
    permission=Private
)
def get_people_xlsx(
    self: ExtendedPersonCollection,
    request: AgencyRequest
) -> Response:

    if not request.app.people_xlsx_exists:
        return Response(status='503 Service Unavailable')

    @request.after
    def cache_headers(response: BaseResponse) -> None:
        last_modified = request.app.people_xlsx_modified
        if last_modified:
            max_age = 1 * 24 * 60 * 60
            expires = datetime.now() + timedelta(seconds=max_age)
            fmt = '%a, %d %b %Y %H:%M:%S GMT'

            response.headers.add('Cache-Control', f'max-age={max_age}, public')
            response.headers.add('ETag', last_modified.isoformat())
            response.headers.add('Expires', expires.strftime(fmt))
            response.headers.add('Last-Modified', last_modified.strftime(fmt))

    return Response(
        request.app.people_xlsx,
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename=people.xlsx'
    )


@AgencyApp.html(
    model=ExtendedPerson,
    template='person.pt',
    permission=Public
)
def view_person(
    self: ExtendedPerson,
    request: AgencyRequest
) -> RenderData:

    return {
        'title': self.title,
        'person': self,
        'layout': ExtendedPersonLayout(self, request)
    }


@AgencyApp.html(
    model=ExtendedPerson,
    template='custom_sort.pt',
    name='sort',
    permission=Private
)
def view_sort_person(
    self: ExtendedPerson,
    request: AgencyRequest
) -> RenderData:

    layout = ExtendedPersonLayout(self, request)

    return {
        'title': _('Sort'),
        'layout': layout,
        'items': (
            (
                _('Memberships'),
                layout.move_membership_url_template,
                (
                    (
                        membership.id,
                        f'{membership.agency.title} - {membership.title}'
                    )
                    for membership in self.memberships_by_agency
                )
            ),
        )
    }


@AgencyApp.form(
    model=ExtendedPersonCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_person_form_class
)
def add_person(
    self: ExtendedPersonCollection,
    request: AgencyRequest,
    form: AgencyPersonForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        person = self.add(**form.get_useful_data())
        request.success(_('Added a new person'))

        return redirect(request.link(person))

    layout = ExtendedPersonCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New person'),
        'form': form
    }


@AgencyApp.form(
    model=ExtendedPerson,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_person_form_class
)
def edit_person(
    self: ExtendedPerson,
    request: AgencyRequest,
    form: AgencyPersonForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    else:
        form.process(obj=self)

    layout = ExtendedPersonLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@AgencyApp.view(
    model=ExtendedPerson,
    request_method='DELETE',
    permission=Private)
def handle_delete_person(
    self: ExtendedPerson,
    request: AgencyRequest
) -> None:

    if not self.deletable(request):
        request.alert(_("People with memberships can't be deleted"))
        return
    return org_handle_delete_person(self, request)


def do_report_person_change(
    self: ExtendedPerson,
    request: AgencyRequest,
    form: PersonMutationForm | AuthenticatedPersonMutationForm
) -> Ticket:

    session = request.session
    with session.no_autoflush:
        ticket = TicketCollection(session).open_ticket(
            handler_code='PER',
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

    assert form.submitter_email.data is not None
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
        #        to the agencies of this person or the first
        #        parent agency for each agency with links to
        #        one or more groups, to mirror email notifications
    )

    return ticket


@AgencyApp.form(
    model=ExtendedPerson,
    name='report-change',
    template='form.pt',
    permission=Public,
    form=PersonMutationForm
)
def report_person_change(
    self: ExtendedPerson,
    request: AgencyRequest,
    form: PersonMutationForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        ticket = do_report_person_change(self, request, form)
        request.success(_('Thank you for your submission!'))
        return redirect(request.link(ticket, 'status'))

    layout = ExtendedPersonLayout(self, request)
    layout.breadcrumbs.append(Link(_('Report change'), '#'))

    return {
        'layout': layout,
        'title': _('Report change'),
        'lead': self.title,
        'form': form
    }
