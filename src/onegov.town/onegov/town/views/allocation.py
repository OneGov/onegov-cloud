import morepath

from libres.db.models import Allocation
from onegov.core.security import Public, Private
from onegov.libres import Resource, ResourceCollection
from onegov.town import TownApp, _, utils
from onegov.town.elements import Link
from onegov.town.layout import ResourceLayout
from onegov.town.forms import DaypassAllocationForm, RoomAllocationForm


@TownApp.json(model=Resource, name='slots', permission=Public)
def view_allocations_json(self, request):

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if start and end:
        scheduler = self.get_scheduler(request.app.libres_context)

        query = scheduler.allocations_in_range(start, end)
        query = query.order_by(Allocation._start)

        allocations = []

        for allocation in query.all():
            info = utils.AllocationEventInfo(allocation, request)
            allocations.append(info.as_dict())

        return allocations
    else:
        return []


def get_allocation_form_class(obj, request):

    if isinstance(obj, Allocation):
        resource = ResourceCollection(
            request.app.libres_context).by_id(obj.resource)
    else:
        resource = obj

    if resource.type == 'daypass':
        return DaypassAllocationForm

    if resource.type == 'room':
        return RoomAllocationForm

    raise NotImplementedError


@TownApp.form(model=Resource, template='form.pt', name='neue-einteilung',
              permission=Private, form=get_allocation_form_class)
def handle_new_allocation(self, request, form):

    if form.submitted(request):
        scheduler = self.get_scheduler(request.app.libres_context)

        allocations = scheduler.allocate(
            dates=form.dates,
            whole_day=form.whole_day,
            quota=form.quota,
            quota_limit=form.quota_limit,
            data=form.data
        )

        request.success(_("Successfully added ${n} allocations", mapping={
            'n': len(allocations)
        }))

        return morepath.redirect(request.link(self))

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))

    start, end = utils.parse_fullcalendar_request(request, self.timezone)
    whole_day = request.params.get('whole_day') == 'yes'

    if start and end:
        if whole_day:
            form.start.data = start
            form.end.data = end

            if hasattr(form, 'as_whole_day'):
                form.as_whole_day.data = 'yes'
        else:
            form.start.data = start
            form.end.data = end

            if hasattr(form, 'as_whole_day'):
                form.as_whole_day.data = 'no'

            if hasattr(form, 'start_time'):
                form.start_time.data = start.strftime('%H:%M')
                form.end_time.data = end.strftime('%H:%M')

    return {
        'layout': layout,
        'title': _("New allocation"),
        'form': form
    }


@TownApp.form(model=Allocation, template='form.pt', name='bearbeiten',
              permission=Private, form=get_allocation_form_class)
def handle_edit_allocation(self, request, form):
    pass


@TownApp.view(model=Allocation, request_method='DELETE', permission=Private)
def handle_delete_allocation(self, request):
    request.assert_valid_csrf_token()

    resources = ResourceCollection(request.app.libres_context)
    scheduler = resources.scheduler_by_id(self.resource)
    scheduler.remove_allocation(id=self.id)
