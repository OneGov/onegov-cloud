from onegov.core.utils import module_path
from onegov.people.models import Agency
from onegov.people.models import AgencyMembership
from onegov.people.models import Person
from os.path import splitext
from pytest import mark


def test_person(session):
    session.add(
        Person(
            salutation="Mr.",
            academic_title="Dr.",
            first_name="Hans",
            last_name="Maulwurf",
            born="1970",
            profession="Truck Driver",
            function="Director",
            political_party="Democratic Party",
            parliamentary_group="Democrats",
            picture_url="https://thats.me/hans-maulwurf/picture",
            email="han.maulwurf@springfield.com",
            phone="11122334455",
            phone_direct="11122334456",
            website="https://thats.me/hans-maulwurf",
            address="Fakestreet 1, Springfield",
            notes="Has bad vision.",
        )
    )
    session.flush()
    person = session.query(Person).one()

    assert person.salutation == "Mr."
    assert person.academic_title == "Dr."
    assert person.first_name == "Hans"
    assert person.last_name == "Maulwurf"
    assert person.born == "1970"
    assert person.profession == "Truck Driver"
    assert person.function == "Director"
    assert person.political_party == "Democratic Party"
    assert person.parliamentary_group == "Democrats"
    assert person.picture_url == "https://thats.me/hans-maulwurf/picture"
    assert person.email == "han.maulwurf@springfield.com"
    assert person.phone == "11122334455"
    assert person.phone_direct == "11122334456"
    assert person.website == "https://thats.me/hans-maulwurf"
    assert person.address == "Fakestreet 1, Springfield"
    assert person.notes == "Has bad vision."

    assert person.spoken_title == "Dr. Hans Maulwurf"

    person.academic_title = None
    assert person.spoken_title == "Hans Maulwurf"


def test_person_vcard(session):
    person = Person(
        salutation="Mr.",
        academic_title="Dr.",
        first_name="Hans",
        last_name="Maulwurf",
        function="Director",
        picture_url="https://thats.me/hans-maulwurf/picture",
        email="han.maulwurf@springfield.com",
        phone="11122334455",
        phone_direct="11122334456",
        website="https://thats.me/hans-maulwurf",
        address="Fakestreet 1, Springfield",
        notes="Has bad vision.",
    )
    session.add(person)
    session.flush()

    agency = Agency(name="agency", title="Agency")
    agency.add_person(person.id, "Membership")
    session.add(agency)
    session.flush()

    vcard = person.vcard()
    assert "BEGIN:VCARD" in vcard
    assert "VERSION:3.0" in vcard
    assert "ADR;CHARSET=utf-8:;;Fakestreet 1\\, Springfield;;;;" in vcard
    assert "EMAIL:han.maulwurf@springfield.com" in vcard
    assert "FN;CHARSET=utf-8:Dr. Hans Maulwurf" in vcard
    assert "N;CHARSET=utf-8:Maulwurf;Hans;;Dr.;" in vcard
    assert "ORG;CHARSET=utf-8:Agency\\, Membership" in vcard
    assert "PHOTO:https://thats.me/hans-maulwurf/picture" in vcard
    assert "TEL:11122334455" in vcard
    assert "TEL:11122334456" in vcard
    assert "TITLE;CHARSET=utf-8:Director" in vcard
    assert "URL:https://thats.me/hans-maulwurf" in vcard
    assert "NOTE;CHARSET=utf-8:" not in vcard
    assert "END:VCARD" in vcard

    vcard = person.vcard((
        'academic_title',
        'function',
        'picture_url',
        'phone_direct',
        'website',
        'address',
    ))
    assert "BEGIN:VCARD" in vcard
    assert "VERSION:3.0" in vcard
    assert "ADR;CHARSET=utf-8:" not in vcard
    assert "EMAIL:han.maulwurf@springfield.com" in vcard
    assert "FN;CHARSET=utf-8:Hans Maulwurf" in vcard
    assert "N;CHARSET=utf-8:Maulwurf;Hans;;;" in vcard
    assert "ORG;CHARSET=utf-8:Agency\\, Membership" in vcard
    assert "PHOTO:" not in vcard
    assert "TEL:11122334455" in vcard
    assert "TEL:11122334456" not in vcard
    assert "TITLE;CHARSET=utf-8:" not in vcard
    assert "URL:" not in vcard
    assert "NOTE;CHARSET=utf-8:Has bad vision." in vcard
    assert "END:VCARD" in vcard


