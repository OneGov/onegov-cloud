import morepath

from libres.db.models import Allocation
from libres.modules.errors import LibresError
from onegov.core.security import Public, Private
from onegov.libres import Resource, ResourceCollection
from onegov.org import OrgApp, utils, _
from onegov.org.elements import Link
from onegov.org.forms import (
    DaypassAllocationForm,
    DaypassAllocationEditForm,
    RoomAllocationForm,
    RoomAllocationEditForm
)
from onegov.org.layout import ResourceLayout, AllocationEditFormLayout
from purl import URL


@OrgApp.json(model=Resource, name='slots', permission=Public)
def view_allocations_json(self, request):
    """ Returns the allocations in a fullcalendar compatible events feed.

    See `<http://fullcalendar.io/docs/event_data/events_json_feed/>`_ for
    more information.

    """

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if not (start and end):
        return []

    # get all allocations (including mirrors), for the availability calculation
    query = self.scheduler.allocations_in_range(start, end, masters_only=False)
    query = query.order_by(Allocation._start)

    allocations = query.all()

    # but only return the master allocations
    return [
        e.as_dict() for e in utils.AllocationEventInfo.from_allocations(
            request, self.scheduler, allocations
        )
    ]


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


@OrgApp.form(model=Resource, template='form.pt', name='neue-einteilung',
             permission=Private, form=get_new_allocation_form_class)
def handle_new_allocation(self, request, form):
    """ Handles new allocations for differing form classes. """

    if form.submitted(request):
        try:
            allocations = self.scheduler.allocate(
                dates=form.dates,
                whole_day=form.whole_day,
                quota=form.quota,
                quota_limit=form.quota_limit,
                data=form.data,
                partly_available=form.partly_available
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
                    form.start_time.data = start
                    form.end_time.data = end

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("New allocation"), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _("New allocation"),
        'form': form
    }


@OrgApp.form(model=Allocation, template='form.pt', name='bearbeiten',
             permission=Private, form=get_edit_allocation_form_class)
def handle_edit_allocation(self, request, form):
    """ Handles edit allocation for differing form classes. """

    resources = ResourceCollection(request.app.libres_context)
    resource = resources.by_id(self.resource)

    # this is a bit of a hack to keep the current view when a user drags an
    # allocation around, which opens this form and later leads back to the
    # calendar - if the user does this on the day view we want to return to
    # the same day view after the process
    # therefore we set the view on the resource (where this is okay) and on
    # the form action (where it's a bit of a hack), to ensure that the view
    # parameter is around for the whole time
    if 'view' in request.params:
        resource.view = view = request.params['view']
        form.action = URL(form.action).query_param('view', view).as_string()

    if form.submitted(request):
        new_start, new_end = form.dates

        try:
            resource.scheduler.move_allocation(
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


@OrgApp.view(model=Allocation, request_method='DELETE', permission=Private)
def handle_delete_allocation(self, request):
    """ Deletes the given resource (throwing an error if there are existing
    reservations associated with it).

    """
    request.assert_valid_csrf_token()

    resource = request.app.libres_resources.by_allocation(self)
    resource.scheduler.remove_allocation(id=self.id)

    @request.after
    def trigger_calendar_update(response):
        response.headers.add('X-IC-Trigger', 'rc-allocations-changed')
