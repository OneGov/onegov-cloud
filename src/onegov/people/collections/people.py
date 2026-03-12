from __future__ import annotations

from sqlalchemy import func

from onegov.core import utils
from onegov.core.collection import GenericCollection
from onegov.people.models import Person

from typing import Any
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID

PersonT = TypeVar('PersonT', bound=Person)


class BasePersonCollection(GenericCollection[PersonT]):

    @property
    def model_class(self) -> type[PersonT]:
        raise NotImplementedError()

    def add(  # type:ignore[override]
        self,
        first_name: str,
        last_name: str,
        **optional: Any
    ) -> PersonT:
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
    ) -> PersonT:
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

    def by_id(self, id: UUID) -> PersonT | None:  # type:ignore[override]
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

    def people_by_organisation(
        self,
        org: str | None,
        sub_org: str | None
    ) -> list[Person]:
        """
        Returns all persons of a given organisation and sub-organisation.

        If organisation and sub-organisation are both None, all persons are
        returned.
        """
        query = self.session.query(Person).order_by(Person.last_name,
                                                    Person.first_name)
        if org:
            query = query.filter(
                func.jsonb_contains(Person.content['organisations_multiple'],
                                    f'["{org}"]'))
        if sub_org:
            query = query.filter(
                func.jsonb_contains(Person.content['organisations_multiple'],
                                    f'["-{sub_org}"]'))
        return query.all()
