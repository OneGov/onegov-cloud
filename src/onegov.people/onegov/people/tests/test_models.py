from onegov.core.utils import module_path
from onegov.people.models import Agency
from onegov.people.models import AgencyMembership
from onegov.people.models import Person
from os.path import splitext
from pytest import mark


def test_person(session):
    session.add(
        Person(
            salutation="Herr",
            first_name="Hans",
            last_name="Maulwurf",
            function="Director",
            picture_url="https://thats.me/hans-maulwurf/picture",
            email="han.maulwurf@springfield.com",
            phone="11122334455",
            website="https://thats.me/hans-maulwurf",
            address="Fakestreet 1, Springfield",
            notes="bad vision",
        )
    )
    session.flush()
    person = session.query(Person).one()

    assert person.salutation == "Herr"
    assert person.first_name == "Hans"
    assert person.last_name == "Maulwurf"
    assert person.function == "Director"
    assert person.picture_url == "https://thats.me/hans-maulwurf/picture"
    assert person.email == "han.maulwurf@springfield.com"
    assert person.phone == "11122334455"
    assert person.website == "https://thats.me/hans-maulwurf"
    assert person.address == "Fakestreet 1, Springfield"
    assert person.notes == "bad vision"
    assert person.title == "Maulwurf Hans"
    assert person.spoken_title == "Herr Hans Maulwurf"

    person.salutation = None
    assert person.spoken_title == "Hans Maulwurf"


def test_person_vcard(session):
    person = Person(
        salutation="Dr.",
        first_name="Erika",
        last_name="Mustermann",
        picture_url=(
            "http://commons.wikimedia.org/wiki/"
            "File:Erika_Mustermann_2010.jpg"
        ),
        phone="+49 221 9999123",
        address="Heidestraße 17\n51147 Köln\nGermany",
        email="erika@mustermann.de",
        website="http://de.wikipedia.org/"
    )
    session.add(person)
    session.flush()

    agency = Agency(
        name="wikimedia",
        title="Wikimedia"
    )
    agency.add_person(person, "Redaktion & Gestaltung")
    session.add(agency)
    session.flush()

    vcard = person.vcard
    assert "BEGIN:VCARD" in vcard
    assert "VERSION:3.0" in vcard
    assert "N:Mustermann;Erika;;Dr.;" in vcard
    assert "FN:Dr. Erika Mustermann" in vcard
    assert "ORG:Wikimedia;Redaktion & Gestaltung" in vcard
    assert (
        "PHOTO:http://commons.wikimedia.org/wiki/"
        "File:Erika_Mustermann_2010.jpg"
    ) in vcard
    assert "TEL:+49 221 9999123" in vcard
    assert "ADR:;;Heidestraße 17\\n51147 Köln\\nGermany;;;;" in vcard
    assert "EMAIL:erika@mustermann.de" in vcard
    assert "URL:http://de.wikipedia.org/" in vcard
    assert "END:VCARD" in vcard


def test_person_polymorphism(session):

    class MyPerson(Person):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherPerson(Person):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(Person(first_name='default', last_name='person'))
    session.add(MyPerson(first_name='my', last_name='person'))
    session.add(MyOtherPerson(first_name='other', last_name='person'))
    session.flush()

    assert session.query(Person).count() == 3
    assert session.query(MyPerson).one().first_name == 'my'
    assert session.query(MyOtherPerson).one().first_name == 'other'


def test_agency(test_app):
    session = test_app.session()
    session.add(
        Agency(
            title="Foreigners' registration office",
            name="foreigners-registration-office",
            description="Agency regarding foreigners",
            portrait=(
                "The Foreigners’ Registration Office is responsible for "
                "matters related to laws concerning foreigners, as well as "
                "the granting and extension of residence permits."
            )
        )
    )
    session.flush()
    agency = session.query(Agency).one()

    assert agency.title == "Foreigners' registration office"
    assert agency.name == "foreigners-registration-office"
    assert agency.description == "Agency regarding foreigners"
    assert agency.portrait == (
        "The Foreigners’ Registration Office is responsible for matters "
        "related to laws concerning foreigners, as well as the granting "
        "and extension of residence permits."
    )
    assert not agency.meta
    assert not agency.content


