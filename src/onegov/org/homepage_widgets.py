from __future__ import annotations

from onegov.directory import DirectoryCollection
from onegov.event import OccurrenceCollection
from onegov.org import _, OrgApp
from onegov.org.elements import Link, LinkGroup
from onegov.org.models import ImageSet, ImageFile, News, NewsCollection
from onegov.file.models.fileset import file_to_set_associations
from operator import attrgetter
from sqlalchemy import func

from onegov.org.models.directory import ExtendedDirectoryEntryCollection


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from onegov.core.types import RenderData
    from onegov.org.layout import DefaultLayout
    from onegov.org.models import ExtendedDirectory


def get_lead(
    text: str,
    max_chars: int = 180,
    consider_sentences: bool = True
) -> str:

    if len(text) > max_chars:
        first_point_ix = text.find('.')
        if first_point_ix < 1 or not consider_sentences:
            return text[0:max_chars] + '...'
        elif first_point_ix >= max_chars:
            # still return the entire first sentence, but nothing more
            return text[0:first_point_ix + 1]
        else:
            # return up to the n'th sentence that is still below the limit
            end = text.rindex('.', 0, max_chars) + 1
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

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        directories: DirectoryCollection[ExtendedDirectory]
        directories = DirectoryCollection(
            layout.app.session(), type='extended')

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
                text=_('All directories'),
                url=layout.request.class_link(DirectoryCollection),
                classes=('more-link', )
            )
        )

        return {
            'directory_panel': LinkGroup(
                title=_('Directories'),
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

    def get_variables(self, layout: DefaultLayout) -> RenderData:

        root_pages = layout.root_pages
        if not root_pages:
            return {'news': ()}

        news_index: int | None = None
        for index, page in enumerate(root_pages):
            if page.type == 'news':
                if page.children:
                    # only bother doing the query if there are children
                    news_index = index
                break

        if news_index is None:
            return {'news': ()}

        # FIXME: We probably don't need full fat News objects for this
        #        and could instead just use children on the root news page
        #        if we need additional attributes, we can just add them
        #        to PageMeta, although we would still need to sort the news
        #        which can get costly if there's a lot of them. So fetching
        #        a small number fresh migh actually be faster, unless we
        #        separately cache the ones we need to display.
        collection = NewsCollection(layout.request)
        news = collection.sticky().all()
        # request more than the required amount of news to account for hidden
        # items which might be in front of the queue
        news.extend(
            collection.subset()
            .filter(~News.id.in_([n.id for n in news]))
            .limit(layout.org.news_limit_homepage)
        )
        # the ones that shouldn't be visible should already be excluded
        # but we do this again anyways just to be safe
        news = layout.request.exclude_invisible(news)
        news.sort(key=attrgetter('published_or_created'), reverse=True)

        return {
            'news': news,
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

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        occurrences = OccurrenceCollection(layout.app.session()).query()
        occurrences = occurrences.limit(layout.org.event_limit_homepage)

        event_links = [
            Link(
                text=o.title,
                url=layout.request.link(o),
                subtitle=layout.format_date(o.localized_start, 'event')
                .title()
            ) for o in occurrences
        ]

        event_links.append(
            Link(
                text=_('All events'),
                url=layout.events_url,
                classes=('more-link', )
            )
        )

        latest_events = LinkGroup(
            title=_('Events'),
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

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        return {'tiles': tuple(self.get_tiles(layout))}

    class Tile(NamedTuple):
        page: Link
        links: Sequence[Link]
        number: int

    def get_tiles(self, layout: DefaultLayout) -> Iterator[Tile]:

        request = layout.request
        homepage_pages = request.homepage_pages
        classes = ('tile-sub-link', )

        for ix, page in enumerate(layout.root_pages):
            if page.type == 'topic':

                yield self.Tile(
                    page=Link(page.title, page.link(request)),
                    number=ix + 1,
                    links=tuple(
                        Link(
                            child.title,
                            child.link(request),
                            classes=classes,
                            # this only accesses the `access` attribute
                            # which we have, so this is safe, even though
                            # it's not the actual page model
                            model=child,
                        )
                        for child in homepage_pages.get(page.id, ())
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
            height_d '{@height-d}'; searchbox '{@searchbox}';
            />
        </xsl:template>
    """

    def get_images_from_sets(
        self,
        layout: DefaultLayout
    ) -> Iterator[RenderData]:

        session = layout.app.session()

        sets = tuple(
            set_id for set_id, meta in session.query(ImageSet)
            .with_entities(ImageSet.id, ImageSet.meta)
            if meta.get('show_images_on_homepage')
            and meta.get('access', 'public') == 'public'
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

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        # if we don't have an album used for images, we use the images
        # shown on the homepage anyway to avoid having to show nothing
        images = tuple(self.get_images_from_sets(layout))

        return {
            'images': images,
        }