def test_person_membership_by_agency(session):
    agency_a = Agency(title="A", name="a")
    agency_b = Agency(title="B", name="b")
    agency_c = Agency(title="C", name="c")
    agency_d = Agency(title="D", name="d")
    person = Person(first_name="Hans", last_name="Maulwurf")
    session.add(agency_a)
    session.add(agency_b)
    session.add(agency_c)
    session.add(agency_d)
    session.add(person)
    session.flush()

    agency_b.add_person(person.id, 'l')
    agency_c.add_person(person.id, 'm')
    agency_a.add_person(person.id, 'n')
    agency_d.add_person(person.id, 'o')

    person = session.query(Person).one()
    assert [m.title for m in person.memberships_by_agency] == [
        'n', 'l', 'm', 'o'
    ]


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

    agency.add_person(patty.id, "Staff")
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


def test_agency_sort_children(session):
    parent = Agency(id=1, name='parent', title='agency')
    session.add(Agency(id=2, name='child_1', parent=parent, order=10,
                       title="Bjorm Guomundsdóttir's"))
    session.add(Agency(id=3, name='child_2', parent=parent, order=11,
                       title="Björn Guðmundsdóttir's"))
    session.add(Agency(id=4, name='child_3', parent=parent, order=11,
                       title="Björk Guomundsdottir's"))
    session.flush()
    assert [c.title for c in parent.children] == [
        "Bjorm Guomundsdóttir's",
        "Björn Guðmundsdóttir's",
        "Björk Guomundsdottir's"
    ]

    parent.sort_children()
    session.flush()
    session.expire_all()
    assert [c.title for c in parent.children] == [
        "Björk Guomundsdottir's",  # ö=oe
        "Björn Guðmundsdóttir's",
        "Bjorm Guomundsdóttir's",
    ]


def test_agency_sort_memberships(session):
    agency = Agency(title='agency', name='agency')
    bjork = Person(first_name="Björn", last_name="Guðmundsdóttir")
    bjorm = Person(first_name="Björk", last_name="Guomundsdottir")
    bjorn = Person(first_name="Bjorm", last_name="Guomundsdóttir")
    session.add(agency)
    session.add(bjork)
    session.add(bjorm)
    session.add(bjorn)
    session.flush()

    for order, person in enumerate((bjorm, bjork, bjorn)):
        session.add(
            AgencyMembership(
                title="Member",
                order=order,
                since="2012",
                agency_id=agency.id,
                person_id=person.id
            )
        )
    session.flush()
    assert [m.person.title for m in agency.memberships] == [
        'Guomundsdottir Björk',
        'Guðmundsdóttir Björn',
        'Guomundsdóttir Bjorm'
    ]

    agency.sort_relationships()
    assert [m.person.title for m in agency.memberships] == [
        'Guðmundsdóttir Björn',  # ð=d
        'Guomundsdottir Björk',  # ö=oe
        'Guomundsdóttir Bjorm'
    ]


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


def test_membership_siblings(session):
    agency_a = Agency(title='A', name='a')
    agency_b = Agency(title='B', name='b')
    person = Person(first_name='a', last_name='person')
    session.add(agency_a)
    session.add(agency_b)
    session.add(person)
    session.flush()

    membership_x = AgencyMembership(
        title="X",
        order=1,
        agency_id=agency_a.id,
        person_id=person.id
    )
    membership_y = AgencyMembership(
        title="Y",
        order=2,
        agency_id=agency_a.id,
        person_id=person.id
    )
    membership_z = AgencyMembership(
        title="Z",
        order=3,
        agency_id=agency_b.id,
        person_id=person.id
    )
    session.add(membership_z)
    session.add(membership_x)
    session.add(membership_y)
    session.flush()

    assert [m.title for m in membership_x.siblings] == ['X', 'Y']
    assert [m.title for m in membership_y.siblings] == ['X', 'Y']
    assert [m.title for m in membership_z.siblings] == ['Z']
