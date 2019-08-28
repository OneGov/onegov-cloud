from io import BytesIO

from xlrd import open_workbook

from onegov.agency.excel_export import export_person_xlsx, column_mapper, \
    extract_person_data
from onegov.agency.models import ExtendedPerson, ExtendedAgency


def test_excel_export(session):
    agency_x = ExtendedAgency(title='Agency X', name='x')
    agency_y = ExtendedAgency(title='Agency Y', name='y')

    person_a = ExtendedPerson(
        salutation='Herr',
        last_name='A',
        first_name='B',
        email='a@b.com',
        phone='+4444',
        phone_direct='+4445',
        born='01.01.2019',
        profession='Funktionär',
        function='Funktionär',
        political_party='PDS',
        parliamentary_group='Parlamentarische Gruppe',
        website='a.com',
        address='Funktionärstrasse 5',
        notes='Notizen',
    )

    person_aa = ExtendedPerson(
        last_name='A',
        first_name='A',
    )

    person_ac = ExtendedPerson(
        last_name='A',
        first_name='C',
    )

    person_b = ExtendedPerson(
        salutation='Herr',
        last_name='B',
        first_name='C',
        email='b@c.com',
        phone='+4444',
        phone_direct='+4445',
        born='01.01.2019',
        profession='Funktionär',
        function='Funktionär',
        political_party='PDS',
        parliamentary_group='Parlamentarische Gruppe',
        website='a.com',
        address='Funktionärstrasse 5',
        notes='Notizen',
    )

    session.add_all(
        [agency_x, agency_y, person_a, person_b, person_aa, person_ac])
    session.flush()

    agency_x.add_person(person_a.id, 'a in x')
    agency_x.add_person(person_b.id, 'b in x')
    agency_y.add_person(person_a.id, 'a in y')

    # Test data extraction
    write_out = extract_person_data(session)
    assert len(write_out) == 4

    file = export_person_xlsx(session)
    workbook = open_workbook(file_contents=file.read())
    sheet = workbook.sheet_by_name('Personen')
    titles = [cell.value for cell in sheet.row(0)]
    # Test titles
    assert titles == list(column_mapper.values())

    # Test ordering in sheet sorted by last_name and first_name
    ix_ln = list(column_mapper.values()).index('Nachname')
    ix_fn = list(column_mapper.values()).index('Vorname')

    order = [
        f"{row[ix_ln].value}{row[ix_fn].value}" for row in sheet.get_rows()]
    assert order == ['NachnameVorname', 'AA', 'AB', 'AC', 'BC']

    # Test a row
    row_num = 2
    for ix, (class_attrib, col_name) in enumerate(column_mapper.items()):
        if class_attrib == 'memberships':
            assert sheet.row(row_num)[ix].value == \
                   f"{agency_x.title} - a in x\n{agency_y.title} - a in y"
        else:
            assert sheet.row(row_num)[ix].value == \
                   getattr(person_a, class_attrib)
