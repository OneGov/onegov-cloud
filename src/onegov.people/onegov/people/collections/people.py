from onegov.core import utils
from onegov.people.models import Person


class PersonCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Person)

    def add(self, first_name, last_name, **optional):
        person = Person(first_name=first_name, last_name=last_name, **optional)

        self.session.add(person)
        self.session.flush()

        return person

    def delete(self, person):
        self.session.delete(person)
        self.session.flush()

    def by_id(self, id):
        if utils.is_uuid(id):
            return self.query().filter(Person.id == id).first()
