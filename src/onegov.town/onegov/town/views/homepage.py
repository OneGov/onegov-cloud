""" The onegov town homepage. """

from collections import namedtuple
from onegov.event import OccurrenceCollection
from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.newsletter import NewsletterCollection
from onegov.people import PersonCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link, LinkGroup
from onegov.town.layout import DefaultLayout, EventBaseLayout
from onegov.town.models import AtoZPages, Town


@TownApp.html(model=Town, template='homepage.pt', permission=Public)
def view_town(self, request):
    """ Renders the town's homepage. """

    session = request.app.session()
    libres_context = request.app.libres_context
    layout = DefaultLayout(self, request)

    Tile = namedtuple('Tile', ['page', 'links', 'number'])

    news_query = layout.root_pages[-1].news_query
    classes = ('tile-sub-link', )

    tiles = []
    homepage_pages = request.app.homepage_pages
    for ix, page in enumerate(layout.root_pages):
        if page.type == 'topic':
            children = homepage_pages.get(page.id, tuple())
            children = (session.merge(c, load=False) for c in children)

            if not request.is_logged_in:
                children = (c for c in children if not c.is_hidden_from_public)

            tiles.append(Tile(
                page=Link(page.title, request.link(page)),
                number=ix + 1,
                links=[
                    Link(c.title, request.link(c), classes=classes, model=c)
                    for c in children
                ]
            ))
        elif page.type == 'news':
            news_url = request.link(page)
            years = (str(year) for year in page.years)

            links = [
                Link(year, news_url + '?year=' + year, classes=classes)
                for year in years
            ]

            links.append(Link(
                _("Newsletter"), request.link(NewsletterCollection(session)),
                classes=classes
            ))

            tiles.append(Tile(
                page=Link(page.title, news_url),
                number=ix + 1,
                links=links
            ))
        else:
            raise NotImplementedError

    # the panels on the homepage are currently mostly place-holders, real
    # links as well as translatable text is added every time we implement
    # a new feature that we need to link up on the homepage
    online_counter_links = [
        Link(
            text=_("Online Counter"),
            url=request.link(FormCollection(session)),
            subtitle=(
                self.meta.get('online_counter_label') or
                _("Forms and applications")
            )
        ),
        Link(
            text=_("Reservations"),
            url=request.link(ResourceCollection(libres_context)),
            subtitle=(
                self.meta.get('reservations_label') or
                _("Daypasses and rooms")
            )
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
                subtitle=(
                    self.meta.get('sbb_daypass_label') or
                    _("Generalabonnement for Towns")
                )
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
                url=request.link(AtoZPages(request)),
                subtitle=_("Catalog A-Z")
            ),
        ]
    )

    return {
        'layout': layout,
        'title': self.name,
        'tiles': tiles,
        'news': request.exclude_invisible(news_query.limit(2).all(),),
        'news_url': news_url,
        'panels': [
            online_counter,
            latest_events,
            directories
        ]
    }
