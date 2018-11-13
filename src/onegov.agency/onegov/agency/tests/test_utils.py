from io import BytesIO
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.utils import export_to_xlsx
from onegov.core.utils import module_path
from pytest import mark
from xlrd import open_workbook
from zipfile import ZipFile


class DummyRequest(object):
    def __init__(self, session):
        self.session = session

    def translate(self, text):
        return text.interpolate()


@mark.parametrize("file", [
    module_path('onegov.agency', 'tests/fixtures/organigram.png'),
])
def test_utils_xlsx(agency_app, file):
    session = agency_app.session()

    with open(file, 'rb') as f:
        organigram = BytesIO(f.read())

    people = ExtendedPersonCollection(session)
    quimby = people.add(
        salutation="Mr.",
        academic_title="Dr.",
        first_name="Joe",
        last_name="Quimby",
        profession="Politician",
        political_party="Republican Party",
        born="1970",
        address="Fakestreet 1, Springfield",
        phone="+1 234 5678",
        phone_direct="+1 234 5679",
        email="joe.quimby@springfield.gov",
        website="https://springfield.gov/joe.quimby",
        notes="Currently Major."
    )

    agencies = ExtendedAgencyCollection(session)
    root = agencies.add_root(title="Communal")
    gov = agencies.add(
        parent=root,
        title="Government",
        portrait="2016/2019",
        organigram_file=organigram,
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    gov.add_person(
        quimby.id,
        "Major",
        since="2001",
        prefix="*",
        addition="Second term",
        note="Suspicion of corruption",
    )
    dmv = agencies.add(
        parent=root,
        title="Department of Motor Vehicles",
    )

    output = BytesIO()
    export_to_xlsx(DummyRequest(session), output)
    output.seek(0)
    book = open_workbook(file_contents=output.read())
    assert book.nsheets == 4

    sheet = book.sheet_by_name('Agencies')
    assert sheet.ncols == 5
    assert sheet.nrows == 4

    assert sheet.cell(0, 0).value == 'ID'
    assert sheet.cell(0, 1).value == 'Suborganizations'
    assert sheet.cell(0, 2).value == 'Title'
    assert sheet.cell(0, 3).value == 'Portrait'
    assert sheet.cell(0, 4).value == 'Export Fields'

    assert sheet.cell(1, 0).value == str(root.id)
    assert sheet.cell(1, 1).value == f'{dmv.id}, {gov.id}'
    assert sheet.cell(1, 2).value == 'Communal'
    assert sheet.cell(1, 3).value == ''
    assert sheet.cell(1, 4).value == ''

    assert sheet.cell(2, 0).value == str(dmv.id)
    assert sheet.cell(2, 1).value == ''
    assert sheet.cell(2, 2).value == 'Department of Motor Vehicles'
    assert sheet.cell(2, 3).value == ''
    assert sheet.cell(2, 4).value == ''

    assert sheet.cell(3, 0).value == str(gov.id)
    assert sheet.cell(3, 1).value == ''
    assert sheet.cell(3, 2).value == 'Government'
    assert sheet.cell(3, 3).value == '2016/2019'
    assert sheet.cell(3, 4).value == 'membership.title, person.title'

    sheet = book.sheet_by_name('Organigrams')
    assert sheet.ncols == 2
    assert sheet.nrows == 2

    assert sheet.cell(0, 0).value == 'Agency'
    assert sheet.cell(0, 1).value == 'Organigram'

    assert sheet.cell(1, 0).value == str(gov.id)
    assert sheet.cell(1, 1).value == ''

    sheet = book.sheet_by_name('People')
    assert sheet.ncols == 14
    assert sheet.nrows == 2

    assert sheet.cell(0, 0).value == 'ID'
    assert sheet.cell(0, 1).value == 'Salutation'
    assert sheet.cell(0, 2).value == 'Academic Title'
    assert sheet.cell(0, 3).value == 'First name'
    assert sheet.cell(0, 4).value == 'Last name'
    assert sheet.cell(0, 5).value == 'Profession'
    assert sheet.cell(0, 6).value == 'Political Party'
    assert sheet.cell(0, 7).value == 'Born'
    assert sheet.cell(0, 8).value == 'Address'
    assert sheet.cell(0, 9).value == 'Phone'
    assert sheet.cell(0, 10).value == 'Direct Phone'
    assert sheet.cell(0, 11).value == 'Email'
    assert sheet.cell(0, 12).value == 'Website'
    assert sheet.cell(0, 13).value == 'Notes'

    assert sheet.cell(1, 0).value == '0'
    assert sheet.cell(1, 1).value == 'Mr.'
    assert sheet.cell(1, 2).value == 'Dr.'
    assert sheet.cell(1, 3).value == 'Joe'
    assert sheet.cell(1, 4).value == 'Quimby'
    assert sheet.cell(1, 5).value == 'Politician'
    assert sheet.cell(1, 6).value == 'Republican Party'
    assert sheet.cell(1, 7).value == '1970'
    assert sheet.cell(1, 8).value == 'Fakestreet 1, Springfield'
    assert sheet.cell(1, 9).value == '+1 234 5678'
    assert sheet.cell(1, 10).value == '+1 234 5679'
    assert sheet.cell(1, 11).value == 'joe.quimby@springfield.gov'
    assert sheet.cell(1, 12).value == 'https://springfield.gov/joe.quimby'
    assert sheet.cell(1, 13).value == 'Currently Major.'

    sheet = book.sheet_by_name('Memberships')
    assert sheet.ncols == 7
    assert sheet.nrows == 2

    assert sheet.cell(0, 0).value == 'Agency'
    assert sheet.cell(0, 1).value == 'Person'
    assert sheet.cell(0, 2).value == 'Title'
    assert sheet.cell(0, 3).value == 'Since'
    assert sheet.cell(0, 4).value == 'Prefix'
    assert sheet.cell(0, 5).value == 'Addition'
    assert sheet.cell(0, 6).value == 'Note'

    assert sheet.cell(1, 0).value == str(gov.id)
    assert sheet.cell(1, 1).value == '0'
    assert sheet.cell(1, 2).value == 'Major'
    assert sheet.cell(1, 3).value == '2001'
    assert sheet.cell(1, 4).value == '*'
    assert sheet.cell(1, 5).value == 'Second term'
    assert sheet.cell(1, 6).value == 'Suspicion of corruption'

    organigram.seek(0)
    output.seek(0)
    zip = ZipFile(output)
    assert zip.read('xl/media/image1.png') == organigram.read()
