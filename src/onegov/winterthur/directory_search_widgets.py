from elasticsearch_dsl.query import MultiMatch  # type:ignore[import-untyped]
from functools import cached_property
from itertools import islice
from markupsafe import Markup
from onegov.core.templates import render_macro
from onegov.directory import DirectoryEntry
from onegov.form import as_internal_id
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.winterthur.app import WinterthurApp
from sqlalchemy import cast, func, literal_column, Text
from sqlalchemy.dialects.postgresql import array


from typing import ClassVar, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.org.layout import DefaultLayout
    from onegov.org.models import ExtendedDirectory
    from onegov.search.dsl import Hit
    from onegov.winterthur.request import WinterthurRequest
    from sqlalchemy.orm import Query
    from typing import TypeVar

    T = TypeVar('T')


def lines(value: str | tuple[str, ...] | list[str]) -> 'Iterator[str]':
    if isinstance(value, (tuple, list)):
        yield from value

    yield from str(value).split('\n')


@WinterthurApp.directory_search_widget('inline')
class InlineDirectorySearch:

    name: ClassVar[Literal['inline']]

    def __init__(
        self,
        request: 'WinterthurRequest',
        directory: 'ExtendedDirectory',
        search_query: dict[str, str] | None
    ) -> None:
        self.app = request.app
        self.request = request
        self.directory = directory
        self.search_query = search_query

    @cached_property
    def term(self) -> str | None:
        return (self.search_query or {}).get('term', None)

    @cached_property
    def searchable(self) -> tuple[str, ...]:
        return tuple(self.directory.configuration.searchable or ())

    @cached_property
    def hits(self) -> dict[str, 'Hit'] | None:
        if not self.term:
            return None

        search = self.app.es_search_by_request(
            request=self.request,
            types=('extended_directory_entries', )
        )

        search = search.filter('term', directory_id=str(self.directory.id))

        fields = tuple(
            f for f in DirectoryEntry.es_properties.keys()
            if not f.startswith('es_') and not f == 'directory_id'
        )

        match = MultiMatch(query=self.term, fields=fields, fuzziness=1)
        search = search.query(match)

        for field in fields:
            search = search.highlight(field)

        return {hit.meta.id: hit for hit in search[0:100].execute()}

    def html(self, layout: 'DefaultLayout') -> Markup:
        return render_macro(layout.macros['inline_search'],
                            self.request, {
            'term': self.term,
            'directory': self.directory,
            'title': self.directory.title,
            'action': self.request.class_link(
                ExtendedDirectoryEntryCollection,
                variables={
                    'directory_name': self.directory.name,
                    'search': self.name
                }
            )
        })

    def fragments(
        self,
        entry: DirectoryEntry
    ) -> 'Iterator[tuple[str, tuple[str, ...]]]':

        assert self.term is not None

        for name in self.searchable:
            key = as_internal_id(name)

            fragment_iter = (
                f'{name}: {line.lstrip(" -")}'
                for line in lines(entry.values[key])
                if self.term in line
            )

            fragments = tuple(islice(fragment_iter, 3))

            if fragments:
                yield name, fragments

    # FIXME: I think these fragments can contain Markup, so for now
    #        we are being potentially unsafe here. The documentation
    #        is unclear about what we get back here, but we used to
    #        render this with the structure keyword
    def lead(
        self,
        layout: 'DefaultLayout',
        entry: DirectoryEntry
    ) -> str | None:

        if not self.term:
            return None

        assert self.hits is not None
        hit = self.hits[str(entry.id)]

        for key in hit.meta.highlight:
            for fragment in hit.meta.highlight[key]:
                return Markup(fragment)  # noqa: MS001
        return None

    def adapt(self, query: 'Query[T]') -> 'Query[T]':
        if not self.term:
            return query

        assert self.hits is not None
        ids = tuple(self.hits.keys())

        query = query.filter(DirectoryEntry.id.in_(ids))

        if ids:
            query = query.order_by(False)
            query = query.order_by(
                func.array_position(
                    array(ids),  # type:ignore[call-overload]
                    cast(literal_column('id'), Text)
                )
            )

        return query
