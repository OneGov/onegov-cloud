# -*- coding: utf-8 -*-

""" The onegov town homepage. """

from collections import namedtuple
from onegov.event import OccurrenceCollection
from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.page import PageCollection, Page
from onegov.people import PersonCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link, LinkGroup
from onegov.town.layout import DefaultLayout, EventBaseLayout
from onegov.town.models import Town


@TownApp.html(model=Town, template='homepage.pt', permission=Public)
def view_town(self, request):
    """ Renders the town's homepage. """

    session = request.app.session()
    libres_context = request.app.libres_context
    layout = DefaultLayout(self, request)

    Tile = namedtuple('Tile', ['page', 'links', 'number'])

    pages = PageCollection(session)
    children_query = pages.query().order_by(Page.title)

    tiles = []
    for ix, page in enumerate(layout.root_pages):

        if page.type == 'topic':
            children = children_query.filter(Page.parent_id == page.id)
            children = children.limit(3).all()
        else:
            children = tuple()

        tiles.append(Tile(
            page=Link(page.title, request.link(page)),
            number=ix + 1,
            links=[
                Link(c.title, request.link(c), classes=('tile-sub-link',))
                for c in children
            ]
        ))

    # the panels on the homepage are currently mostly place-holders, real
    # links as well as translatable text is added every time we implement
    # a new feature that we need to link up on the homepage
    online_counter_links = [
        Link(
            text=_("Online Counter"),
            url=request.link(FormCollection(session)),
            subtitle=_("Forms and applications")
        ),
        Link(
            text=_("Reservations"),
            url=request.link(ResourceCollection(libres_context)),
            subtitle=_("Daypasses and rooms")
        ),
    ]

    # ga-tageskarte is the legacy name..
    sbb = ResourceCollection(libres_context).by_name('sbb-tageskarte')
    sbb = sbb or ResourceCollection(libres_context).by_name('ga-tageskarte')

    if sbb:
        online_counter_links.append(
            Link(
                text=_("SBB Daypass"),
                url=request.link(sbb),
                subtitle=_("Generalabonnement for Towns")
            )
        )

    online_counter = LinkGroup(
        title=_("Services"),
        links=online_counter_links
    )

    event_layout = EventBaseLayout(self, request)
    occurrences = OccurrenceCollection(session).query().limit(4)
    event_links = [
        Link(
            text=occurrence.title,
            url=request.link(occurrence),
            subtitle=event_layout.format_date(occurrence.localized_start,
                                              'event')
        )
        for occurrence in occurrences
    ]
    event_links.append(
        Link(
            text=_("All events"),
            url=event_layout.events_url,
            classes=('more-link', )
        )
    )

    latest_events = LinkGroup(
        title=_("Events"),
        links=event_links,
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
            layout.root_pages[-1].news_query.limit(2).all(),
        ),
        'panels': [
            online_counter,
            latest_events,
            directories
        ]
    }
