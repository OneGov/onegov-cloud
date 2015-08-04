from onegov.core.security import Public
from onegov.libres.models import Resource
from onegov.town import TownApp
from onegov.town.layout import ResourceLayout


@TownApp.html(model=Resource, template='resource.pt', permission=Public)
def view_resource(self, request):
    return {
        'title': self.title,
        'resource': self,
        'layout': ResourceLayout(self, request)
    }
