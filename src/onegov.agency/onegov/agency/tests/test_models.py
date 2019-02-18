from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import AgencyMembershipMove
from onegov.agency.models import AgencyMove
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from onegov.people import Agency
from onegov.people import AgencyMembership
from onegov.people import Person


def test_extended_agency(agency_app):
    session = agency_app.session()

    agency = ExtendedAgency(
        title="Test Agency",
        name="test-agency",
        portrait="This is a test\nagency."
    )
    session.add(agency)
    session.flush()

    agency = session.query(Agency).one()
    assert isinstance(agency, ExtendedAgency)
    assert agency.type == 'extended'
    assert agency.title == "Test Agency"
    assert agency.name == "test-agency"
    assert agency.portrait == "This is a test\nagency."
    assert agency.portrait_html == "<p>This is a test<br>agency.</p>"
    assert agency.export_fields == []
    assert agency.pdf is None
    assert agency.pdf_file is None
    assert agency.trait == 'agency'
    assert agency.proxy().id == agency.id
    assert agency.is_hidden_from_public is None
    assert agency.es_public is True

    agency.pdf_file = b'PDF'
    assert agency.pdf_file.read() == b'PDF'
    assert agency.pdf_file.filename == 'test-agency.pdf'
    assert agency.pdf.name == 'test-agency.pdf'

    agency.pdf_file = b'PDF2'
    assert agency.pdf_file.read() == b'PDF2'
    assert agency.pdf_file.filename == 'test-agency.pdf'
    assert agency.pdf.name == 'test-agency.pdf'

    agency.is_hidden_from_public = True
    assert agency.es_public is False


def test_extended_agency_add_person(session):
    agency = ExtendedAgency(title="Agency", name="agency",)
    person = ExtendedPerson(first_name="A", last_name="Person")
    session.add(person)
    session.flush()

    agency.add_person(person.id, "Staff", since="2012", note="N", prefix="*")
    membership = agency.memberships.one()

    assert isinstance(membership, ExtendedAgencyMembership)
    assert membership.since == "2012"
    assert membership.note == "N"
    assert membership.prefix == "*"


def test_extended_person(session):
    person = ExtendedPerson(
        first_name="Hans",
        last_name="Maulwurf",
        academic_title="Dr.",
        profession="Politican",
        political_party="Democratic Party",
        parliamentary_group="Democrats",
        born="2000",
        phone="+1 234 56 78",
        phone_direct="+1 234 56 79",
        address="Street 1\nCity",
        notes="This is\na note."
    )
    session.add(person)
    session.flush()

    person = session.query(Person).one()
    assert isinstance(person, ExtendedPerson)
    assert person.type == 'extended'
    assert person.first_name == "Hans"
    assert person.last_name == "Maulwurf"
    assert person.academic_title == "Dr."
    assert person.profession == "Politican"
    assert person.political_party == "Democratic Party"
    assert person.parliamentary_group == "Democrats"
    assert person.born == "2000"
    assert person.phone == "+1 234 56 78"
    assert person.phone_direct == "+1 234 56 79"
    assert person.address == "Street 1\nCity"
    assert person.address_html == "<p>Street 1<br>City</p>"
    assert person.notes == "This is\na note."
    assert person.notes_html == "<p>This is<br>a note.</p>"
    assert person.is_hidden_from_public is None
    assert person.es_public is True

    person.is_hidden_from_public = True
    assert person.es_public is False


