from __future__ import annotations

from onegov.core.security import Public
from onegov.winterthur import WinterthurApp, _
from onegov.winterthur.layout import RoadworkLayout, RoadworkCollectionLayout
from onegov.winterthur.roadwork import Roadwork, RoadworkCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.winterthur.request import WinterthurRequest


@WinterthurApp.html(
    model=RoadworkCollection,
    permission=Public,
    template='roadworks.pt'
)
def view_roadwork_collection(
    self: RoadworkCollection,
    request: WinterthurRequest
) -> RenderData:

    return {
        'layout': RoadworkCollectionLayout(self, request),
        'title': _('Roadworks'),
        'model': self
    }


@WinterthurApp.html(
    model=Roadwork,
    permission=Public,
    template='roadwork.pt'
)
def view_roadwork(
    self: Roadwork,
    request: WinterthurRequest
) -> RenderData:

    return {
        'layout': RoadworkLayout(self, request),
        'title': self.title,
        'model': self,
        'back': request.class_link(RoadworkCollection)
    }
