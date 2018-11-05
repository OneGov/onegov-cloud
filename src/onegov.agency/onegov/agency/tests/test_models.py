from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson


def test_extended_agency(agency_app):
    session = agency_app.session()

    agency = ExtendedAgency(
        title="Test Agency",
        name="test-agency",
        portrait="This is a test\nagency."
    )

    session.add(agency)
    session.flush()

    agency = session.query(ExtendedAgency).one()

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


def test_extended_person(session):
    person = ExtendedPerson(
        first_name="Hans",
        last_name="Maulwurf",
        academic_title="Dr.",
        profession="Politican",
        political_party="Democratic Party",
        year="2000",
        direct_phone="+1 234 56 78",
        address="Street 1\nCity",
        notes="This is\na note."
    )
    session.add(person)
    session.flush()

    person = session.query(ExtendedPerson).one()

    assert person.first_name == "Hans"
    assert person.last_name == "Maulwurf"
    assert person.academic_title == "Dr."
    assert person.profession == "Politican"
    assert person.political_party == "Democratic Party"
    assert person.year == "2000"
    assert person.direct_phone == "+1 234 56 78"
    assert person.address == "Street 1\nCity"
    assert person.address_html == "<p>Street 1<br>City</p>"
    assert person.notes == "This is\na note."
    assert person.notes_html == "<p>This is<br>a note.</p>"


def test_extended_person_membership_by_agency(session):
    agency_a = ExtendedAgency(title="A", name="a")
    agency_b = ExtendedAgency(title="B", name="b")
    agency_c = ExtendedAgency(title="C", name="c")
    agency_d = ExtendedAgency(title="D", name="d")
    person = ExtendedPerson(first_name="Hans", last_name="Maulwurf")
    session.add(agency_a)
    session.add(agency_b)
    session.add(agency_c)
    session.add(agency_d)
    session.add(person)
    session.flush()

    agency_b.add_person(person, 'l')
    agency_c.add_person(person, 'm')
    agency_a.add_person(person, 'n')
    agency_d.add_person(person, 'o')

    person = session.query(ExtendedPerson).one()
    assert [m.title for m in person.memberships_by_agency] == [
        'n', 'l', 'm', 'o'
    ]
