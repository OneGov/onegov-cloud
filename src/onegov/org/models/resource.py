from __future__ import annotations

import sedate

from datetime import date, datetime

from libres.db.models import ReservedSlot

from onegov.core.orm.mixins import (
    dict_markup_property, dict_property, meta_property)
from onegov.core.orm.types import UUID
from onegov.form.models import FormSubmission
from onegov.org.models.extensions import (
    ContactExtension, GeneralFileLinkExtension, ResourceValidationExtension)
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import PersonLinkExtension
from onegov.reservation import Resource, ResourceCollection, Reservation
from onegov.search import SearchableContent
from onegov.ticket import Ticket
from sqlalchemy.orm import undefer
from sqlalchemy.sql.expression import cast
from uuid import uuid4, uuid5


from typing import ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from libres.context.core import Context
    from libres.db.scheduler import Scheduler
    from onegov.org.request import OrgRequest
    from sqlalchemy import Column
    from sqlalchemy.orm import Query


class FindYourSpotCollection(ResourceCollection):

    def __init__(
        self,
        libres_context: Context,
        group: str | None = None,
        subgroup: str | None = None,
    ) -> None:
        super().__init__(libres_context)
        self.group = group
        self.subgroup = subgroup

    def query(self) -> Query[Resource]:
        query = self.session.query(Resource)
        # we only support find-your-spot for rooms for now
        query = query.filter(Resource.type == 'room')
        query = query.filter(Resource.group == (self.group or ''))
        if self.subgroup is not None:
            query = query.filter(Resource.subgroup == self.subgroup)
        return query


class SharedMethods:

    if TYPE_CHECKING:
        title_template: ClassVar[str]
        id: Column[uuid.UUID]
        libres_context: Context
        date: date | None
        view: str | None
        timezone: Column[str]

        @property
        def scheduler(self) -> Scheduler: ...
        def get_scheduler(self, context: Context) -> Scheduler: ...

    lead: dict_property[str | None] = meta_property()
    text = dict_markup_property('content')
    confirmation_text = dict_markup_property('content')
    occupancy_is_visible_to_members: dict_property[bool | None]
    occupancy_is_visible_to_members = meta_property()

    @property
    def deletable(self) -> bool:
        # FIXME: use exists() subqueries for speed
        if self.scheduler.managed_reserved_slots().first():
            return False

        if self.scheduler.managed_reservations().first():
            return False

        return True

    @property
    def future_managed_reservations(self) -> Query[Reservation]:
        return self.scheduler.managed_reservations().filter(  # type:ignore
            Reservation.end >= sedate.utcnow())

    @property
    def future_managed_reserved_slots(self) -> Query[ReservedSlot]:
        return self.scheduler.managed_reserved_slots().filter(
            ReservedSlot.end >= sedate.utcnow())

    @property
    def calendar_date_range(self) -> tuple[datetime, datetime]:
        """ Returns the date range set by the fullcalendar specific params. """

        if self.date:
            date = datetime(self.date.year, self.date.month, self.date.day)
            date = sedate.replace_timezone(date, self.timezone)
        else:
            date = sedate.to_timezone(sedate.utcnow(), self.timezone)

        if self.view in ('multiMonthYear', 'listYear'):
            return sedate.replace_timezone(
                datetime(date.year, 1, 1),
                self.timezone
            ), sedate.replace_timezone(
                datetime(date.year, 12, 31, 23, 59, 59, 999999),
                self.timezone
            )
        elif self.view in ('dayGridMonth', 'listMonth'):
            return sedate.align_range_to_month(date, date, self.timezone)
        elif self.view in ('timeGridWeek', 'listWeek'):
            return sedate.align_range_to_week(date, date, self.timezone)
        elif self.view in ('timeGridDay', 'listDay'):
            return sedate.align_range_to_day(date, date, self.timezone)
        else:
            raise NotImplementedError()

    def remove_expired_reservation_sessions(
        self,
        expiration_date: datetime | None = None
    ) -> None:

        session = self.libres_context.get_service('session_provider').session()
        queries = self.scheduler.queries

        expired_sessions = queries.find_expired_reservation_sessions(
            expiration_date)

        if expired_sessions:
            query = session.query(Reservation).with_entities(Reservation.token)
            query = query.filter(Reservation.session_id.in_(expired_sessions))
            tokens = {token for token, in query.all()}

            query = session.query(FormSubmission)
            query = query.filter(FormSubmission.name == None)
            query = query.filter(FormSubmission.id.in_(tokens))

            query.delete('fetch')
            queries.remove_expired_reservation_sessions(expiration_date)

    def bound_reservations(
        self,
        request: OrgRequest,
        status: str = 'pending',
        with_data: bool = False
    ) -> Query[Reservation]:
        """ The reservations associated with this resource and user. """

        session = self.bound_session_id(request)
        scheduler = self.get_scheduler(request.app.libres_context)

        res = scheduler.queries.reservations_by_session(session)
        res = res.filter(Reservation.resource == self.id)
        res = res.filter(Reservation.status == status)
        res = res.order_by(None)  # clear existing order
        res = res.order_by(Reservation.start)

        # used by ReservationInfo
        res = res.options(undefer(Reservation.created))

        if with_data:
            res = res.options(undefer(Reservation.data))

        return res

    def bound_session_id(self, request: OrgRequest) -> uuid.UUID:
        """ The session id associated with this resource and user. """
        if not request.browser_session.has('libres_session_id'):
            request.browser_session.libres_session_id = uuid4()

        return uuid5(self.id, request.browser_session.libres_session_id.hex)

    def reservations_with_tickets_query(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        exclude_pending: bool = True
    ) -> Query[Reservation]:
        """ Returns a query which joins this resource's reservations between
        start and end with the tickets table.

        """
        query = self.scheduler.managed_reservations()
        if start:
            query = query.filter(start <= Reservation.start)
        if end:
            query = query.filter(Reservation.end <= end)

        query = query.join(
            Ticket, Reservation.token == cast(Ticket.handler_id, UUID))

        query = query.order_by(Reservation.start)
        query = query.order_by(Ticket.subtitle)
        query = query.filter(Reservation.status == 'approved')
        if exclude_pending:
            query = query.filter(Reservation.data['accepted'] == True)

        return query

    def reservation_title(self, reservation: Reservation) -> str:
        title = self.title_template.format(
            start=reservation.display_start(),
            end=reservation.display_end(),
            quota=reservation.quota
        )

        if title.endswith('00:00'):
            return title[:-5] + '24:00'

        return title


