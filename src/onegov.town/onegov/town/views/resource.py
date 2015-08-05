import morepath

from libres.db.models import Allocation
from onegov.core.security import Public, Private
from onegov.libres import ResourceCollection
from onegov.libres.models import Resource
from onegov.town import TownApp, _, utils
from onegov.town.elements import Link
from onegov.town.forms import ResourceForm
from onegov.town.models.resource import DaypassResource, RoomResource
from onegov.town.layout import ResourcesLayout, ResourceLayout
from onegov.town.forms import DaypassAllocationForm, RoomAllocationForm
from webob import exc


RESOURCE_TYPES = {
    'daypass': {
        'success': _("Added a new daypass"),
        'title': _("New daypass"),
        'class': DaypassResource
    },
    'room': {
        'success': _("Added a new room"),
        'title': _("New room"),
        'class': RoomResource
    }
}


def get_daypass_form(self, request):
    return get_resource_form(self, request, 'daypass')


def get_room_form(self, request):
    return get_resource_form(self, request, 'room')


def get_resource_form(self, request, type=None):
    if isinstance(self, ResourceCollection):
        assert type is not None
        model = RESOURCE_TYPES[type]['class']()
    else:
        model = self

    return model.with_content_extensions(ResourceForm, request)


@TownApp.html(model=ResourceCollection, template='resources.pt',
              permission=Public)
def view_resources(self, request):
    return {
        'title': _("Reservations"),
        'resources': self.query().order_by(Resource.title).all(),
        'layout': ResourcesLayout(self, request)
    }


@TownApp.form(model=ResourceCollection, name='neuer-raum',
              template='form.pt', permission=Private, form=get_room_form)
def handle_new_room(self, request, form):
    return handle_new_resource(self, request, form, 'room')


@TownApp.form(model=ResourceCollection, name='neue-tageskarte',
              template='form.pt', permission=Private, form=get_daypass_form)
def handle_new_daypass(self, request, form):
    return handle_new_resource(self, request, form, 'daypass')


def handle_new_resource(self, request, form, type):
    if form.submitted(request):

        resource = self.add(
            title=form.title.data, type=type, timezone='Europe/Zurich'
        )
        form.update_model(resource)

        request.success(RESOURCE_TYPES[type]['success'])
        return morepath.redirect(request.link(resource))

    layout = ResourcesLayout(self, request)
    layout.include_editor()
    layout.breadcrumbs.append(Link(RESOURCE_TYPES[type]['title'], '#'))

    return {
        'layout': layout,
        'title': _(RESOURCE_TYPES[type]['title']),
        'form': form,
        'form_width': 'large'
    }


@TownApp.form(model=Resource, name='bearbeiten', template='form.pt',
              permission=Private, form=get_resource_form)
def handle_edit_resource(self, request, form):
    if form.submitted(request):
        form.update_model(self)

        request.success(_(u"Your changes were saved"))
        return morepath.redirect(request.link(self))

    form.apply_model(self)

    layout = ResourceLayout(self, request)
    layout.include_editor()
    layout.breadcrumbs.append(Link(_("Edit"), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


@TownApp.html(model=Resource, template='resource.pt', permission=Public)
def view_resource(self, request):
    return {
        'title': self.title,
        'resource': self,
        'layout': ResourceLayout(self, request),
        'feed': request.link(self, name='slots')
    }


@TownApp.view(model=Resource, request_method='DELETE', permission=Private)
def handle_delete_resource(self, request):

    if not self.deletable(request.app.libres_context):
        raise exc.HTTPMethodNotAllowed()

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(self, including_reservations=False)


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


def get_allocation_form_class(resource, request):
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
