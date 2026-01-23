from __future__ import annotations

from onegov.activity import AttendeeCollection, Attendee, Booking
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodSelectForm
from onegov.form import merge_forms
from onegov.org.forms import ExportForm
from sqlalchemy import and_, not_


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.models import BookingPeriod, BookingPeriodMeta
    from sqlalchemy.orm import Query, Session


@FeriennetApp.export(
    id='unlucky',
    form_class=merge_forms(ExportForm, PeriodSelectForm),
    permission=Secret,
    title=_('Attendees without Bookings'),
    explanation=_('Attendees who were not granted any of their wishes'),
)
class UnluckyExport(FeriennetExport):

    def run(
        self,
        form: PeriodSelectForm,  # type:ignore[override]
        session: Session
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        assert form.selected_period is not None
        return self.rows(session, form.selected_period)

    def query(
        self,
        session: Session,
        period: BookingPeriod | BookingPeriodMeta
    ) -> Query[Attendee]:

        with_any_bookings = session.query(Booking.attendee_id).filter(
            Booking.period_id == period.id).scalar_subquery()  # type: ignore[attr-defined]

        with_accepted_bookings = session.query(Booking.attendee_id).filter(
            Booking.state == 'accepted',
            Booking.period_id == period.id).scalar_subquery()  # type: ignore[attr-defined]

        return AttendeeCollection(session).query().filter(
            and_(
                Attendee.id.in_(with_any_bookings),
                not_(Attendee.id.in_(with_accepted_bookings)),
            ))

    def rows(
        self,
        session: Session,
        period: BookingPeriod | BookingPeriodMeta
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        for user in self.query(session, period):
            yield ((k, v) for k, v in self.fields(user))

    def fields(self, attendee: Attendee) -> Iterator[tuple[str, Any]]:
        yield from self.attendee_fields(attendee)
        yield from self.user_fields(attendee.user)
