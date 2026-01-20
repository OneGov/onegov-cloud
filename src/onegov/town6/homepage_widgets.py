from __future__ import annotations

import lxml.etree
import requests
from datetime import datetime

from onegov.event import OccurrenceCollection
from onegov.form import FormCollection
from onegov.org.elements import Link, LinkGroup

from onegov.org.homepage_widgets import (
    NewsWidget as OrgNewsWidget,
    DirectoriesWidget as OrgDirectoriesWidget,
    get_lead)
from onegov.org.models import PublicationCollection
from onegov.people import PersonCollection
from onegov.reservation import ResourceCollection

from onegov.town6 import TownApp
from onegov.town6 import _


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from lxml.etree import _Element
    from onegov.core.types import RenderData
    from onegov.town6.layout import DefaultLayout


@TownApp.homepage_widget(tag='row')
class RowWidget:
    template = """
        <xsl:template match="row">
            <div class="grid-container">
                <div class="grid-x grid-padding-x {@class}">
                    <xsl:apply-templates select="node()"/>
                </div>
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='row-wide')
class RowWidgetWide:
    template = """
        <xsl:template match="row-wide">
            <div class="grid-container full {@bgcolor}">
                <div class="grid-x {@class}">
                    <xsl:apply-templates select="node()"/>
                </div>
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='column')
class ColumnWidget:
    template = """
        <xsl:template match="column">
            <div class="small-12 medium-{@span} cell">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='title')
class TitleWidget:
    template = """
        <xsl:template match="title">
            <h3 class="{@class}">
                <xsl:apply-templates select="node()"/>
            </h3>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='autoplay_video')
class AutoplayVideoWidget:
    template = """
        <xsl:template match="autoplay_video">
            <div metal:use-macro="layout.macros.autoplay_video"
            tal:define="max_height '{@max-height}'; link_mp4 '{@link_mp4}';
            link_mp4_low_res '{@link_mp4_low_res}';
            link_webm '{@link_webm}'; button_url '{@button_url}';
            link_webm_low_res '{@link_webm_low_res}'; text '{@text}';
            button_text '{@button_text}';
            "
            />
        </xsl:template>
    """


@TownApp.homepage_widget(tag='random_videos')
class RandomVideosWidget:
    template = """
        <xsl:template match="random_videos">
            <div id="random-video">
                <xsl:apply-templates select="node()" />
            </div>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='icon_link')
class IconLinksWidget:
    template = """
        <xsl:template match="icon_link">
            <div metal:use-macro="layout.macros.icon_link"
            tal:define="
                title '{@title}'; invert '{@invert}'; icon '{@icon}';
                text '{@text}'; link '{@link}';
            "
            />
        </xsl:template>
    """


@TownApp.homepage_widget(tag='text')
class TextWidget:
    template = """
        <xsl:template match="text">
            <p class="homepage-text">
                <xsl:apply-templates select="node()"/>
            </p>
        </xsl:template>
    """


@TownApp.homepage_widget(tag='links')
class LinksWidget:
    template = """
        <xsl:template match="links">
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
    news_limit = 3
    template = """
        <xsl:template match="news">
            <div metal:use-macro="layout.macros.newslist"
                tal:define="heading 'h5'; show_all_news_link True;
                hide_date False"
            />
        </xsl:template>
    """


class EventCard(NamedTuple):
    text: str
    url: str
    subtitle: str
    image_url: str | None
    location: str | None
    lead: str


@TownApp.homepage_widget(tag='events')
class EventsWidget:
    template = """
        <xsl:template match="events">
            <metal:block use-macro="layout.macros['event-cards']"
            tal:define="with_lead True" />
        </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        occurrences = OccurrenceCollection(layout.app.session()).query()
        occurrences = occurrences.limit(layout.org.event_limit_homepage)

        event_links = [
            EventCard(
                text=o.title,
                url=layout.request.link(o),
                subtitle=(
                    layout.format_date(
                        o.localized_start, 'event_short').title() + ', '
                    + layout.format_time_range(
                        o.localized_start, o.localized_end).title()),
                image_url=(
                    layout.request.link(o.event.image)
                    if o.event.image else None
                ),
                location=o.location,
                lead=get_lead(o.event.title)
            ) for o in occurrences
        ]

        latest_events = LinkGroup(
            title=_('Events'),
            links=event_links,  # type:ignore[arg-type]
        ) if event_links else None

        return {
            'event_panel': latest_events,
            'all_events_link': Link(
                text=_('All events'),
                url=layout.events_url,
                classes=('more-link', )
            ),

        }


@TownApp.homepage_widget(tag='partners')
class PartnerWidget:

    template = """
        <xsl:template match="partners">
            <xsl:variable name="apos">'</xsl:variable>
            <xsl:variable name="show_title">
                <xsl:choose>
                     <xsl:when test="@hide-title">
                        <xsl:value-of
                        select="'False'" />
                    </xsl:when>
                     <xsl:otherwise>
                        <xsl:value-of select="'True'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <metal:block use-macro="layout.macros['partner-cards']">
            <xsl:attribute name="tal:define">
            <xsl:value-of
            select="concat(
                'title ',
                $apos,
                @title,
                $apos,
                '; ',
                'show_title ',
                $show_title,
                ';')" />
          </xsl:attribute>
            </metal:block>
        </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        return {'partners': layout.partners}


