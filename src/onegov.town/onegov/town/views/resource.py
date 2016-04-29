import morepath

from collections import OrderedDict
from itertools import groupby
from onegov.core.security import Public, Private
from onegov.libres import ResourceCollection
from onegov.libres.models import Resource
from onegov.town import TownApp, _
from onegov.town import utils
from onegov.town.elements import Link
from onegov.town.forms import ResourceForm, ResourceCleanupForm
from onegov.town.layout import ResourcesLayout, ResourceLayout
from onegov.town.models.resource import DaypassResource, RoomResource
from sqlalchemy.sql.expression import nullsfirst
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
    resources = self.query().order_by(nullsfirst(Resource.group)).all()
    resources = request.exclude_invisible(resources)
    grouped = OrderedDict()

    for group, items in groupby(resources, lambda r: r.group or _("General")):
        grouped[group] = sorted(tuple(items), key=lambda r: r.title)

    if len(grouped) == 1:
        grouped = {None: tuple(grouped.values())[0]}

    return {
        'title': _("Reservations"),
        'resources': grouped,
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
        form.populate_obj(resource)

        request.success(RESOURCE_TYPES[type]['success'])
        return morepath.redirect(request.link(resource))

    layout = ResourcesLayout(self, request)
    layout.include_editor()
    layout.include_code_editor()
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
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = ResourceLayout(self, request)
    layout.include_editor()
    layout.include_code_editor()
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

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(self, including_reservations=False)


@TownApp.form(model=Resource, permission=Private, name='cleanup',
              form=ResourceCleanupForm, template='resource_cleanup.pt')
def handle_cleanup_allocations(self, request, form):
    """ Removes all unused allocations between the given dates. """

    if form.submitted(request):
        start, end = form.data['start'], form.data['end']

        scheduler = self.get_scheduler(request.app.libres_context)
        count = scheduler.remove_unused_allocations(start, end)

        request.success(
            _("Successfully removed ${count} unused allocations", mapping={
                'count': count
            })
        )

        return morepath.redirect(request.link(self))

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Clean up"), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _("Clean up"),
        'form': form
    }


@TownApp.json(model=Resource, name='reservations', permission=Public)
def get_reservations(self, request):
    return [
        utils.ReservationInfo(reservation, request).as_dict() for reservation
        in self.bound_reservations(request)
    ]
