from libres.db.models import Allocation
from onegov.core.security import Public
from onegov.libres.models import Resource
from onegov.town import TownApp
from onegov.town import utils
from onegov.town.layout import ResourceLayout


@TownApp.html(model=Resource, template='resource.pt', permission=Public)
def view_resource(self, request):
    return {
        'title': self.title,
        'resource': self,
        'layout': ResourceLayout(self, request)
    }


@TownApp.json(model=Resource, name='slots', permission=Public)
def view_allocations_json(self, request):

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if start and end:
        scheduler = self.get_scheduler(request.app.libres_context)

        query = scheduler.allocations_in_range(start, end)
        query = query.order_by(Allocation._start)

        allocations = []

        for allocation in query.all():
            allocations.append(
                {
                    'start': allocation.display_start().isoformat(),
                    'end': allocation.display_end().isoformat()
                }
            )

        return allocations
    else:
        return []
