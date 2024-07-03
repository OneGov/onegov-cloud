from functools import cached_property

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

    def by_id(self, id: 'UUID') -> PersonT | None:  # type:ignore[override]
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

    @cached_property
    def unique_organisations(self) -> list[str]:
        query = self.session.query(Person.organisation)
        query = query.filter(Person.organisation.isnot(None)).distinct()
        query = query.order_by(Person.organisation)
        return tuple(p.organisation for p in query if p.organisation != '')

    @cached_property
    def unique_sub_organisations(self) -> list[str]:
        query = self.session.query(Person.sub_organisation)
        query = query.filter(Person.sub_organisation.isnot(None)).distinct()
        query = query.order_by(Person.sub_organisation)
        return tuple(p.sub_organisation
                     for p in query if p.sub_organisation != '')
