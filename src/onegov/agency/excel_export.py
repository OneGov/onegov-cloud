from __future__ import annotations

from collections import OrderedDict
from io import BytesIO

from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedPerson
from xlsxwriter.workbook import Workbook
from decimal import Decimal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


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


def extract_person_data(session: Session) -> list[dict[str, object]]:
    collection = ExtendedPersonCollection(session)
    collection.exclude_hidden = False
    query = collection.query().outerjoin(ExtendedPerson.memberships)

    write_out = []

    for person in query:
        out_dict: dict[str, object] = OrderedDict()
        memberships = '\n'.join(
            f'{m.agency.title} - {m.title}' for m in person.memberships
        )
        for col in column_mapper.keys():
            if col == 'memberships':
                out_dict[col] = memberships
            else:
                out_dict[col] = getattr(person, col)
        write_out.append(out_dict)
    return write_out


def export_person_xlsx(session: Session) -> BytesIO:
    """ Exports every person with their memberships in xlsx format. """
    file = BytesIO()
    workbook = Workbook(file, {'default_date_format': 'dd.mm.yyyy'})
    worksheet = workbook.add_worksheet('Personen')
    worksheet.write_row(0, 0, column_mapper.values())

    write_out = extract_person_data(session)

    for row, entry in enumerate(write_out, start=1):
        for column, value in enumerate(entry.values()):
            if value is None:
                worksheet.write_string(row, column, '')
            elif isinstance(value, str):
                worksheet.write_string(row, column, value)
            elif isinstance(value, (int, Decimal)):
                worksheet.write_number(row, column, value)
            else:
                raise NotImplementedError()

    workbook.close()
    file.seek(0)
    return file
