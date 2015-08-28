import morepath

from itertools import groupby
from libres.db.models import Allocation
from libres.modules.errors import LibresError
from operator import attrgetter
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
    """ Returns the allocations in a fullcalendar compatible events feed.

    See `<http://fullcalendar.io/docs/event_data/events_json_feed/>`_ for
    more information.

    """

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if not (start and end):
        return []

    scheduler = self.get_scheduler(request.app.libres_context)
    queries = scheduler.queries

    # get all allocations (including mirrors), for the availability calculation
    query = scheduler.allocations_in_range(start, end, masters_only=False)
    query = query.order_by(Allocation._start)

    allocations = query.all()

    # put only return the master allocations
    events = []

    for key, group in groupby(allocations, key=attrgetter('_start')):
        grouped = tuple(group)
        availability = queries.availability_by_allocations(grouped)

        for allocation in grouped:
            if allocation.is_master:
                events.append(
                    utils.AllocationEventInfo(
                        allocation,
                        availability,
                        request
                    )
                )

    return [e.as_dict() for e in events]


def get_new_allocation_form_class(resource, request):
    """ Returns the form class for new allocations (different resources have
    different allocation forms).

    """

    if resource.type == 'daypass':
        return DaypassAllocationForm

    if resource.type == 'room':
        return RoomAllocationForm

    raise NotImplementedError


def get_edit_allocation_form_class(allocation, request):
    """ Returns the form class for existing allocations (different resources
    have different allocation forms).

    """

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
    """ Handles new allocations for differing form classes. """

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

            self.highlight_allocations(allocations)
            return morepath.redirect(request.link(self))
    elif not request.POST:
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

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("New allocation"), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _("New allocation"),
        'form': form
    }


@TownApp.form(model=Allocation, template='form.pt', name='bearbeiten',
              permission=Private, form=get_edit_allocation_form_class)
def handle_edit_allocation(self, request, form):
    """ Handles edit allocation for differing form classes. """

    resources = ResourceCollection(request.app.libres_context)
    resource = resources.by_id(self.resource)

    if form.submitted(request):
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
            resource.highlight_allocations([self])
            return morepath.redirect(request.link(resource))
    elif not request.POST:
        form.apply_model(self)

        start, end = utils.parse_fullcalendar_request(request, self.timezone)
        if start and end:
            form.apply_dates(start, end)

    return {
        'layout': AllocationEditFormLayout(self, request),
        'title': _("Edit allocation"),
        'form': form
    }


@TownApp.view(model=Allocation, request_method='DELETE', permission=Private)
def handle_delete_allocation(self, request):
    """ Deletes the given resource (throwing an error if there are existing
    reservations associated with it).

    """
    request.assert_valid_csrf_token()

    resources = ResourceCollection(request.app.libres_context)
    scheduler = resources.scheduler_by_id(self.resource)
    scheduler.remove_allocation(id=self.id)
