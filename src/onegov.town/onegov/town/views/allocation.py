import morepath

from libres.db.models import Allocation
from libres.modules.errors import LibresError
from onegov.core.security import Public, Private
from onegov.libres import Resource, ResourceCollection
from onegov.town import TownApp, _, utils
from onegov.town.elements import Link
from onegov.town.layout import ResourceLayout, AllocationEditFormLayout
from onegov.town.forms import (
    DaypassAllocationForm,
    DaypassAllocationEditForm,
    RoomAllocationForm,
    RoomAllocationEditForm
)


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


def get_new_allocation_form_class(resource, request):

    if resource.type == 'daypass':
        return DaypassAllocationForm

    if resource.type == 'room':
        return RoomAllocationForm

    raise NotImplementedError


def get_edit_allocation_form_class(allocation, request):

    resource = ResourceCollection(
        request.app.libres_context).by_id(allocation.resource)

    if resource.type == 'daypass':
        return DaypassAllocationEditForm

    if resource.type == 'room':
        return RoomAllocationEditForm

    raise NotImplementedError


@TownApp.form(model=Resource, template='form.pt', name='neue-einteilung',
              permission=Private, form=get_new_allocation_form_class)
def handle_new_allocation(self, request, form):

    if form.submitted(request):
        scheduler = self.get_scheduler(request.app.libres_context)

        try:
            allocations = scheduler.allocate(
                dates=form.dates,
                whole_day=form.whole_day,
                quota=form.quota,
                quota_limit=form.quota_limit,
                data=form.data
            )
        except LibresError as e:
            utils.show_libres_error(e, request)
        else:
            request.success(_("Successfully added ${n} allocations", mapping={
                'n': len(allocations)
            }))

            return morepath.redirect(request.link(self))

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("New allocation"), '#'))
    layout.editbar_links = None

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
              permission=Private, form=get_edit_allocation_form_class)
def handle_edit_allocation(self, request, form):

    resources = ResourceCollection(request.app.libres_context)
    resource = resources.by_id(self.resource)

    if form.submitted(request):
        resources = ResourceCollection(request.app.libres_context)
        resource = resources.by_id(self.resource)
        scheduler = resource.get_scheduler(request.app.libres_context)

        new_start, new_end = form.dates

        try:
            scheduler.move_allocation(
                master_id=self.id,
                new_start=new_start,
                new_end=new_end,
                new_quota=form.quota,
                quota_limit=form.quota_limit
            )
        except LibresError as e:
            utils.show_libres_error(e, request)
        else:
            request.success(_("Your changes were saved"))
            return morepath.redirect(request.link(resource))

    layout = AllocationEditFormLayout(self, request)

    form.apply_model(self)

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if start and end:
        form.apply_dates(start, end)

    return {
        'layout': layout,
        'title': _("Edit allocation"),
        'form': form
    }


@TownApp.view(model=Allocation, request_method='DELETE', permission=Private)
def handle_delete_allocation(self, request):
    request.assert_valid_csrf_token()

    resources = ResourceCollection(request.app.libres_context)
    scheduler = resources.scheduler_by_id(self.resource)
    scheduler.remove_allocation(id=self.id)
