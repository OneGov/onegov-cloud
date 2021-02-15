from collections import namedtuple
from onegov.event import OccurrenceCollection
from onegov.org.elements import Link, LinkGroup
from onegov.org.layout import EventBaseLayout

from onegov.org.homepage_widgets.widgets import NewsWidget as OrgNewsWidget

from onegov.town6 import TownApp
from onegov.town6 import _


def get_lead(text, max_chars=180, consider_sentences=True):
    if len(text) > max_chars:
        first_point_ix = text.find('.')
        if not first_point_ix or not consider_sentences:
            return text[0:max_chars] + '...'
        elif first_point_ix >= max_chars:
            return text
        else:
            end = text[0:max_chars].rindex('.') + 1
            return text[0:end]

    return text


@TownApp.homepage_widget(tag='row')
class RowWidget(object):
    template = """
        <xsl:template match="row">
            <div class="grid-container">
                <div class="grid-x grid-padding-x">
                    <xsl:apply-templates select="node()"/>
                </div>
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='row-wide')
class RowWidget(object):
    template = """
        <xsl:template match="row-wide">
            <div class="grid-container full">
                <div class="grid-x">
                    <xsl:apply-templates select="node()"/>
                </div>
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='column')
class ColumnWidget(object):
    template = """
        <xsl:template match="column">
            <div class="small-12 medium-{@span} cell">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='links')
class LinksWidget(object):
    template = """
        <xsl:template match="links">
            <xsl:if test="@title">
                <h3>
                    <xsl:value-of select="@title" />
                </h3>
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


@TownApp.homepage_widget(tag='news')
class NewsWidget(OrgNewsWidget):
    template = """
        <xsl:template match="news">
            <div metal:use-macro="layout.macros.newslist"
                tal:define="heading 'h5'; show_all_news_link True;
                hide_date True"
            />
        </xsl:template>
    """


@TownApp.homepage_widget(tag='homepage-cover')
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


EventCard = namedtuple(
    'EventCard', ['text', 'url', 'subtitle', 'image_url', 'location', 'lead']
)


@TownApp.homepage_widget(tag='events')
class EventsWidget(object):
    template = """
        <xsl:template match="events">
            <metal:block use-macro="layout.macros['event-cards']"
            tal:define="with_lead True" />
        </xsl:template>
    """

    def get_variables(self, layout):
        occurrences = OccurrenceCollection(layout.app.session()).query()
        occurrences = occurrences.limit(4)

        event_layout = EventBaseLayout(layout.model, layout.request)
        event_links = [
            EventCard(
                text=o.title,
                url=layout.request.link(o),
                subtitle=event_layout.format_date(o.localized_start, 'event')
                .title(),
                image_url=o.event.image and layout.request.link(o.event.image),
                location=o.location,
                lead=get_lead(o.event.description)
            ) for o in occurrences
        ]

        latest_events = LinkGroup(
            title=_("Events"),
            links=event_links,
        )

        return {
            'event_panel': latest_events,
            'all_events_link': Link(
                text=_("All events"),
                url=event_layout.events_url,
                classes=('more-link', )
            ),

        }


PartnerCard = namedtuple('PartnerCard', ['url', 'image_url', 'lead'])


@TownApp.homepage_widget(tag='partners')
class PartnerWidget(object):

    template = """
            <xsl:template match="partners">
                <metal:block use-macro="layout.macros['partner-cards']" />
            </xsl:template>
    """

    def get_variables(self, layout):
        org = layout.org
        partner_attrs = [key for key in dir(org) if 'partner' in key]
        partner_count = int(len(partner_attrs) / 3)

        return {'partners': [
            PartnerCard(
                url=getattr(org, f'partner_{ix}_url'),
                image_url=getattr(org, f'partner_{ix}_img'),
                lead=getattr(org, f'partner_{ix}_name'),
            ) for ix in range(1, partner_count + 1)
        ]}
