from onegov.activity import Activity, Occasion
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
