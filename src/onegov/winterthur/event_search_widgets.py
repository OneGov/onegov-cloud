from functools import cached_property
from sqlalchemy import func, or_

from onegov.core.templates import render_macro
from onegov.event import OccurrenceCollection, Event
from onegov.winterthur.app import WinterthurApp


@WinterthurApp.event_search_widget('inline')
class InlineEventSearch:

    # TODO view allow empty search query
    def __init__(self, request, search_query):
        self.app = request.app
        self.request = request
        self.search_query = search_query

    @cached_property
    def term(self):
        return (self.search_query or {}).get('term', None)

    def html(self, layout):
        return render_macro(layout.macros['inline_event_search'],
                            self.request, {
            'term': self.term,
            'action': self.request.class_link(
                OccurrenceCollection,
                variables={
                    'search': self.name
                }
            )
        })

    def adapt(self, query):
        conditions = []

        if not self.term:
            return query

        search_properties = [p for p in Event.es_properties.keys() if not
                             p.startswith('es_')]
        for p in search_properties:
            conditions.append(
                func.lower(getattr(Event, p)).contains(self.term))

        query = query.filter(or_(*conditions))
        return query
