from __future__ import annotations

from onegov.activity import Occasion, OccasionNeed
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from sqlalchemy.orm import joinedload, undefer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.models import BookingPeriod, Volunteer
    from sqlalchemy.orm import Query, Session


@FeriennetApp.export(
    id='helfer',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_('Volunteers'),
    explanation=_('Exports volunteers in the given period.'),
)
class VolunteerExport(FeriennetExport):

    def run(
        self,
        form: PeriodExportForm,  # type:ignore[override]
        session: Session
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        assert form.selected_period is not None
        return self.rows(session, form.selected_period)

    def query(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Query[OccasionNeed]:

        q = session.query(OccasionNeed)
        q = q.filter(OccasionNeed.occasion_id.in_(
            session.query(Occasion.id)
            .filter(Occasion.period_id == period.id)
            .scalar_subquery()
        ))
        q = q.join(Occasion)
        q = q.options(
            joinedload(OccasionNeed.occasion)
            .joinedload(Occasion.activity)
        )
        q = q.options(
            joinedload(OccasionNeed.occasion)
            .joinedload(Occasion.period)
        )
        q = q.options(undefer('*'))
        q = q.order_by(Occasion.activity_id)

        return q

    def rows(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        for need in self.query(session, period):
            for volunteer in need.volunteers:
                yield ((k, v) for k, v in self.fields(volunteer))

    def fields(self, volunteer: Volunteer) -> Iterator[tuple[str, Any]]:

        yield from self.volunteer_fields(volunteer)