@TownApp.homepage_widget(tag='services')
class ServicesWidget:
    template = """
        <xsl:template match="services">
            <div class="services-panel">
                <ul class="panel-links callout">
                    <li tal:repeat="link services_panel.links">
                        <tal:b content="structure link(layout)" />
                    </li>
                    <xsl:for-each select="link">
                        <li tal:define="icon '{@icon}'">
                            <a tal:attributes="
                                class ('h5 fa fa-' + icon) if icon
                                      else 'generic h5'
                                ">
                                <xsl:attribute name="href">
                                    <xsl:value-of select="@url" />
                                </xsl:attribute>
                                <xsl:value-of select="node()" />
                            </a>
                        </li>
                    </xsl:for-each>
                </ul>
            </div>
        </xsl:template>
    """

    def get_service_links(self, layout: DefaultLayout) -> Iterator[Link]:
        if not layout.org.hide_online_counter:
            yield Link(
                text=_('Online Counter'),
                url=layout.request.class_link(FormCollection),
                subtitle=(
                    layout.org.meta.get('online_counter_label')
                    or _('Forms and applications')
                ),
                classes=('online-counter', 'h5')
            )

        # only if there are publications, will we enable the link to them
        if not layout.org.hide_publications and layout.app.publications_count:
            yield Link(
                text=_('Publications'),
                url=layout.request.class_link(PublicationCollection),
                subtitle=_(
                    layout.org.meta.get('publications_label')
                    or _('Official Documents')
                ),
                classes=('publications', 'h5')
            )

        if not layout.org.hide_reservations:
            yield Link(
                text=_('Reservations'),
                url=layout.request.class_link(ResourceCollection),
                subtitle=(
                    layout.org.meta.get('reservations_label')
                    or _('Daypasses and rooms')
                ),
                classes=('reservations', 'h5')
            )

        if move_url := layout.org.meta.get('e_move_url'):
            yield Link(
                text=_('E-Move'),
                url=move_url,
                subtitle=(
                    layout.org.meta.get('e_move_label')
                    or _('Move with eMovingCH')
                ),
                classes=('e-move', 'h5')
            )

        resources = ResourceCollection(layout.app.libres_context)

        # ga-tageskarte is the legacy name
        sbb_daypass = (
            resources.by_name('sbb-tageskarte')
            or resources.by_name('ga-tageskarte')
        )

        if sbb_daypass:
            yield Link(
                text=_('SBB Daypass'),
                url=layout.request.link(sbb_daypass),
                subtitle=(
                    layout.org.meta.get('daypass_label')
                    or _('Generalabonnement for Towns')
                ),
                classes=('sbb-daypass', 'h5')
            )

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        return {
            'services_panel': LinkGroup(_('Services'), links=tuple(
                self.get_service_links(layout)
            ))
        }


@TownApp.homepage_widget(tag='contacts_and_albums')
class ContactsAndAlbumsWidget:

    template = """
           <xsl:template match="contacts_and_albums">
              <div class="contacts-albums-panel">
                <metal:block use-macro="layout.macros['panel-links']"
                   tal:define="panel contacts_and_albums_panel;
                   classes ['more-list']"
                />
              </div>
           </xsl:template>
       """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        request = layout.request

        return {
            'contacts_and_albums_panel': LinkGroup(
                title=_('Contacts'),
                links=[
                    Link(
                        text=_('People'),
                        url=request.class_link(PersonCollection),
                        subtitle=_('All contacts'),
                        classes=('list-link list-title',)
                    )
                ]
            )
        }


@TownApp.homepage_widget(tag='directories')
class DirectoriesWidget(OrgDirectoriesWidget):
    template = """
        <xsl:template match="directories">
            <metal:block use-macro="layout.macros['directories-list']" />
        </xsl:template>
    """