@mark.parametrize("organigram", [
    (module_path('onegov.people', 'tests/fixtures/organigram.jpg'), '.jpe'),
    (module_path('onegov.people', 'tests/fixtures/organigram.png'), '.png'),
])
def test_agency_organigram(test_app, organigram):
    with open(organigram[0], 'rb') as organigram_file:
        session = test_app.session()
        session.add(
            Agency(
                title="Agency",
                name="agency",
                organigram_file=organigram_file
            )
        )
        session.flush()
    agency = session.query(Agency).one()

    assert splitext(agency.organigram_file.name)[1] == organigram[1]
    with open(organigram[0], 'rb') as organigram_file:
        assert agency.organigram_file.read() == organigram_file.read()


def test_agency_add_person(session):
    agency = Agency(title="Agency", name="agency",)
    patty = Person(first_name="Patty", last_name="Bouvier")
    selma = Person(first_name="Selma", last_name="Bouvier")
    session.add(agency)
    session.add(patty)
    session.add(selma)
    session.flush()

    agency.add_person(patty, "Staff")
    agency.add_person(selma.id, "Staff", since="2012")
    agency.add_person(str(selma.id), "Managing director", since="2018")

    assert [m.order for m in agency.memberships] == [0, 1, 2]

    people = [f"{m.title} {m.person.first_name}" for m in agency.memberships]
    assert people == ['Staff Patty', 'Staff Selma', 'Managing director Selma']

    role = sorted([f"{m.title} @ {m.agency.title}" for m in patty.memberships])
    assert role == ["Staff @ Agency"]

    role = sorted([f"{m.title} @ {m.agency.title}" for m in selma.memberships])
    assert role == ["Managing director @ Agency", "Staff @ Agency"]


def test_agency_polymorphism(session):

    class MyAgency(Agency):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherAgency(Agency):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(Agency(title='default', name='default'))
    session.add(MyAgency(title='my', name='my'))
    session.add(MyOtherAgency(title='other', name='other'))
    session.flush()

    assert session.query(Agency).count() == 3
    assert session.query(MyAgency).one().title == 'my'
    assert session.query(MyOtherAgency).one().title == 'other'


def test_membership(session):
    agency = Agency(title='agency', name='agency')
    person = Person(first_name='a', last_name='person')
    session.add(agency)
    session.add(person)
    session.flush()

    session.add(
        AgencyMembership(
            title="Director",
            order=12,
            since="2012",
            agency_id=agency.id,
            person_id=person.id
        )
    )
    session.flush()
    membership = session.query(AgencyMembership).one()

    assert membership.title == "Director"
    assert membership.order == 12
    assert membership.since == "2012"
    assert membership.agency_id == agency.id
    assert membership.person_id == person.id
    assert membership.agency == agency
    assert membership.person == person
    assert agency.memberships.one() == membership
    assert person.memberships.one() == membership

    session.delete(agency)
    session.flush()
    assert session.query(Agency).count() == 0
    assert session.query(Person).count() == 1
    assert session.query(AgencyMembership).count() == 0


def test_membership_polymorphism(session):
    agency = Agency(title='agency', name='agency')
    person = Person(first_name='a', last_name='person')
    session.add(agency)
    session.add(person)
    session.flush()

    class MyMembership(AgencyMembership):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherMembership(AgencyMembership):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(
        AgencyMembership(
            title='default',
            agency_id=agency.id,
            person_id=person.id,
            order=0
        )
    )
    session.add(
        MyMembership(
            title='my',
            agency_id=agency.id,
            person_id=person.id,
            order=1
        )
    )
    session.add(
        MyOtherMembership(
            title='other',
            agency_id=agency.id,
            person_id=person.id,
            order=2
        )
    )
    session.flush()

    assert session.query(AgencyMembership).count() == 3
    assert session.query(MyMembership).one().title == 'my'
    assert session.query(MyOtherMembership).one().title == 'other'
