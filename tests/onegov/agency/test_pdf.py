from datetime import date
from datetime import timedelta
from freezegun import freeze_time
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg
from onegov.pdf.utils import extract_pdf_info
from sedate import utcnow


def test_pdf_page_break_on_level(session):
    pass


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
    canton = agencies.add_root(title="Kanton")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="Portrait NR",
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

    # test single agency with toc break on level 1
    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[],
        page_break_on_level=1
    )
    pages, pdf = extract_pdf_info(file)
    assert pages == 2
    assert "Staatskalender" in pdf
    assert "1 Bundesbehörden" in pdf
    assert "1.1 Nationalrat" in pdf
    assert "1.2 Ständerat" in pdf
    assert "1 Bundesbehörden" in pdf
    assert "1.1 Nationalrat" in pdf
    assert "Portrait NR" in pdf
    assert "Mitglied von Zug" in pdf
    assert "Aeschi Thomas" in pdf
    assert "SVP" not in pdf
    assert "1.2 Ständerat" in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Joachim, Eder, FDP" in pdf

    # test page break on level 2
    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[],
        page_break_on_level=2
    )
    pages, pdf = extract_pdf_info(file)
    assert pages == 3
    assert "1.2 Ständerat" in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Joachim, Eder, FDP" in pdf

    # test page break on level 1 with succeeding headers
    file = AgencyPdfDefault.from_agencies(
        agencies=[bund, canton],
        title="Staatskalender",
        toc=True,
        exclude=[],
        page_break_on_level=1
    )
    pages, pdf = extract_pdf_info(file)
    assert pages == 3
    assert "2 Kanton" in pdf
    assert "2 Kanton" in pdf

    file = AgencyPdfDefault.from_agencies(
        agencies=[nr, sr],
        title="Staatskalender",
        toc=False,
        exclude=['political_party']
    )
    pages, pdf = extract_pdf_info(file)
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
    pages, pdf = extract_pdf_info(file)
    assert pages == 1
    assert 'Nationalrat' in pdf
    assert 'Portrait NR' in pdf
    assert 'Mitglied von Zug' in pdf
    assert 'Aeschi Thomas' in pdf


def test_agency_pdf_default_hidden_by_access(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        access='private'
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
        access='private'
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
    sr.add_person(eder.id, "Ständerat für Zug", access='private')

    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=False,
        exclude=[]
    )
    _, pdf = extract_pdf_info(file)
    assert "Bundesrat" not in pdf
    assert "Nationalrat" in pdf
    assert "Ständerat" in pdf
    assert "Mitglied von Zug" not in pdf
    assert "Aeschi" not in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Eder" not in pdf


def test_agency_pdf_default_hidden_by_publication(session):
    then = utcnow() + timedelta(days=7)

    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        publication_start=then
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
        publication_start=utcnow() + timedelta(days=7)
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
    sr.add_person(eder.id, "Ständerat für Zug", publication_start=then)

    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=False,
        exclude=[]
    )
    _, pdf = extract_pdf_info(file)
    assert "Bundesrat" not in pdf
    assert "Nationalrat" in pdf
    assert "Ständerat" in pdf
    assert "Mitglied von Zug" not in pdf
    assert "Aeschi" not in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Eder" not in pdf


@freeze_time("2018-01-01")
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
        portrait="Portrait NR",
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
    assert extract_pdf_info(file) == (
        2,
        f'Staatskalender\n'
        f'1 Bundesbehörden       2\n'
        f'1.1 Nationalrat        2\n'
        f'1.2 Ständerat          2\n'
        f'Druckdatum: {date.today():%d.%m.%Y} 1\n'
        f'\n'
        f'Staatskalender Kanton Appenzell Ausserrhoden\n'
        f'1 Bundesbehörden\n'
        f'1.1 Nationalrat\n'
        f'Portrait NR\n'
        f'Mitglied von AR                        Aeschi Thomas\n'
        f'1.2 Ständerat\n'
        f'Joachim, Eder, FDP\n'
        f'Druckdatum: {date.today():%d.%m.%Y}                               2'
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
        portrait="Portrait NR",
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
    assert extract_pdf_info(file) == (
        2,
        f'Staatskalender\n'
        f'1 Bundesbehörden 2\n'
        f'1.1 Nationalrat  2\n'
        f'1.2 Ständerat    2\n'
        f'\n'
        f'1 Bundesbehörden\n'
        f'1.1 Nationalrat\n'
        f'Portrait NR\n'
        f'Mitglied von Zug       Aeschi Thomas\n'
        f'1.2 Ständerat\n'
        f'Joachim, Eder, FDP\n'
        f'Staatskalender\n'
        f'Druckdatum: {date.today():%d.%m.%Y}               2'
    )
