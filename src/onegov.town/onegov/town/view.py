""" Contains the view handling code for onegov.town.

This will be moved to a subfolder in the future as more views are amassed.

"""

from onegov.core.security import Public
from onegov.town.app import TownApp
from onegov.town.model import Town


@TownApp.html(model=Town, template='town.pt', permission=Public)
def view_town(self, request):
    return {
        'title': self.name
    }
