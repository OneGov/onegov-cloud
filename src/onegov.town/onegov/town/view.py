""" Contains the view handling code for onegov.town. """

from onegov.core.security import Public
from onegov.town.app import TownApp
from onegov.town.model import Town
from onegov.town.template import TemplateApi


@TownApp.html(model=Town, template='town.pt', permission=Public)
def view_town(self, request):
    return {'api': TemplateApi(self, request)}
