from collections import namedtuple
from onegov.directory import DirectoryCollection
from onegov.event import OccurrenceCollection
from onegov.org import _, OrgApp
from onegov.org.elements import Link, LinkGroup
from onegov.org.layout import EventBaseLayout
from onegov.org.models import ImageSet, ImageFile, News
from onegov.file.models.fileset import file_to_set_associations
from sqlalchemy import func

from onegov.org.models.directory import ExtendedDirectoryEntryCollection


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


@OrgApp.homepage_widget(tag='row')
class RowWidget:
    template = """
        <xsl:template match="row">
            <div class="row">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='column')
class ColumnWidget:
    template = """
        <xsl:template match="column">
            <div class="small-12 medium-{@span} columns">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='text')
class TextWidget:
    template = """
        <xsl:template match="text">
            <p class="homepage-text">
                <xsl:apply-templates select="node()"/>
            </p>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='panel')
class PanelWidget:
    # panels with less than one link (not counting the more-link) are
    # hidden unless the user is logged-in
    template = """
        <xsl:template match="panel">
            <div class="side-panel requires-children">
                <xsl:attribute name="data-required-children">
                    <xsl:value-of select="'a:not(.more-link)'"/>
                </xsl:attribute>
                <xsl:attribute name="data-required-count">
                    <xsl:value-of select="'1'"/>
                </xsl:attribute>
                <xsl:attribute name="data-required-unless">
                    <xsl:value-of select="'.is-logged-in'"/>
                </xsl:attribute>

                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='links')
class LinksWidget:
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


@OrgApp.homepage_widget(tag='directories')
class DirectoriesWidget:
    template = """
        <xsl:template match="directories">
            <metal:block use-macro="layout.macros['directories-panel']" />
        </xsl:template>
    """

    def get_variables(self, layout):
        directories = DirectoryCollection(
            layout.app.session(), type="extended")

        links = [
            Link(
                text=d.title,
                url=layout.request.class_link(
                    ExtendedDirectoryEntryCollection,
                    {'directory_name': d.name}
                ),
                subtitle=d.lead
            ) for d in layout.request.exclude_invisible(directories.query())
        ]

        links.append(
            Link(
                text=_("All directories"),
                url=layout.request.class_link(DirectoryCollection),
                classes=('more-link', )
            )
        )

        return {
            'directory_panel': LinkGroup(
                title=_("Directories"),
                links=links,
            )
        }


@OrgApp.homepage_widget(tag='news')
class NewsWidget:

    template = """
        <xsl:template match="news">
            <div metal:use-macro="layout.macros.newslist"
                tal:define="heading 'h3'; show_all_news_link True;
                hide_date True"
            />
        </xsl:template>
    """

    def get_variables(self, layout):

        if not layout.root_pages:
            return {'news': ()}

        news_index = False
        for index, page in enumerate(layout.root_pages):
            if isinstance(page, News):
                news_index = index
                break

        if news_index is False:
            return {'news': ()}

        # request more than the required amount of news to account for hidden
        # items which might be in front of the queue
        news_limit = layout.org.news_limit_homepage
        news = layout.request.exclude_invisible(
            layout.root_pages[news_index].news_query(
                limit=news_limit + 2,
                published_only=not layout.request.is_manager
            ).all()
        )

        # limits the news, but doesn't count sticky news towards that limit
        def limited(news, limit):
            count = 0

            for item in news:
                if count < limit or item.is_visible_on_homepage:
                    yield item

                if not item.is_visible_on_homepage:
                    count += 1

        return {
            'news': limited(news, limit=news_limit),
            'get_lead': get_lead
        }


@OrgApp.homepage_widget(tag='homepage-cover')
class CoverWidget:
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
class EventsWidget:
    template = """
        <xsl:template match="events">
            <metal:block use-macro="layout.macros['events-panel']" />
        </xsl:template>
    """

    def get_variables(self, layout):
        occurrences = OccurrenceCollection(layout.app.session()).query()
        occurrences = occurrences.limit(layout.org.event_limit_homepage)

        event_layout = EventBaseLayout(layout.model, layout.request)
        event_links = [
            Link(
                text=o.title,
                url=layout.request.link(o),
                subtitle=event_layout.format_date(o.localized_start, 'event')
                .title()
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
            'event_panel': latest_events
        }


@OrgApp.homepage_widget(tag='homepage-tiles')
class TilesWidget:
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
        classes = ('tile-sub-link', )

        for ix, page in enumerate(layout.root_pages):
            if page.type == 'topic':

                children = []
                for child in page.children:
                    if child.id in (
                        n.id for n in homepage_pages[page.id]
                    ):
                        children.append(child)

                if not request.is_manager:
                    children = (
                        c for c in children if c.access == 'public'
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
                pass
            else:
                raise NotImplementedError


@OrgApp.homepage_widget(tag='line')
class HrWidget:
    template = """
        <xsl:template match="line">
            <hr />
        </xsl:template>
    """


@OrgApp.homepage_widget(tag='slider')
class SliderWidget:
    template = """
        <xsl:template match="slider">
            <div metal:use-macro="layout.macros['slider']"
            tal:define="height_m '{@height-m}';
            height_d '{@height-d}'"
            />
        </xsl:template>
    """

    def get_images_from_sets(self, layout):
        session = layout.app.session()

        sets = session.query(ImageSet)
        sets = sets.with_entities(ImageSet.id, ImageSet.meta)
        sets = tuple(
            s.id for s in sets
            if s.meta.get('show_images_on_homepage')
            and s.meta.get('access', 'public') == 'public'
        )

        if not sets:
            return

        files = session.query(file_to_set_associations)
        files = files.with_entities(file_to_set_associations.c.file_id)
        files = files.filter(file_to_set_associations.c.fileset_id.in_(
            sets
        ))

        images = session.query(ImageFile)
        images = images.filter(ImageFile.id.in_(files.subquery()))
        images = images.order_by(func.random())
        images = images.limit(6)

        for image in images:
            yield {
                'note': image.note,
                'src': layout.request.link(image)
            }

    def get_variables(self, layout):
        # if we don't have an album used for images, we use the images
        # shown on the homepage anyway to avoid having to show nothing
        images = tuple(self.get_images_from_sets(layout))

        return {
            'images': images,
        }