@TownApp.homepage_widget(tag='focus')
class FocusWidget:
    template = """
    <xsl:template match="focus">
        <a href="{@focus-url}" class="focus-link">
            <div class="focus-widget card" data-aos="fade">
                <xsl:if test="@text-on-image = 'True'">
                    <xsl:attribute name="class">focus-widget card only-title
                    </xsl:attribute>
                </xsl:if>
                <xsl:variable name="apos">'</xsl:variable>
                <xsl:variable name="image_src">
                    <xsl:choose>
                            <xsl:when test="@image-src">
                            <xsl:value-of
                            select="concat($apos, @image-src, $apos)" />
                        </xsl:when>
                            <xsl:otherwise>
                            <xsl:value-of select="'None'" />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <metal:block use-macro="layout.macros['focus-panel']"
                tal:define="image_src '{@image-src}'; title '{@title}';
                 text_on_image '{@text-on-image}'; lead '{@lead}';"
                />
                <xsl:choose>
                    <xsl:when test="@text-on-image">
                        <xsl:if test="text">
                            <div class="card-section">
                                <xsl:for-each select="text">
                                    <p class="homepage-text">
                                        <xsl:apply-templates select="node()"/>
                                    </p>
                                </xsl:for-each>
                            </div>
                        </xsl:if>
                    </xsl:when>
                    <xsl:otherwise>
                    <div class="card-section">
                        <h5>
                            <xsl:choose>
                                <xsl:when test="@title">
                                    <xsl:value-of select="@title" />
                                </xsl:when>
                                <xsl:otherwise>
                                    <metal:block
                                    use-macro="layout.macros['focus-title']" />
                                </xsl:otherwise>
                            </xsl:choose>
                        </h5>
                        <xsl:choose>
                            <xsl:when test="@lead">
                                <p><b>
                                    <xsl:value-of select="@lead" />
                                </b></p>
                            </xsl:when>
                            <xsl:otherwise> </xsl:otherwise>
                        </xsl:choose>
                        <xsl:for-each select="text">
                            <p class="homepage-text">
                                <xsl:apply-templates select="node()"/>
                            </p>
                        </xsl:for-each>
                    </div>
                    </xsl:otherwise>
                </xsl:choose>
            </div>
        </a>
    </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        return {}


@TownApp.homepage_widget(tag='testimonial')
class TestimonialsWidget:
    template = """
        <xsl:template match="testimonial">
            <div metal:use-macro="layout.macros.testimonial"
             tal:define="description '{@description}'; quote '{@quote}';
             image '{@image}';
             "
            />
        </xsl:template>
    """


@TownApp.homepage_widget(tag='testimonial_slider')
class TestimonialSliderWidget:
    template = """
        <xsl:template match="testimonial_slider">
            <div metal:use-macro="layout.macros.testimonial_slider"
             tal:define="color '{@color}';
             description_1 '{@description_1}';
             quote_1 '{@quote_1}'; image_1 '{@image_1}';
             description_2 '{@description_2}';
             quote_2 '{@quote_2}'; image_2 '{@image_2}';
             description_3 '{@description_3}';
             quote_3 '{@quote_3}'; image_3 '{@image_3}';
             "
            />
        </xsl:template>
    """


@TownApp.homepage_widget(tag='jobs')
class JobsWidget:

    template = """
    <xsl:template match="jobs">
        <div metal:use-macro="layout.macros['jobs-cards']"
        tal:define="jobs_card_title '{@jobs_card_title}';
        rss_feed '{@rss_feed}';
        "
        />
    </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        def rss_widget_builder(rss_feed_url: str) -> RSSChannel | None:
            """ Builds and caches widget data from the given RSS URL.

            Note that this is called within the <?python> tag in the macro.
            This is done so we can get the ``rss_feed_url`` which itself is a
            dependency to build the actual widget.
            """
            try:
                # FIXME: We may want to consider caching the parsed feed
                #        rather than the raw content, although we would
                #        either need to add a JSON serializer for RSSFeed
                #        or change them to plain dictionaries.
                def get_content() -> bytes | None:
                    response = requests.get(rss_feed_url, timeout=4)
                    if response.status_code == 200:
                        return response.content
                    return None

                content = layout.app.cache.get_or_create(
                    'jobs_rss_feed',
                    creator=get_content,
                    expiration_time=3600,
                    should_cache_fn=bool,
                )
                if content is None:
                    return None

                parsed = parsed_rss(content)
                return parsed
            except Exception:
                return None

        return {'rss_widget_builder': rss_widget_builder}


class RSSItem(NamedTuple):
    """ The elements inside <item> """
    title: str
    description: str
    guid: str
    pubDate: datetime | None  # noqa: N815


class RSSChannel(NamedTuple):
    """ The elements inside <channel> """
    title: str
    link: str
    description: str
    language: str
    copyright: str
    items: Iterator[RSSItem]


def parsed_rss(rss: bytes) -> RSSChannel:

    def parse_date(date_str: str) -> datetime | None:
        try:
            return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            return None

    def get_text(element: _Element | None) -> str:
        return element.text or '' if element is not None else ''

    def extract_channel_info(
        channel: _Element,
    ) -> tuple[str, str, str, str, str]:
        return (  # type:ignore[return-value]
            get_text(channel.find(field))
            for field in RSSChannel._fields
            if field != 'items'
        )

    def extract_items(channel: _Element) -> Iterator[RSSItem]:
        for item in channel.findall('item'):
            yield RSSItem(
                title=get_text(item.find('title')),
                description=get_text(item.find('description')),
                guid=get_text(item.find('guid')),
                pubDate=parse_date(get_text(item.find('pubDate')))
            )

    root = lxml.etree.fromstring(rss)
    channel = root.find('.//channel')
    assert channel is not None

    return RSSChannel(
        *extract_channel_info(channel),
        extract_items(channel)
    )
