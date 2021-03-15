from onegov.core.security import Public, Private

from onegov.org.views.resource import view_resources, get_room_form, \
    get_daypass_form, handle_new_room, handle_new_daypass, \
    get_resource_form, handle_edit_resource, view_resource, \
    handle_cleanup_allocations, view_occupancy, \
    view_resource_subscribe, view_export
from onegov.reservation import ResourceCollection, Resource
from onegov.town6 import TownApp
from onegov.org.forms import ResourceCleanupForm, ResourceExportForm
from onegov.town6.layout import ResourcesLayout, ResourceLayout


@TownApp.html(model=ResourceCollection, template='resources.pt',
              permission=Public)
def town_view_resources(self, request):
    return view_resources(self, request, ResourcesLayout(self, request))


@TownApp.form(model=ResourceCollection, name='new-room',
              template='form.pt', permission=Private, form=get_room_form)
def town_handle_new_room(self, request, form):
    return handle_new_room(self, request, form, ResourcesLayout(self, request))


@TownApp.form(model=ResourceCollection, name='new-daypass',
              template='form.pt', permission=Private, form=get_daypass_form)
def town_handle_new_daypass(self, request, form):
    return handle_new_daypass(
        self, request, form, ResourcesLayout(self, request))


@TownApp.form(model=Resource, name='edit', template='form.pt',
              permission=Private, form=get_resource_form)
def town_handle_edit_resource(self, request, form):
    return handle_edit_resource(
        self, request, form, ResourceLayout(self, request))


@TownApp.html(model=Resource, template='resource.pt', permission=Public)
def town_view_resource(self, request):
    return view_resource(self, request, ResourceLayout(self, request))


@TownApp.form(model=Resource, permission=Private, name='cleanup',
              form=ResourceCleanupForm, template='resource_cleanup.pt')
def town_handle_cleanup_allocations(self, request, form):
    return handle_cleanup_allocations(
        self, request, form, ResourceLayout(self, request))


@TownApp.html(model=Resource, permission=Private, name='occupancy',
              template='resource_occupancy.pt')
def town_view_occupancy(self, request):
    return view_occupancy(self, request, ResourceLayout(self, request))


@TownApp.html(model=Resource, template='resource-subscribe.pt',
              permission=Private, name='subscribe')
def town_view_resource_subscribe(self, request):
    return view_resource_subscribe(
        self, request, ResourceLayout(self, request))


@TownApp.form(model=Resource, permission=Private, name='export',
              template='export.pt', form=ResourceExportForm)
def town_view_export(self, request, form):
    return view_export(self, request, form, ResourceLayout(self, request))