def test_extended_membership(session):
    agency = Agency(title='agency', name='agency')
    person = Person(first_name='a', last_name='person')
    session.add(agency)
    session.add(person)
    session.flush()

    session.add(
        ExtendedAgencyMembership(
            title="Director",
            order=12,
            since="2012",
            note="Interim",
            addition="Production",
            prefix="*",
            agency_id=agency.id,
            person_id=person.id
        )
    )
    session.flush()

    membership = session.query(AgencyMembership).one()
    assert isinstance(membership, ExtendedAgencyMembership)
    assert membership.type == 'extended'
    assert membership.title == "Director"
    assert membership.order == 12
    assert membership.since == "2012"
    assert membership.note == "Interim"
    assert membership.addition == "Production"
    assert membership.prefix == "*"
    assert membership.is_hidden_from_public is None
    assert membership.es_public is True
    assert membership.agency_id == agency.id
    assert membership.person_id == person.id
    assert membership.agency == agency
    assert membership.person == person
    assert agency.memberships.one() == membership
    assert person.memberships.one() == membership

    membership.is_hidden_from_public = True
    assert membership.es_public is False

    membership.is_hidden_from_public = False
    membership.agency.is_hidden_from_public = True
    assert membership.es_public is False

    membership.agency.is_hidden_from_public = False
    membership.person.is_hidden_from_public = True
    assert membership.es_public is False


def test_agency_move(session):
    # test URL template
    move = AgencyMove(None, None, None, None).for_url_template()
    assert move.direction == '{direction}'
    assert move.subject_id == '{subject_id}'
    assert move.target_id == '{target_id}'

    # test execute
    collection = ExtendedAgencyCollection(session)
    collection.add_root(title='2', id=2, order=2)
    collection.add_root(title='1', id=1, oder=1)
    parent = collection.add_root(title='3', id=3, order=3)
    collection.add(parent=parent, title='5', id=5, order=2)
    collection.add(parent=parent, title='4', id=4, order=1)

    def tree():
        return [
            [o.title, [c.title for c in o.children]]
            for o in collection.query().filter_by(parent_id=None)
        ]

    assert tree() == [['1', []], ['2', []], ['3', ['4', '5']]]

    AgencyMove(session, 1, 2, 'below').execute()
    assert tree() == [['2', []], ['1', []], ['3', ['4', '5']]]

    AgencyMove(session, 3, 1, 'above').execute()
    assert tree() == [['2', []], ['3', ['4', '5']], ['1', []]]

    AgencyMove(session, 5, 4, 'above').execute()
    session.flush()
    session.expire_all()
    assert tree() == [['2', []], ['3', ['5', '4']], ['1', []]]

    # invalid
    AgencyMove(session, 8, 9, 'above').execute()
    assert tree() == [['2', []], ['3', ['5', '4']], ['1', []]]

    AgencyMove(session, 5, 2, 'above').execute()
    session.expire_all()
    assert tree() == [['2', []], ['3', ['5', '4']], ['1', []]]


def test_membership_move(session):
    # test URL template
    move = AgencyMembershipMove(None, None, None, None).for_url_template()
    assert move.direction == '{direction}'
    assert move.subject_id == '{subject_id}'
    assert move.target_id == '{target_id}'

    # test execute
    agency_a = ExtendedAgency(title="A", name="a",)
    agency_b = ExtendedAgency(title="B", name="b",)
    person = ExtendedPerson(first_name="P", last_name="P")
    session.add(agency_a)
    session.add(agency_b)
    session.add(person)
    session.flush()

    agency_a.add_person(person.id, "X")
    agency_a.add_person(person.id, "Y")
    agency_a.add_person(person.id, "Z")
    agency_b.add_person(person.id, "K")

    x = agency_a.memberships.filter_by(title="X").one().id
    y = agency_a.memberships.filter_by(title="Y").one().id
    z = agency_a.memberships.filter_by(title="Z").one().id
    k = agency_b.memberships.one().id

    assert [m.title for m in agency_a.memberships] == ['X', 'Y', 'Z']

    AgencyMembershipMove(session, x, y, 'below').execute()
    assert [m.title for m in agency_a.memberships] == ['Y', 'X', 'Z']

    AgencyMembershipMove(session, z, y, 'above').execute()
    assert [m.title for m in agency_a.memberships] == ['Z', 'Y', 'X']

    # invalid
    AgencyMembershipMove(session, x, k, 'above').execute()
    assert [m.title for m in agency_a.memberships] == ['Z', 'Y', 'X']
