from __future__ import annotations

from sqlalchemy import func, or_, type_coerce
from sqlalchemy_utils import escape_like

from onegov.core import utils
from onegov.core.collection import GenericCollection
from onegov.core.orm.types import JSON
from onegov.people.models import Person

from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from uuid import UUID


class BasePersonCollection[T: Person](GenericCollection[T]):

    @property
    def model_class(self) -> type[T]:
        raise NotImplementedError()

    def add(  # type:ignore[override]
        self,
        first_name: str,
        last_name: str,
        **optional: Any
    ) -> T:
        person = self.model_class(
            first_name=first_name,
            last_name=last_name,
            **optional
        )

        self.session.add(person)
        self.session.flush()

        return person

    def add_or_get(
        self,
        first_name: str,
        last_name: str,
        compare_names_only: bool = False,
        **optional: Any
    ) -> T:
        """
        Adds a person if it does not exist yet, otherwise returns the
        existing.

        """
        query = self.query()
        query = query.filter(self.model_class.first_name == first_name)
        query = query.filter(self.model_class.last_name == last_name)
        if not compare_names_only:
            for key, value in optional.items():
                query = query.filter(getattr(self.model_class, key) == value)

        item = query.first()

        if item:
            return item
        else:
            return self.add(first_name, last_name, **optional)

    def by_id(self, id: UUID) -> T | None:  # type:ignore[override]
        if utils.is_uuid(id):
            return self.query().filter(self.model_class.id == id).first()
        return None


class PersonCollection(BasePersonCollection[Person]):
    """ Manages a list of people.

    Use it like this::

        from onegov.people import PersonCollection
        people = PersonCollection(session)

    """

    @property
    def model_class(self) -> type[Person]:
        return Person

    def query(self) -> Query[Person]:
        return super().query().order_by(Person.last_name, Person.first_name)

    def people_by_organisation(
        self,
        org: str | None,
        sub_org: str | None,
        query: Query[Person],
    ) -> Query[Person]:
        """
        Returns a query filtered by organisation and sub-organisation.
        """
        if org:
            query = query.filter(
                func.jsonb_contains(
                    Person.content['organisations_multiple'],
                    type_coerce([org], JSON)
                )
            )
        if sub_org:
            query = query.filter(
                func.jsonb_contains(
                    Person.content['organisations_multiple'],
                    type_coerce([f'-{sub_org}'], JSON)
                )
            )
        return query

    def people_by_search_term(
        self,
        search_term: str | None,
        query: Query[Person],
    ) -> Query[Person]:
        """
        Applies a search term filter on name and function to a query.
        """
        if not search_term:
            return query

        term = f'%{escape_like(search_term)}%'
        return query.filter(or_(
            Person.last_name.ilike(term, escape='*'),
            Person.first_name.ilike(term, escape='*'),
            Person.function.ilike(term, escape='*'),
        ))
