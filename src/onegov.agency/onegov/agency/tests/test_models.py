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
    assert agency.state is None
    assert agency.pdf is None
    assert agency.pdf_file is None
    assert agency.trait == 'agency'
    assert agency.proxy().id == agency.id

    agency.pdf_file = b'PDF'
    assert agency.pdf_file.read() == b'PDF'
    assert agency.pdf_file.filename == 'test-agency.pdf'
    assert agency.pdf.name == 'test-agency.pdf'

    agency.pdf_file = b'PDF2'
    assert agency.pdf_file.read() == b'PDF2'
    assert agency.pdf_file.filename == 'test-agency.pdf'
    assert agency.pdf.name == 'test-agency.pdf'


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
    assert person.born == "2000"
    assert person.phone == "+1 234 56 78"
    assert person.phone_direct == "+1 234 56 79"
    assert person.address == "Street 1\nCity"
    assert person.address_html == "<p>Street 1<br>City</p>"
    assert person.notes == "This is\na note."
    assert person.notes_html == "<p>This is<br>a note.</p>"


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
    assert membership.agency_id == agency.id
    assert membership.person_id == person.id
    assert membership.agency == agency
    assert membership.person == person
    assert agency.memberships.one() == membership
    assert person.memberships.one() == membership
