from collections import namedtuple
from onegov.event import OccurrenceCollection
from onegov.newsletter import NewsletterCollection
from onegov.org import _, OrgApp
from onegov.org.elements import Link, LinkGroup
from onegov.org.layout import EventBaseLayout


@OrgApp.homepage_widget(tag='row')
class RowWidget(object):
    template = """
        <xsl:template match="row">
            <div class="row">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='column')
class ColumnWidget(object):
    template = """
        <xsl:template match="column">
            <div class="small-12 medium-{@span} columns">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='panel')
class PanelWidget(object):
    template = """
        <xsl:template match="panel">
            <div class="homepage-panel">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='links')
class LinksWidget(object):
    template = """
        <xsl:template match="links">
            <xsl:if test="@title">
                <h2>
                    <xsl:value-of select="@title" />
                </h2>
            </xsl:if>
            <ul class="panel-links">
                <xsl:for-each select="link">
                <li>
                    <a>
                        <xsl:attribute name="href">
                            <xsl:value-of select="@url" />
                        </xsl:attribute>

                        <xsl:value-of select="node()" />
                    </a>

                    <xsl:if test="@description">
                        <small>
                            <xsl:value-of select="@description" />
                        </small>
                    </xsl:if>
                </li>
                </xsl:for-each>
            </ul>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='news')
class NewsWidget(object):
    template = """
        <xsl:template match="news">
            <div metal:use-macro="layout.macros.newslist"
                tal:define="heading 'h3'; show_all_news_link True"
            />
        </xsl:template>
    """

    def get_variables(self, layout):
        return {
            'news': layout.root_pages[-1].news_query.limit(2).all()
        }


@OrgApp.homepage_widget(tag='homepage-cover')
class CoverWidget(object):
    template = """
        <xsl:template match="homepage-cover">
            <div class="homepage-content page-text">
                <tal:block
                    content="structure layout.org.meta.get('homepage_cover')"
                />
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='events')
class EventsWidget(object):
    template = """
        <xsl:template match="events">
            <metal:block use-macro="layout.macros['events-panel']" />
        </xsl:template>
    """

    def get_variables(self, layout):
        occurrences = OccurrenceCollection(layout.app.session()).query()
        occurrences = occurrences.limit(4)

        event_layout = EventBaseLayout(layout.model, layout.request)
        event_links = [
            Link(
                text=o.title,
                url=layout.request.link(o),
                subtitle=event_layout.format_date(o.localized_start, 'event')
            ) for o in occurrences
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

        return {
            'events_panel': latest_events
        }


@OrgApp.homepage_widget(tag='homepage-tiles')
class TilesWidget(object):
    template = """
        <xsl:template match="homepage-tiles">
            <xsl:choose>
                <xsl:when test="@show-title">
                    <metal:block use-macro="layout.macros['homepage-tiles']"
                       tal:define="show_title True" />
                </xsl:when>
                <xsl:otherwise>
                    <metal:block use-macro="layout.macros['homepage-tiles']"
                      tal:define="show_title False" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:template>
    """

    def get_variables(self, layout):
        return {'tiles': tuple(self.get_tiles(layout))}

    def get_tiles(self, layout):
        Tile = namedtuple('Tile', ['page', 'links', 'number'])

        homepage_pages = layout.request.app.homepage_pages
        request = layout.request
        link = request.link
        session = layout.app.session()
        classes = ('tile-sub-link', )

        for ix, page in enumerate(layout.root_pages):
            if page.type == 'topic':

                children = homepage_pages.get(page.id, tuple())
                children = (session.merge(c, load=False) for c in children)

                if not request.is_manager:
                    children = (
                        c for c in children if not c.is_hidden_from_public
                    )

                yield Tile(
                    page=Link(page.title, link(page)),
                    number=ix + 1,
                    links=tuple(
                        Link(c.title, link(c), classes=classes, model=c)
                        for c in children
                    )
                )
            elif page.type == 'news':
                news_url = link(page)
                years = (str(year) for year in page.years)

                links = [
                    Link(year, news_url + '?year=' + year, classes=classes)
                    for year in years
                ]

                links.append(Link(
                    _("Newsletter"), link(NewsletterCollection(session)),
                    classes=classes
                ))

                yield Tile(
                    page=Link(page.title, news_url),
                    number=ix + 1,
                    links=links
                )
            else:
                raise NotImplementedError
