from collections import OrderedDict
from io import BytesIO

from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedPerson
from xlsxwriter.workbook import Workbook
from decimal import Decimal

column_mapper = OrderedDict(
    salutation='Anrede',
    academic_title='Akademischer Titel',
    last_name='Nachname',
    first_name='Vorname',
    email='Email',
    phone='Tel.',
    phone_direct='Tel. direkt.',
    born='Geburtsdatum',
    profession='Beruf',
    function='Funktion',
    political_party='Partei',
    parliamentary_group='Parlamentarische Gruppe',
    website='Website',
    location_address='Standortadresse',
    location_code_city='Standort Postleitzahl und Ort',
    postal_address='Postadresse',
    postal_code_city='Postleitzahl und Ort',
    notes='Notizen',
    memberships='Mitgliedschaften'
)


def extract_person_data(session):
    collection = ExtendedPersonCollection(session)
    collection.exclude_hidden = False
    query = collection.query().outerjoin(ExtendedPerson.memberships)

    write_out = []

    for person in query:
        out_dict = OrderedDict()
        memberships = "\n".join(
            (f"{m.agency.title} - {m.title}" for m in person.memberships)
        )
        for col in column_mapper.keys():
            if col == 'memberships':
                out_dict[col] = memberships
            else:
                out_dict[col] = getattr(person, col)
        write_out.append(out_dict)
    return write_out


def export_person_xlsx(session):
    """ Exports every person with their memberships in xlsx format. """
    file = BytesIO()
    workbook = Workbook(file, {'default_date_format': 'dd.mm.yyyy'})
    worksheet = workbook.add_worksheet('Personen')
    worksheet.write_row(0, 0, column_mapper.values())

    write_out = extract_person_data(session)

    row = 0
    for entry in write_out:
        row += 1
        for col_ix, value in enumerate(entry.values()):
            if value is None:
                worksheet.write_string(row, col_ix, '')
            elif isinstance(value, str):
                worksheet.write_string(row, col_ix, value)
            elif isinstance(value, int) or isinstance(value, Decimal):
                worksheet.write_number(row, col_ix, value)
            else:
                raise NotImplementedError()

    workbook.close()
    file.seek(0)
    return file
