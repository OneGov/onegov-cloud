from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg
from PyPDF2 import PdfFileReader


def test_agency_pdf_default(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        political_party="SVP"
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim",
        political_party="FDP"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="2016/2019",
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=[
            'person.first_name',
            'person.last_name',
            'person.political_party',
        ]
    )

    nr.add_person(aeschi.id, "Mitglied von Zug")
    sr.add_person(eder.id, "Ständerat für Zug")

    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Staatskalender" in pdf
    assert "1 Bundesbehörden" in pdf
    assert "1.1 Nationalrat" in pdf
    assert "1.2 Ständerat" in pdf
    assert "2016/2019" in pdf
    assert "Mitglied von Zug" in pdf
    assert "Aeschi Thomas" in pdf
    assert "SVP" not in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Joachim, Eder, FDP" in pdf

    file = AgencyPdfDefault.from_agencies(
        agencies=[nr, sr],
        title="Staatskalender",
        toc=False,
        exclude=['political_party']
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Staatskalender" in pdf
    assert "Bundesbehörden" not in pdf
    assert "FDP" not in pdf
    assert "SVP" not in pdf

    file = AgencyPdfDefault.from_agencies(
        agencies=[nr],
        title="Nationalrat",
        toc=False,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert pdf == (
        '1\nNationalrat\n2016/2019\nMitglied von Zug\nAeschi Thomas\n'
    )


def test_agency_pdf_default_hidden(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        is_hidden_from_public=True
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    agencies.add(
        parent=bund,
        title="Bundesrat",
        is_hidden_from_public=True
    )
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        export_fields=['membership.title', 'person.title']
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=['membership.title', 'person.title']
    )

    nr.add_person(aeschi.id, "Mitglied von Zug")
    sr.add_person(eder.id, "Ständerat für Zug", is_hidden_from_public=True)

    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=False,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Bundesrat" not in pdf
    assert "Nationalrat" in pdf
    assert "Ständerat" in pdf
    assert "Mitglied von Zug" not in pdf
    assert "Aeschi" not in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Eder" not in pdf


def test_agency_pdf_ar(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        political_party="SVP"
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim",
        political_party="FDP"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="2016/2019",
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=[
            'person.first_name',
            'person.last_name',
            'person.political_party',
        ]
    )

    nr.add_person(aeschi.id, "Mitglied von AR")
    sr.add_person(eder.id, "Ständerat für AR")

    file = AgencyPdfAr.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert pdf == (
        '© 2018 Kanton Appenzell Ausserrhoden\n1\n'
        'Staatskalender\n'
        '2\n1 Bundesbehörden\n'
        '2\n1.1 Nationalrat\n'
        '3\n1.2 Ständerat\n\n'
        'Staatskalender\n29.11.2018\n'
        '© 2018 Kanton Appenzell Ausserrhoden\n2\n'
        '1 Bundesbehörden\n'
        '1.1 Nationalrat\n'
        '2016/2019\n'
        'Mitglied von AR\nAeschi Thomas\n\n'
        'Staatskalender\n29.11.2018\n'
        '© 2018 Kanton Appenzell Ausserrhoden\n3\n'
        '1.2 Ständerat\n'
        'Joachim, Eder, FDP\n'
    )


def test_agency_pdf_zg(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        political_party="SVP"
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim",
        political_party="FDP"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="2016/2019",
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=[
            'person.first_name',
            'person.last_name',
            'person.political_party',
        ]
    )

    nr.add_person(aeschi.id, "Mitglied von Zug")
    sr.add_person(eder.id, "Ständerat für Zug")

    file = AgencyPdfZg.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert pdf == (
        'Staatskalender\n'
        '2\n1 Bundesbehörden\n'
        '2\n1.1 Nationalrat\n'
        '3\n1.2 Ständerat\n\n'
        'Staatskalender\nDruckdatum: 29.11.2018\n2\n'
        '1 Bundesbehörden\n'
        '1.1 Nationalrat\n'
        '2016/2019\n'
        'Mitglied von Zug\nAeschi Thomas\n\n'
        'Staatskalender\nDruckdatum: 29.11.2018\n3\n'
        '1.2 Ständerat\nJoachim, Eder, FDP\n'
    )
