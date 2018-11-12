from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.pdf import DefaultAgencyPdf
from PyPDF2 import PdfFileReader


def test_default_agency_pdf(session):
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

    file = DefaultAgencyPdf.from_agencies(
        agencies=[bund],
        author="Kanton Zug",
        title="Staatskalender Zug",
        toc=True,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Kanton Zug" in pdf
    assert "Staatskalender Zug" in pdf
    assert "1 Bundesbehörden" in pdf
    assert "1.1 Nationalrat" in pdf
    assert "1.2 Ständerat" in pdf
    assert "2016/2019" in pdf
    assert "Mitglied von Zug" in pdf
    assert "Aeschi Thomas" in pdf
    assert "SVP" not in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Joachim, Eder, FDP" in pdf

    file = DefaultAgencyPdf.from_agencies(
        agencies=[nr, sr],
        author="Kanton Zug",
        title="Staatskalender Zug",
        toc=False,
        exclude=['political_party']
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Kanton Zug" in pdf
    assert "Staatskalender Zug" in pdf
    assert "Bundesbehörden" not in pdf
    assert "FDP" not in pdf
    assert "SVP" not in pdf
