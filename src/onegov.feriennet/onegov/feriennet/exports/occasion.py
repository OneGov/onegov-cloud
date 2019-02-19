from onegov.activity import Activity, Occasion, OccasionNeed
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from sqlalchemy.orm import joinedload, undefer


@FeriennetApp.export(
    id='durchfuehrungen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_("Occasions"),
    explanation=_("Exports activities with an occasion in the given period."),
)
class OccasionExport(FeriennetExport):

    def run(self, form, session):
        return self.rows(session, form.selected_period)

    def query(self, session, period):
        q = session.query(Occasion)
        q = q.filter(Occasion.period_id == period.id)
        q = q.options(joinedload(Occasion.activity).joinedload(Activity.user))
        q = q.options(joinedload(Occasion.period))
        q = q.options(undefer('*'))
        q = q.order_by(Occasion.order)

        return q

    def rows(self, session, period):
        for occasion in self.query(session, period):
            yield ((k, v) for k, v in self.fields(occasion))

    def fields(self, occasion):
        yield from self.activity_fields(occasion.activity)
        yield from self.occasion_fields(occasion)
        yield from self.user_fields(occasion.activity.user)


@FeriennetApp.export(
    id='bedarf',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_("Needs"),
    explanation=_("Exports occasion needs."),
)
class OccasionNeedExport(FeriennetExport):

    def run(self, form, session):
        return self.rows(session, form.selected_period)

    def query(self, session, period):
        q = session.query(OccasionNeed)
        q = q.filter(OccasionNeed.occasion_id.in_(
            session.query(Occasion.id)
            .filter(Occasion.period_id == period.id)
            .subquery()
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

    def rows(self, session, period):
        for need in self.query(session, period):
            yield ((k, v) for k, v in self.fields(need))

    def fields(self, need):
        yield from self.activity_fields(need.occasion.activity)
        yield from self.occasion_fields(need.occasion)
        yield from self.occasion_need_fields(need)
