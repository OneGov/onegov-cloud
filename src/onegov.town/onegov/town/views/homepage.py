# -*- coding: utf-8 -*-

""" The onegov town homepage. """

from collections import namedtuple
from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.people import PersonCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link, LinkGroup
from onegov.town.layout import DefaultLayout
from onegov.town.models import Town


@TownApp.html(model=Town, template='homepage.pt', permission=Public)
def view_town(self, request):
    """ Renders the town's homepage. """

    session = request.app.session()
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

    # the panels on the homepage are currently mostly place-holders, real
    # links as well as translatable text is added every time we implement
    # a new feature that we need to link up on the homepage
    online_counter = LinkGroup(
        title=_("Services"),
        links=[
            Link(
                text=_("Online Counter"),
                url=request.link(FormCollection(session)),
                subtitle=_("Forms and applications")
            ),
            Link(
                text=u"Raumreservationen",
                url="#",
                subtitle=u"Turnhalle und Gesellschaftsräume"
            ),
            Link(
                text=u"GA-Tageskarte",
                url="#",
                subtitle=u"Günstige Tageskarten von der Gemeinde"
            )
        ]
    )

    latest_events = LinkGroup(
        title=u"Veranstaltungen",
        links=[
            Link(
                text=u"Gemeindeversammlung",
                url="#",
                subtitle=u"Montag, 16. März 2015, 19:30"
            ),
            Link(
                text=u"Grümpelturnier",
                url="#",
                subtitle=u"Sonntag, 22. März 2015, 10:00"
            ),
            Link(
                text=u"MuKi Turnen",
                url="#",
                subtitle=u"Freitag, 26. März 2015, 18:30"
            ),
            Link(
                text=u"150 Jahre Govikon",
                url="#",
                subtitle=u"Sonntag, 31. März 2015, 11:00"
            ),
        ]
    )

    directories = LinkGroup(
        title=_("Directories"),
        links=[
            Link(
                text=_("People"),
                url=request.link(PersonCollection(session)),
                subtitle=_("All contacts")
            ),
            Link(
                text=_("Topics"),
                url='#',
                subtitle=_("Catalog A-Z")
            ),
        ]
    )

    return {
        'layout': layout,
        'title': self.name,
        'tiles': tiles,
        'news': request.exclude_invisible(
            layout.root_pages[-1].news_query.limit(3).all(),
        ),
        'panels': [
            online_counter,
            latest_events,
            directories
        ]
    }
