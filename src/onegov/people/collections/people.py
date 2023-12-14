from onegov.core import utils
from onegov.core.collection import GenericCollection
from onegov.people.models import Person


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID


class PersonCollection(GenericCollection[Person]):
    """ Manages a list of people.

    Use it like this::

        from onegov.people import PersonCollection
        people = PersonCollection(session)

    """

    @property
    def model_class(self) -> type[Person]:
        return Person

    def add(  # type:ignore[override]
        self,
        first_name: str,
        last_name: str,
        **optional: Any
    ) -> Person:

        person = self.model_class(
            first_name=first_name,
            last_name=last_name,
            **optional
        )

        self.session.add(person)
        self.session.flush()

        return person

    def by_id(self, id: 'UUID') -> Person | None:  # type:ignore[override]
        if utils.is_uuid(id):
            return self.query().filter(self.model_class.id == id).first()
        return None
