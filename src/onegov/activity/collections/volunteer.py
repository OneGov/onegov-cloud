from onegov.activity.models import Volunteer
from onegov.core.collection import GenericCollection
from onegov.core.orm.sql import as_selectable_from_path
from onegov.core.utils import module_path
from sqlalchemy import select


class VolunteerCollection(GenericCollection):

    def __init__(self, session, period):
        super().__init__(session)
        self.period = period

    @property
    def model_class(self):
        return Volunteer

    @property
    def period_id(self):
        return self.period and self.period.id

    def report(self):
        stmt = as_selectable_from_path(
            module_path('onegov.activity', 'queries/volunteer-report.sql'))

        query = select(stmt.c).where(stmt.c.period_id == self.period.id)

        return self.session.execute(query)

    def for_period(self, period):
        return self.__class__(self.session, period)
