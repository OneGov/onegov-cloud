from __future__ import annotations

from functools import cached_property
from sqlalchemy import func, or_, cast, String

from onegov.core.templates import render_macro
from onegov.event import OccurrenceCollection, Event
from onegov.winterthur.app import WinterthurApp


from typing import ClassVar, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.layout import DefaultLayout
    from onegov.winterthur.request import WinterthurRequest
    from sqlalchemy.orm import Query
    from typing import TypeVar

    T = TypeVar('T')


@WinterthurApp.event_search_widget('inline')
class InlineEventSearch:

    name: ClassVar[Literal['inline']]

    def __init__(
        self,
        request: WinterthurRequest,
        search_query: dict[str, str]
    ) -> None:
        self.app = request.app
        self.request = request
        self.search_query = search_query

    @cached_property
    def term(self) -> str | None:
        return (self.search_query or {}).get('term', None)

    def html(self, layout: DefaultLayout) -> str:
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

    def adapt(self, query: Query[T]) -> Query[T]:
        """
        Adapt the query to search for words in the search term `self.term` in
        event search properties.

        """
        if not self.term:
            return query

        for word in self.term.split():
            query = query.filter(or_(*(
                func.lower(
                    cast(getattr(Event, prop), String)
                ).contains(word.lower())
                for prop in Event.fts_properties.keys()
            )))

        return query
