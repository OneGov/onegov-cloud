from onegov.core.security import Public
from onegov.winterthur import WinterthurApp, _
from onegov.winterthur.layout import RoadworkLayout, RoadworkCollectionLayout
from onegov.winterthur.roadwork import Roadwork, RoadworkCollection


@WinterthurApp.html(
    model=RoadworkCollection,
    permission=Public,
    template='roadworks.pt'
)
def view_roadwork_collection(self, request):

    return {
        'layout': RoadworkCollectionLayout(self, request),
        'title': _("Roadworks"),
        'model': self
    }


@WinterthurApp.html(
    model=Roadwork,
    permission=Public,
    template='roadwork.pt'
)
def view_roadwork(self, request):

    return {
        'layout': RoadworkLayout(self, request),
        'title': self.title,
        'model': self,
        'back': request.class_link(RoadworkCollection)
    }