class DaypassResource(Resource, AccessExtension, SearchableContent,
                      ContactExtension, PersonLinkExtension,
                      CoordinatesExtension, SharedMethods,
                      ResourceValidationExtension, GeneralFileLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'daypass'}

    es_type_name = 'daypasses'

    # the selected view
    view = 'dayGridMonth'

    # show or hide quota numbers in reports
    show_quota = True

    # use to render the reservation title
    title_template = '{start:%d.%m.%Y} ({quota})'


class RoomResource(Resource, AccessExtension, SearchableContent,
                   ContactExtension, PersonLinkExtension,
                   CoordinatesExtension, SharedMethods,
                   ResourceValidationExtension, GeneralFileLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'room'}

    es_type_name = 'rooms'

    # the selected view (depends on the resource's default)
    view = None

    # show or hide quota numbers in reports
    show_quota = False

    # used to render the reservation title
    title_template = '{start:%d.%m.%Y} {start:%H:%M} - {end:%H:%M}'

    kaba_components: dict_property[list[tuple[str, str]]]
    kaba_components = meta_property(default=list)

    @property
    def deletable(self) -> bool:
        if self.future_managed_reserved_slots.first():
            return False

        if self.future_managed_reservations.first():
            return False

        return True


class ItemResource(Resource, AccessExtension, SearchableContent,
                   ContactExtension, PersonLinkExtension,
                   CoordinatesExtension, SharedMethods,
                   ResourceValidationExtension, GeneralFileLinkExtension):

    __mapper_args__ = {'polymorphic_identity': 'daily-item'}

    es_type_name = 'daily_items'

    view = None

    show_quota = True

    title_template = '{start:%d.%m.%Y} {start:%H:%M} - {end:%H:%M} ({quota})'

    kaba_components: dict_property[list[tuple[str, str]]]
    kaba_components = meta_property(default=list)
