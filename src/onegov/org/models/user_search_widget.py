from __future__ import annotations

from functools import cached_property
from sqlalchemy import func, or_, cast, String

from onegov.core.templates import render_macro
from onegov.user import User, UserCollection


from typing import ClassVar, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.layout import DefaultLayout
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Query


class InlineUserSearch:
    """ A substring search over users, always enabled on the user
    management. Mirrors the inline event/directory search widgets. """

    name: ClassVar[Literal['inline']] = 'inline'

    def __init__(
        self,
        request: OrgRequest,
        search_query: dict[str, str] | None
    ) -> None:
        self.request = request
        self.search_query = search_query

    @cached_property
    def term(self) -> str | None:
        term = (self.search_query or {}).get('term')
        if term:
            return term
        value = self.request.params.get('term')
        return value if isinstance(value, str) else None

    def html(self, layout: DefaultLayout) -> str:
        return render_macro(layout.macros['inline_search'], self.request, {
            'term': self.term,
            'action': self.request.class_link(UserCollection)
        })

    def adapt(self, query: Query[User]) -> Query[User]:
        """ Filters users whose search properties contain each word of the
        term (case-insensitive substring). """
        if not self.term:
            return query

        for word in self.term.split():
            query = query.filter(or_(*(
                func.lower(cast(column, String)).contains(word.lower())
                for column in (User.username, User.realname)
            )))

        return query
