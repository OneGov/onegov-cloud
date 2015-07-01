from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.orgs.models import Organization, Person, Membership


class OrganizationCollection(AdjacencyListCollection):
    __listclass__ = Organization


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
        return self.query().filter(Person.id == id).first()


class MembershipCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Membership)

    def add(self, organization, person, function):
        membership = Membership(
            organization=organization,
            person=person,
            function=function
        )

        self.session.add(membership)
        self.session.flush()

        return membership

    def by_organization_and_person(self, organization, person):
        query = self.query().filter(organization=organization)
        query = query.filter(person=person)

        return query.first()

    def delete(self, organization, person):
        query = self.query().filter(organization=organization)
        query = query.filter(person=person)

        query.delete()
