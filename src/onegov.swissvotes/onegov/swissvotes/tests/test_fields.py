from cgi import FieldStorage
from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.form import Form
from onegov.swissvotes.fields import PolicyAreaField
from onegov.swissvotes.fields import SwissvoteDatasetField
from onegov.swissvotes.models import ColumnMapper
from psycopg2.extras import NumericRange
from xlsxwriter.workbook import Workbook


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_swissvotes_dataset_field():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')

    assert field()
    assert len(field.validators) == 2

    # Corrupt file type
    field_storage = FieldStorage()
    field_storage.file = BytesIO(b'Test')
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    assert "Not a valid XLSX file." in field.errors

    # Empty XLSX/sheet
    file = BytesIO()
    workbook = Workbook(file)
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    assert "No data." in field.errors

    # Missing columns
    mapper = ColumnMapper()
    columns = [value for value in mapper.columns.values() if value != 'anzahl']

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet()
    worksheet.write_row(0, 0, columns)
    worksheet.write_row(1, 0, columns)
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    errors = [error.interpolate() for error in field.errors]
    assert 'Some columns are missing: anzahl.' in errors

    # Wrong types and missing values
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet()
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(1, 0, [
        '',  # anr / NUMERIC
        '',  # datum / DATE
        '',  # legislatur / INTEGER
        '',  # legisjahr / INT4RANGE
        '',  # jahrzent / INT4RANGE
        '',  # titel / TEXT
    ])
    worksheet.write_row(2, 0, [
        None,  # anr / NUMERIC
        None,  # datum / DATE
        None,  # legislatur / INTEGER
        None,  # legisjahr / INT4RANGE
        None,  # jahrzent / INT4RANGE
        None,  # titel / TEXT
    ])
    worksheet.write_row(3, 0, [
        'x',  # anr / NUMERIC
        'x',  # datum / DATE
        'x',  # legislatur / INTEGER
        'x',  # legisjahr / INT4RANGE
        'x',  # jahrzent / INT4RANGE
        'x',  # titel / TEXT
    ])
    worksheet.write_row(4, 0, [
        1,  # anr / NUMERIC
        1,  # datum / DATE
        1,  # legislatur / INTEGER
        1,  # legisjahr / INT4RANGE
        1,  # jahrzent / INT4RANGE
        1,  # titel / TEXT
    ])
    worksheet.write_row(5, 0, [
        1.1,  # anr / NUMERIC
        1.1,  # datum / DATE
        1.1,  # legislatur / INTEGER
        1.1,  # legisjahr / INT4RANGE
        1.1,  # jahrzent / INT4RANGE
        1.1,  # titel / TEXT
    ])
    worksheet.write_row(5, 0, [
        date(2018, 12, 12),  # anr / NUMERIC
        date(2018, 12, 12),  # datum / DATE
        date(2018, 12, 12),  # legislatur / INTEGER
        date(2018, 12, 12),  # legisjahr / INT4RANGE
        date(2018, 12, 12),  # jahrzent / INT4RANGE
        date(2018, 12, 12),  # titel / TEXT
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    error = [error.interpolate() for error in field.errors][0]

    assert "1:anr ∅" in error
    assert "1:datum ∅" in error
    assert "1:legislatur ∅" in error
    assert "1:legisjahr ∅" in error
    assert "1:jahrzehnt ∅" in error
    assert "1:titel_off_d ∅" in error
    assert "1:titel_off_f ∅" in error
    assert "1:titel_kurz_d ∅" in error
    assert "1:titel_kurz_f ∅" in error

    assert "1:anzahl ∅" in error
    assert "1:rechtsform ∅" in error

    assert "2:anr ∅" in error
    assert "2:datum ∅" in error
    assert "2:legislatur ∅" in error
    assert "2:legisjahr ∅" in error
    assert "2:jahrzehnt ∅" in error
    assert "2:titel_off_d ∅" in error
    assert "2:titel_off_f ∅" in error
    assert "2:titel_kurz_d ∅" in error
    assert "2:titel_kurz_f ∅" in error

    assert "3:anr 'x' ≠ numeric(8, 2)" in error
    assert "3:datum 'x' ≠ date" in error
    assert "3:legislatur 'x' ≠ integer" in error
    assert "3:legisjahr 'x' ≠ int4range" in error
    assert "3:jahrzehnt 'x' ≠ int4range" in error

    assert "4:legisjahr '1' ≠ int4range" in error
    assert "4:jahrzehnt '1' ≠ int4range" in error

    assert "5:legisjahr '43446' ≠ int4range" in error
    assert "5:jahrzehnt '43446' ≠ int4range" in error

    # OK
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet()
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        '1',  # legislatur / INTEGER
        '2004-2008',  # legisjahr / INT4RANGE
        '2000-2009',  # jahrzent / INT4RANGE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
        '2',  # anzahl / INTEGER
        '3',  # rechtsform
    ])
    worksheet.write_row(2, 0, [
        100.2,  # anr / NUMERIC
        date(2008, 2, 1),  # datum / DATE
        1,  # legislatur / INTEGER
        '2004-2008',  # legisjahr / INT4RANGE
        '2000-2009',  # jahrzent / INT4RANGE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
        2,  # anzahl / INTEGER
        3,  # rechtsform
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    field.process(DummyPostData({'dataset': field_storage}))

    assert field.validate(form)
    assert not field.errors

    assert field.data[0].bfs_number == Decimal('100.10')
    assert field.data[0].date == date(2008, 2, 1)
    assert field.data[0].legislation_number == 1
    assert field.data[0].legislation_decade == NumericRange(2004, 2008)
    assert field.data[0].decade == NumericRange(2000, 2009)
    assert field.data[0].title_de == 'titel_off_d'
    assert field.data[0].title_fr == 'titel_off_f'
    assert field.data[0].short_title_de == 'titel_kurz_d'
    assert field.data[0].short_title_fr == 'titel_kurz_f'
    assert field.data[0].keyword == 'stichwort'
    assert field.data[0].votes_on_same_day == 2
    assert field.data[0]._legal_form == 3

    assert field.data[1].bfs_number == Decimal('100.20')
    assert field.data[1].date == date(2008, 2, 1)
    assert field.data[1].legislation_number == 1
    assert field.data[1].legislation_decade == NumericRange(2004, 2008)
    assert field.data[1].decade == NumericRange(2000, 2009)
    assert field.data[1].title_de == 'titel_off_d'
    assert field.data[1].title_fr == 'titel_off_f'
    assert field.data[1].short_title_de == 'titel_kurz_d'
    assert field.data[1].short_title_fr == 'titel_kurz_f'
    assert field.data[1].keyword == 'stichwort'
    assert field.data[1].votes_on_same_day == 2
    assert field.data[1]._legal_form == 3


def test_policy_area_field():
    form = Form()
    field = PolicyAreaField(choices=[])
    field = field.bind(form, 'policy_area')

    html = field()
    assert 'class="policy-selector"' in html
    assert 'data-no-matches-text="No results match"' in html
    assert 'data-placehoder-text="Select Some Options"' in html
    assert 'data-tree="[]"' in html
    assert 'multiple' in html

    field.tree = [
        {
            'label': 'A',
            'value': 'a',
            'children': [
                {
                    'label': 'A.1',
                    'value': 'a1',
                    'children': []
                },
                {
                    'label': 'A.2',
                    'value': 'a2',
                    'children': [
                        {
                            'label': 'A.2.1',
                            'value': 'a21',
                            'children': []
                        }
                    ]
                }
            ],
        },
        {
            'label': 'B',
            'value': 'b',
            'children': []
        }
    ]
    assert field.choices == [
        ('a', 'A'), ('a1', 'A.1'), ('a2', 'A.2'), ('a21', 'A.2.1'), ('b', 'B')
    ]

    field.process(DummyPostData({'policy_area': ['a2', 'b']}))
    assert field.data == ['a2', 'b']
    assert field.tree == [
        {
            'label': 'A',
            'value': 'a',
            'checked': False,
            'expanded': True,
            'children': [
                {
                    'label': 'A.1',
                    'value': 'a1',
                    'checked': False,
                    'expanded': False,
                    'children': [],
                },
                {
                    'label': 'A.2',
                    'value': 'a2',
                    'checked': True,
                    'expanded': False,
                    'children': [
                        {
                            'label': 'A.2.1',
                            'value': 'a21',
                            'checked': False,
                            'expanded': False,
                            'children': [],
                        }
                    ],
                }
            ],
        },
        {
            'label': 'B',
            'value': 'b',
            'checked': True,
            'expanded': False,
            'children': [],
        }
    ]
