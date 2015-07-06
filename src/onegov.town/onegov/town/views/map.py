# -*- coding: utf-8 -*-

""" Shows a point on a map. """

from onegov.core.security import Public
from onegov.town.app import TownApp
from onegov.town.layout import MapLayout
from onegov.town.models import Map


@TownApp.html(model=Map, template='map.pt', permission=Public)
def view_map(self, request):
    return {
        'layout': MapLayout(self, request),
        'map': self
    }
