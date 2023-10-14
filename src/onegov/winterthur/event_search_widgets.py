from functools import cached_property
from sqlalchemy import func, or_, cast, String

from onegov.core.templates import render_macro
from onegov.event import OccurrenceCollection, Event
from onegov.winterthur.app import WinterthurApp


@WinterthurApp.event_search_widget('inline')
class InlineEventSearch:

    def __init__(self, request, search_query):
        self.app = request.app
        self.request = request
        self.search_query = search_query

    @cached_property
    def term(self):
        return (self.search_query or {}).get('term', None)

    def html(self, layout):
        return render_macro(layout.macros['inline_search'],
                            self.request, {
            'term': self.term,
            'title': None,
            'action': self.request.class_link(
                OccurrenceCollection,
                variables={
                    'search': self.name
                }
            )
        })

    def adapt(self, query):
        """
        Adapt the query to search for words in the search term `self.term in
        event search properties.

        """
        if not self.term:
            return query

        search_properties = [p for p in Event.es_properties.keys() if not
                             p.startswith('es_')]
        for word in self.term.split():
            conditions = []
            for p in search_properties:
                conditions.append(
                    func.lower(cast(getattr(Event, p), String)).contains(
                        word.lower()))
            query = query.filter(or_(*conditions))

        return query
