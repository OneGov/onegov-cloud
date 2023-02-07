from onegov.activity import Occasion, OccasionNeed
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from sqlalchemy.orm import joinedload, undefer


@FeriennetApp.export(
    id='helfer',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_("Volunteers"),
    explanation=_("Exports volunteers in the given period."),
)
class VolunteerExport(FeriennetExport):

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
        q = q.order_by(Occasion.activity_id)

        return q

    def rows(self, session, period):
        for need in self.query(session, period):
            for volunteer in need.volunteers:
                yield ((k, v) for k, v in self.fields(volunteer))

    def fields(self, volunteer):

        yield from self.volunteer_fields(volunteer)
