from __future__ import annotations

from onegov.core.security import Public, Private, Personal
from onegov.org.forms.resource import AllResourcesExportForm

from onegov.org.views.resource import (
    view_resources, view_find_your_spot, get_room_form,
    get_daypass_form, handle_new_room, handle_new_daypass,
    get_resource_form, handle_edit_resource, view_resource,
    handle_cleanup_allocations, view_occupancy,
    view_resource_subscribe, view_export_all, get_item_form,
    handle_new_resource_item, view_export, view_my_reservations,
    view_my_reservations_subscribe
)
from onegov.reservation import ResourceCollection, Resource
from onegov.org.forms import (
    FindYourSpotForm, ResourceCleanupForm, ResourceExportForm
)
from onegov.org.models.resource import FindYourSpotCollection
from onegov.town6 import TownApp
from onegov.town6.layout import (
    DefaultLayout, FindYourSpotLayout, ResourcesLayout, ResourceLayout
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import ResourceForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=ResourceCollection,
    template='resources.pt',
    permission=Public
)
def town_view_resources(
    self: ResourceCollection,
    request: TownRequest
) -> RenderData:
    return view_resources(self, request, ResourcesLayout(self, request))


@TownApp.form(
    model=FindYourSpotCollection,
    template='find_your_spot.pt',
    permission=Public,
    form=FindYourSpotForm
)
def town_view_find_your_spot(
    self: FindYourSpotCollection,
    request: TownRequest,
    form: FindYourSpotForm
) -> RenderData:
    return view_find_your_spot(
        self, request, form, FindYourSpotLayout(self, request))


@TownApp.form(
    model=ResourceCollection,
    name='new-room',
    template='form.pt',
    permission=Private,
    form=get_room_form
)
def town_handle_new_room(
    self: ResourceCollection,
    request: TownRequest,
    form: ResourceForm
) -> RenderData | Response:
    return handle_new_room(self, request, form, ResourcesLayout(self, request))


@TownApp.form(
    model=ResourceCollection,
    name='new-daypass',
    template='form.pt',
    permission=Private,
    form=get_daypass_form
)
def town_handle_new_daypass(
    self: ResourceCollection,
    request: TownRequest,
    form: ResourceForm
) -> RenderData | Response:
    return handle_new_daypass(
        self, request, form, ResourcesLayout(self, request))


@TownApp.form(
    model=ResourceCollection,
    name='new-daily-item',
    template='form.pt',
    permission=Private,
    form=get_item_form
)
def town_handle_new_resource_item(
    self: ResourceCollection,
    request: TownRequest,
    form: ResourceForm
) -> RenderData | Response:
    return handle_new_resource_item(
        self, request, form, ResourcesLayout(self, request))


@TownApp.form(
    model=Resource,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_resource_form
)
def town_handle_edit_resource(
    self: Resource,
    request: TownRequest,
    form: ResourceForm
) -> RenderData | Response:
    return handle_edit_resource(
        self, request, form, ResourceLayout(self, request))


@TownApp.html(model=Resource, template='resource.pt', permission=Public)
def town_view_resource(self: Resource, request: TownRequest) -> RenderData:
    return view_resource(self, request, ResourceLayout(self, request))


@TownApp.form(
    model=Resource,
    permission=Private,
    name='cleanup',
    form=ResourceCleanupForm,
    template='resource_cleanup.pt'
)
def town_handle_cleanup_allocations(
    self: Resource,
    request: TownRequest,
    form: ResourceCleanupForm
) -> RenderData | Response:
    return handle_cleanup_allocations(
        self, request, form, ResourceLayout(self, request))


@TownApp.html(
    model=Resource,
    permission=Personal,
    name='occupancy',
    template='resource_occupancy.pt'
)
def town_view_occupancy(
    self: Resource,
    request: TownRequest
) -> RenderData:
    return view_occupancy(self, request, ResourceLayout(self, request))


@TownApp.html(
    model=ResourceCollection,
    permission=Public,
    name='my-reservations',
    template='resource_occupancy.pt'
)
def town_view_my_reservations(
    self: ResourceCollection,
    request: TownRequest
) -> RenderData:
    return view_my_reservations(self, request, DefaultLayout(self, request))


@TownApp.html(
    model=ResourceCollection,
    template='resource-subscribe.pt',
    permission=Public,
    name='my-reservations-subscribe'
)
def town_view_my_reservations_subscribe(
    self: ResourceCollection,
    request: TownRequest
) -> RenderData:
    return view_my_reservations_subscribe(
        self, request, DefaultLayout(self, request))


@TownApp.html(
    model=Resource,
    template='resource-subscribe.pt',
    permission=Private,
    name='subscribe'
)
def town_view_resource_subscribe(
    self: Resource,
    request: TownRequest
) -> RenderData:
    return view_resource_subscribe(
        self, request, ResourceLayout(self, request))


@TownApp.form(
    model=Resource,
    permission=Private,
    name='export',
    template='export.pt',
    form=ResourceExportForm
)
def town_view_export(
    self: Resource,
    request: TownRequest,
    form: ResourceExportForm
) -> RenderData | Response:
    return view_export(self, request, form, ResourceLayout(self, request))


@TownApp.form(
    model=ResourceCollection,
    permission=Private, name='export-all',
    template='export.pt',
    form=AllResourcesExportForm
)
def town_view_export_all(
    self: ResourceCollection,
    request: TownRequest,
    form: AllResourcesExportForm
) -> RenderData | Response:
    return view_export_all(
        self, request, form,
        ResourceLayout(self, request))  # type:ignore[arg-type]
