from __future__ import annotations

from onegov.activity.models import Volunteer
from onegov.core.collection import GenericCollection
from onegov.core.orm.sql import as_selectable_from_path
from onegov.core.utils import module_path
from sqlalchemy import select


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date, datetime
    from onegov.activity.models import BookingPeriod, BookingPeriodMeta
    from onegov.activity.models.volunteer import VolunteerState
    from sqlalchemy.engine import Result
    from sqlalchemy.orm import Session
    from uuid import UUID
    from typing import NamedTuple
    from typing import Self, TypeAlias

    class ReportRowWithVolunteer(NamedTuple):
        activity_id: UUID
        activity_title: str
        activity_name: str
        need_id: UUID
        need_name: str
        min_required: int
        max_required: int
        confirmed: int
        occasion_id: UUID
        period_id: UUID
        occasion_number: int
        volunteer_id: UUID
        first_name: str
        last_name: str
        address: str
        zip_code: str
        place: str
        organisation: str | None
        birth_date: date
        age: int
        email: str
        phone: str
        state: VolunteerState
        dates: Sequence[datetime]

    class ReportRowWithoutVolunteer(NamedTuple):
        activity_id: UUID
        activity_title: str
        activity_name: str
        need_id: UUID
        need_name: str
        min_required: int
        max_required: int
        confirmed: int
        occasion_id: UUID
        period_id: UUID
        occasion_number: int
        volunteer_id: None
        first_name: None
        last_name: None
        address: None
        zip_code: None
        place: None
        organisation: None
        birth_date: None
        age: None
        email: None
        phone: None
        state: None
        dates: Sequence[datetime]

    ReportRow: TypeAlias = ReportRowWithVolunteer | ReportRowWithoutVolunteer


class VolunteerCollection(GenericCollection[Volunteer]):

    def __init__(
        self,
        session: Session,
        period: BookingPeriod | BookingPeriodMeta | None
    ) -> None:
        super().__init__(session)
        self.period = period

    @property
    def model_class(self) -> type[Volunteer]:
        return Volunteer

    @property
    def period_id(self) -> UUID | None:
        return self.period and self.period.id or None

    def report(self) -> Result[ReportRow]:
        stmt = as_selectable_from_path(
            module_path('onegov.activity', 'queries/volunteer-report.sql'))

        query = select(*stmt.c).where(stmt.c.period_id == self.period_id)

        return self.session.execute(query)

    def for_period(
        self,
        period: BookingPeriod | BookingPeriodMeta | None
    ) -> Self:
        return self.__class__(self.session, period)
