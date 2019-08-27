from onegov.core import utils
from onegov.core.collection import GenericCollection
from onegov.people.models import Person


class PersonCollection(GenericCollection):
    """ Manages a list of people.

    Use it like this::

        from onegov.people import PersonCollection
        people = PersonCollection(session)

    """

    @property
    def model_class(self):
        return Person

    def add(self, first_name, last_name, **optional):
        person = self.model_class(
            first_name=first_name,
            last_name=last_name,
            **optional
        )

        self.session.add(person)
        self.session.flush()

        return person

    def by_id(self, id):
        if utils.is_uuid(id):
            return self.query().filter(self.model_class.id == id).first()
