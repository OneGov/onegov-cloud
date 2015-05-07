""" The onegov town homepage. """

from collections import namedtuple
from onegov.core.security import Public
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.models import Town
from onegov.town.layout import DefaultLayout


@TownApp.html(model=Town, template='homepage.pt', permission=Public)
def view_town(self, request):
    """ Renders the town's homepage. """

    layout = DefaultLayout(self, request)
    Tile = namedtuple('Tile', ['page', 'links', 'number'])

    tiles = [
        Tile(
            page=Link(page.title, request.link(page)),
            number=ix + 1,
            links=[
                Link(c.title, request.link(c), classes=('tile-sub-link',))
                for c in (page.children[:3] if page.type == 'topic' else [])
            ]
        ) for ix, page in enumerate(layout.root_pages)
    ]

    return {
        'layout': layout,
        'title': self.name,
        'tiles': tiles,
        'news': layout.root_pages[-1].news_query.limit(3).all()
    }
