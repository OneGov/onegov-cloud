from cached_property import cached_property
from elasticsearch_dsl.query import MultiMatch
from onegov.core.templates import render_macro
from onegov.directory import DirectoryEntry, DirectoryEntryCollection
from onegov.form import as_internal_id
from onegov.winterthur.app import WinterthurApp
from sqlalchemy import cast, func, literal_column, Text
from sqlalchemy.dialects.postgresql import array


def lines(value):
    if isinstance(value, (tuple, list)):
        yield from value

    for line in str(value).split('\n'):
        yield line


@WinterthurApp.directory_search_widget('inline')
class InlineSearch(object):

    def __init__(self, request, directory, search_query):
        self.app = request.app
        self.request = request
        self.directory = directory
        self.search_query = search_query

    @cached_property
    def term(self):
        return (self.search_query or {}).get('term', None)

    @cached_property
    def searchable(self):
        return tuple(self.directory.configuration.searchable)

    @cached_property
    def hits(self):
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

    def html(self, layout):
        return render_macro(layout.macros['inline_search'], self.request, {
            'term': self.term,
            'directory': self.directory,
            'action': self.request.class_link(
                DirectoryEntryCollection,
                variables={
                    'directory_name': self.directory.name,
                    'search': self.name
                }
            )
        })

    def fragments(self, entry):
        for name in self.searchable:
            key = as_internal_id(name)

            fragments = (
                f'{name}: {line.lstrip(" -")}'
                for line in lines(entry.values[key])
                if self.term in line
            )

            fragments = tuple(f for ix, f in enumerate(fragments) if ix <= 2)

            if fragments:
                yield name, fragments

    def lead(self, layout, entry):
        if not self.term:
            return None

        hit = self.hits[str(entry.id)]

        for key in hit.meta.highlight:
            for fragment in hit.meta.highlight[key]:
                return fragment

    def adapt(self, query):
        if not self.term:
            return query

        ids = tuple(self.hits.keys())

        query = query.filter(DirectoryEntry.id.in_(ids))

        if ids:
            query = query.order_by(False)
            query = query.order_by(
                func.array_position(
                    array(ids),
                    cast(literal_column('id'), Text)
                )
            )

        print(query)

        return query
