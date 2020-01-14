from onegov.core.security import Private
from onegov.activity import OccasionNeed, Volunteer
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.layout import OccasionAttendeeLayout
from sqlalchemy.orm import joinedload


@FeriennetApp.html(
    model=OccasionAttendeeCollection,
    template='occasion_attendees.pt',
    permission=Private)
def view_occasion_attendees(self, request):

    def occasion_volunteers(occasion):
        return tuple(
            request.session.query(Volunteer)
            .options(joinedload(Volunteer.need))
            .filter(OccasionNeed.occasion_id == occasion.id)
            .filter(Volunteer.state == 'confirmed')
            .order_by(Volunteer.first_name, Volunteer.last_name)
        )

    return {
        'layout': OccasionAttendeeLayout(self, request),
        'title': _("Attendees for ${period}", mapping={
            'period': self.period.title
        }),
        'occasions': self.occasions(),
        'occasion_volunteers': occasion_volunteers,
        'periods': request.app.periods,
        'period': self.period,
        'model': self,
        'organisation': request.app.org,
    }
