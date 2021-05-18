from collections import namedtuple

from onegov.event import OccurrenceCollection
from onegov.form import FormCollection
from onegov.org.elements import Link, LinkGroup
from onegov.org.layout import EventBaseLayout

from onegov.org.homepage_widgets import NewsWidget as OrgNewsWidget, \
    get_lead, DirectoriesWidget as OrgDirectoriesWidget
from onegov.org.models import PublicationCollection
from onegov.people import PersonCollection
from onegov.reservation import ResourceCollection

from onegov.town6 import TownApp
from onegov.town6 import _


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
class RowWidgetWide(object):
    template = """
        <xsl:template match="row-wide">
            <div class="grid-container full {@bgcolor}">
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


@TownApp.homepage_widget(tag='text')
class TextWidget(object):
    template = """
        <xsl:template match="text">
            <p class="homepage-text">
                <xsl:apply-templates select="node()"/>
            </p>
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
    news_limit = 3
    template = """
        <xsl:template match="news">
            <div metal:use-macro="layout.macros.newslist"
                tal:define="heading 'h5'; show_all_news_link True;
                hide_date False"
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
        occurrences = occurrences.limit(layout.org.event_limit_homepage)

        event_layout = EventBaseLayout(layout.model, layout.request)
        event_links = [
            EventCard(
                text=o.title,
                url=layout.request.link(o),
                subtitle=event_layout.format_date(
                    o.localized_start, 'event_short')
                .title(),
                image_url=o.event.image and layout.request.link(o.event.image),
                location=o.location,
                lead=get_lead(o.event.title)
            ) for o in occurrences
        ]

        latest_events = LinkGroup(
            title=_("Events"),
            links=event_links,
        ) if event_links else None

        return {
            'event_panel': latest_events,
            'all_events_link': Link(
                text=_("All events"),
                url=event_layout.events_url,
                classes=('more-link', )
            ),

        }


@TownApp.homepage_widget(tag='partners')
class PartnerWidget(object):

    template = """
            <xsl:template match="partners">
                <metal:block use-macro="layout.macros['partner-cards']" />
            </xsl:template>
    """

    def get_variables(self, layout):
        return {'partners': layout.partners}


@TownApp.homepage_widget(tag='services')
class ServicesWidget(object):
    template = """
        <xsl:template match="services">
            <div class="services-panel">
                <h3 tal:content="services_panel.title"></h3>

                <metal:block use-macro="layout.macros['panel-links']"
                    tal:define="panel services_panel; show_subtitle False;
                     as_callout True"
                />
            </div>
        </xsl:template>
    """

    def get_service_links(self, layout):
        yield Link(
            text=_("Online Counter"),
            url=layout.request.class_link(FormCollection),
            subtitle=(
                layout.org.meta.get('online_counter_label')
                or _("Forms and applications")
            ),
            classes=('online-counter', 'h5-size')
        )

        # only if there are publications, will we enable the link to them
        if not layout.org.hide_publications and layout.app.publications_count:
            yield Link(
                text=_("Publications"),
                url=layout.request.class_link(PublicationCollection),
                subtitle=_(
                    layout.org.meta.get('publications_label')
                    or _("Official Documents")
                ),
                classes=('publications', 'h5-size')
            )

        yield Link(
            text=_("Reservations"),
            url=layout.request.class_link(ResourceCollection),
            subtitle=(
                layout.org.meta.get('reservations_label')
                or _("Daypasses and rooms")
            ),
            classes=('reservations', 'h5-size')
        )

        if layout.org.meta.get('e_move_url'):
            yield Link(
                text=_("E-Move"),
                url=layout.org.meta.get('e_move_url'),
                subtitle=(
                    layout.org.meta.get('e_move_label')
                    or _("Move with eMovingCH")
                ),
                classes=('e-move', 'h5-size')
            )

        resources = ResourceCollection(layout.app.libres_context)

        # ga-tageskarte is the legacy name
        sbb_daypass = resources.by_name('sbb-tageskarte') \
            or resources.by_name('ga-tageskarte')

        if sbb_daypass:
            yield Link(
                text=_("SBB Daypass"),
                url=layout.request.link(sbb_daypass),
                subtitle=(
                    layout.org.meta.get('daypass_label')
                    or _("Generalabonnement for Towns")
                ),
                classes=('sbb-daypass', 'h5-size')
            )

    def get_variables(self, layout):
        return {
            'services_panel': LinkGroup(_("Services"), links=tuple(
                self.get_service_links(layout)
            ))
        }


@TownApp.homepage_widget(tag='contacts_and_albums')
class ContactsAndAlbumsWidget(object):

    template = """
           <xsl:template match="contacts_and_albums">
              <div class="contacts-albums-panel">
                <h3 tal:content="contacts_and_albums_panel.title"></h3>
                <metal:block use-macro="layout.macros['panel-links']"
                   tal:define="panel contacts_and_albums_panel;
                   classes ['more-list']"
                />
              </div>
           </xsl:template>
       """

    def get_variables(self, layout):
        request = layout.request

        return {
            'contacts_and_albums_panel': LinkGroup(
                title=_("Contacts"),
                links=[
                    Link(
                        text=_("People"),
                        url=request.class_link(PersonCollection),
                        subtitle=_("All contacts"),
                        classes=('h5-size',)
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
class FocusWidget(object):

    template = """
         <xsl:template match="focus">
            <xsl:choose>
              <xsl:when test="@hide-title"></xsl:when>
              <xsl:otherwise>
                <h3>
                  <xsl:choose>
                    <xsl:when test="@title">
                      <xsl:value-of select="@title" />
                   </xsl:when>
                   <xsl:otherwise>
                     <metal:block use-macro="layout.macros['focus-title']" />
                   </xsl:otherwise>
                  </xsl:choose>
                </h3>
              </xsl:otherwise>
            </xsl:choose>
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
            <xsl:variable name="image_url">
                <xsl:choose>
                     <xsl:when test="@image-url">
                        <xsl:value-of
                        select="concat($apos, @image-url, $apos)" />
                    </xsl:when>
                     <xsl:otherwise>
                        <xsl:value-of select="'None'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="no_title">
                <xsl:choose>
                     <xsl:when test="@hide-title">
                        <xsl:value-of select="'True'" />
                    </xsl:when>
                     <xsl:otherwise>
                        <xsl:value-of select="'False'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="no_lead">
                <xsl:choose>
                     <xsl:when test="@hide-lead">
                        <xsl:value-of select="'True'" />
                    </xsl:when>
                     <xsl:otherwise>
                        <xsl:value-of select="'False'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="no_text">
                <xsl:choose>
                     <xsl:when test="@hide-text">
                        <xsl:value-of select="'True'" />
                    </xsl:when>
                     <xsl:otherwise>
                        <xsl:value-of select="'False'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <metal:block use-macro="layout.macros['focus-panel']">
              <xsl:attribute name="tal:define">
                <xsl:value-of
                select="concat(
                  'page_path ',
                   $apos,
                    @page-path,
                    $apos,
                    '; ',
                    'hide_title ',
                    $no_title,
                    '; ',
                    'hide_lead ',
                    $no_lead,
                    '; ',
                    'hide_text ',
                    $no_text,
                    '; ',
                    'image_src ',
                    $image_src,
                    '; ',
                    'image_url ',
                    $image_url,
                    ';'
                    )"/>
              </xsl:attribute>
            </metal:block>
        </xsl:template>
    """

    def get_variables(self, layout):
        return {}
