from __future__ import annotations

from onegov.agency.app import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMembershipMoveWithinPerson
from onegov.agency.models import AgencyMove
from onegov.agency.models import AgencyMutation
from onegov.agency.models import AgencyProxy
from onegov.agency.models import PersonMutation
from onegov.core.converters import LiteralConverter
from onegov.core.orm.abstract import MoveDirection
from onegov.people import Agency
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection
from onegov.ticket import TicketCollection
from onegov.ticket.collection import ArchivedTicketCollection
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.models import ExtendedAgency
    from onegov.ticket.collection import ExtendedTicketState


@AgencyApp.path(
    model=ExtendedPersonCollection,
    path='/people',
    converters={'page': int}
)
def get_people(
    app: AgencyApp,
    page: int = 0,
    letter: str | None = None,
    agency: str | None = None,
    xlsx_modified: str | None = None
) -> ExtendedPersonCollection:
    return ExtendedPersonCollection(
        app.session(), page, letter, agency, xlsx_modified)


@AgencyApp.path(
    model=ExtendedAgencyCollection,
    path='/organizations',
)
def get_agencies(
    app: AgencyApp,
    root_pdf_modified: str | None = None,
    browse: str | None = None
) -> ExtendedAgencyCollection:
    return ExtendedAgencyCollection(app.session(), root_pdf_modified, browse)


@AgencyApp.path(
    model=Agency,
    path='/organization',
    absorb=True
)
def get_agency(app: AgencyApp, absorb: str) -> ExtendedAgency | None:
    collection = ExtendedAgencyCollection(app.session())
    return collection.by_path(absorb)


@AgencyApp.path(
    model=AgencyProxy,
    path='/agency/{id}',
    converters={'id': int}
)
def get_agency_proxy(app: AgencyApp, id: int) -> ExtendedAgency | None:
    return ExtendedAgencyCollection(app.session()).by_id(id)


@AgencyApp.path(
    model=AgencyMove,
    path='/move/agency/{subject_id}/{direction}/{target_id}',
    converters={
        'subject_id': int,
        'direction': MoveDirection,
        'target_id': int
    }
)
def get_agency_move(
    app: AgencyApp,
    subject_id: int,
    direction: MoveDirection,
    target_id: int
) -> AgencyMove:
    return AgencyMove(app.session(), subject_id, target_id, direction)


@AgencyApp.path(
    model=AgencyMembership,
    path='/membership/{id}',
    converters={'id': UUID}
)
def get_membership(app: AgencyApp, id: UUID) -> AgencyMembership | None:
    return AgencyMembershipCollection(app.session()).by_id(id)


@AgencyApp.path(
    model=AgencyMembershipMoveWithinAgency,
    path='/move-for-agency/membership/{subject_id}/{direction}/{target_id}',
    converters={
        'subject_id': UUID,
        'direction': MoveDirection,
        'target_id': UUID
    }
)
def get_membership_move_for_agency(
    app: AgencyApp,
    subject_id: UUID,
    direction: MoveDirection,
    target_id: UUID
) -> AgencyMembershipMoveWithinAgency | None:
    return AgencyMembershipMoveWithinAgency(
        app.session(),
        subject_id,
        target_id,
        direction
    )


@AgencyApp.path(
    model=AgencyMembershipMoveWithinPerson,
    path='/move-for-person/membership/{subject_id}/{direction}/{target_id}',
    converters={
        'subject_id': UUID,
        'direction': MoveDirection,
        'target_id': UUID
    }
)
def get_membership_move_for_person(
    app: AgencyApp,
    subject_id: UUID,
    direction: MoveDirection,
    target_id: UUID
) -> AgencyMembershipMoveWithinPerson | None:
    return AgencyMembershipMoveWithinPerson(
        app.session(),
        subject_id,
        target_id,
        direction
    )


@AgencyApp.path(
    model=AgencyMutation,
    path='/mutation/agency/{target_id}/{ticket_id}',
    converters={'target_id': int, 'ticket_id': UUID}
)
def get_agency_mutation(
    app: AgencyApp,
    target_id: int,
    ticket_id: UUID
) -> AgencyMutation:
    return AgencyMutation(app.session(), target_id, ticket_id)


@AgencyApp.path(
    model=PersonMutation,
    path='/mutation/person/{target_id}/{ticket_id}',
    converters={'target_id': UUID, 'ticket_id': UUID}
)
def get_person_mutation(
    app: AgencyApp,
    target_id: UUID,
    ticket_id: UUID
) -> PersonMutation:
    return PersonMutation(app.session(), target_id, ticket_id)


@AgencyApp.path(
    model=TicketCollection,
    path='/tickets/{handler}/{state}',
    converters={'page': int, 'state': LiteralConverter(
        'open',
        'pending',
        'closed',
        'archived',
        'all',
        'unfinished'
    )}
)
def get_tickets(
    app: AgencyApp,
    handler: str = 'ALL',
    state: ExtendedTicketState | None = 'open',
    page: int = 0,
    group: str | None = None,
    owner: str | None = None,
    submitter: str | None = None,
    q: str | None = None,
    extra_parameters: dict[str, str] | None = None
) -> TicketCollection | None:

    if state is None:
        return None

    # NOTE: agency has its own ticket filterting that's different
    #       from org's, eventually we probably want to implement this
    #       logic into the query as well
    return TicketCollection(
        app.session(),
        handler=handler,
        state=state,
        page=page,
        group=group,
        owner=owner or '*',
        submitter=submitter or '*',
        term=q,
        extra_parameters=extra_parameters,
    )


@AgencyApp.path(
    model=ArchivedTicketCollection,
    path='/tickets-archive/{handler}',
    converters={'page': int}
)
def get_archived_tickets(
    app: AgencyApp,
    handler: str = 'ALL',
    page: int = 0,
    group: str | None = None,
    owner: str | None = None,
    submitter: str | None = None,
    q: str | None = None,
    extra_parameters: dict[str, str] | None = None
) -> ArchivedTicketCollection:
    # NOTE: agency has its own ticket filterting that's different
    #       from org's, eventually we probably want to implement this
    #       logic into the query as well
    return ArchivedTicketCollection(
        app.session(),
        handler=handler,
        state='archived',
        page=page,
        group=group,
        owner=owner or '*',
        submitter=submitter or '*',
        term=q,
        extra_parameters=extra_parameters,
    )
