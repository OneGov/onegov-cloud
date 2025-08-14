from __future__ import annotations

from sqlalchemy import or_

from onegov.core.collection import GenericCollection
from onegov.core.utils import toggle
from onegov.parliament.models import Parliamentarian
from onegov.user.collections.user import as_dictionary_of_sets

from typing import Any, TYPE_CHECKING
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self

ParliamentarianT = TypeVar(
    'ParliamentarianT',
    bound=Parliamentarian,
    default=Any
)


class ParliamentarianCollection(GenericCollection[ParliamentarianT]):

    def __init__(self, session: Session, **filters: Any):
        # print('*** tschupre __init__ filters:', filters)
        super().__init__(session)
        self.filters = as_dictionary_of_sets(filters)
        # print('*** tschupre __init__ filters 2:', filters)
        if 'active' not in self.filters:
            self.filters['active'] = {}
        if 'party' not in self.filters:
            self.filters['party'] = {}

    def __getattr__(self, name: str) -> set[Any] | None:
        if name not in self.filters:
            raise AttributeError(name)

        return self.filters[name]

    @property
    def model_class(self) -> type[ParliamentarianT]:
        return Parliamentarian  # type: ignore[return-value]

    def query(self) -> Query[ParliamentarianT]:
        query = super().query()

        for key, values in self.filters.items():
            if values:
                query = self.apply_filter(query, key, values)

        return query.order_by(
            Parliamentarian.last_name,
            Parliamentarian.first_name,
        )

    def apply_filter(
        self,
        query: Query[ParliamentarianT],
        key: str,
        values: set[str]
    ) -> Query[ParliamentarianT]:
        if '' in values:
            return query.filter(
                or_(
                    getattr(Parliamentarian, key).in_(values),
                    getattr(Parliamentarian, key).is_(None)
                )
            )

        return query.filter(getattr(Parliamentarian, key).in_(values))

    def for_filter(self, **filters: Any) -> Self:
        # print('*** tschupre for_filter filters:', filters)
        toggled = {
            key: toggle(self.filters.get(key, set()), value)
            for key, value in filters.items()
        }

        for key in self.filters:
            if key not in toggled:
                toggled[key] = self.filters[key]

        return self.__class__(self.session, **toggled)

    def party_values(self) -> list[str]:
        """ Returns a list of all parties given in the database. """

        return sorted([
            party[0]
            for party in self.session.query(Parliamentarian.party).distinct()
            if party[0]
        ])
