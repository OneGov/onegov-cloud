from __future__ import annotations

from onegov.activity import Activity, Occasion, OccasionNeed
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from sqlalchemy.orm import joinedload, undefer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.models import BookingPeriod
    from sqlalchemy.orm import Query, Session


@FeriennetApp.export(
    id='durchfuehrungen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_('Occasions'),
    explanation=_('Exports activities with an occasion in the given period.'),
)
class OccasionExport(FeriennetExport):

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
    ) -> Query[Occasion]:
        q = session.query(Occasion)
        q = q.filter(Occasion.period_id == period.id)
        q = q.options(joinedload(Occasion.activity).joinedload(Activity.user))
        q = q.options(joinedload(Occasion.period))
        q = q.options(undefer('*'))
        q = q.order_by(Occasion.order)

        return q

    def rows(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        for occasion in self.query(session, period):
            yield ((k, v) for k, v in self.fields(occasion))

    def fields(self, occasion: Occasion) -> Iterator[tuple[str, Any]]:
        yield from self.activity_fields(occasion.activity)
        yield from self.occasion_fields(occasion)
        yield from self.user_fields(occasion.activity.user)


@FeriennetApp.export(
    id='bedarf',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_('Needs'),
    explanation=_('Exports occasion needs.'),
)
class OccasionNeedExport(FeriennetExport):

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
            .scalar_subquery()  # type: ignore[attr-defined]
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
        q = q.order_by(Occasion.order, OccasionNeed.name)

        return q

    def rows(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        for need in self.query(session, period):
            yield ((k, v) for k, v in self.fields(need))

    def fields(self, need: OccasionNeed) -> Iterator[tuple[str, Any]]:
        yield from self.activity_fields(need.occasion.activity)
        yield from self.occasion_fields(need.occasion)
        yield from self.occasion_need_fields(need)
