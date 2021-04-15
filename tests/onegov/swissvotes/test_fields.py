from cgi import FieldStorage
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest

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


def test_swissvotes_dataset_field_validators():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')
    assert field()
    assert len(field.validators) == 2


def test_swissvotes_dataset_field_corrupt():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = BytesIO(b'Test')
    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    assert "Not a valid XLSX file." in field.errors


def test_swissvotes_dataset_field_missing_sheet_data():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')

    file = BytesIO()
    workbook = Workbook(file)
    workbook.add_worksheet('CITATION')
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    # It raises for the first sheet it cant find
    assert not field.validate(form)
    assert "Sheet DATA is missing." in field.errors


def test_swissvotes_dataset_field_missing_sheet_citations():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')

    file = BytesIO()
    workbook = Workbook(file)
    workbook.add_worksheet('DATA')
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    # It raises for the first sheet it cant find
    assert not field.validate(form)
    assert "Sheet CITATION is missing." in field.errors


def test_swissvotes_dataset_field_empty():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')

    file = BytesIO()
    workbook = Workbook(file)
    workbook.add_worksheet('DATA')
    workbook.add_worksheet('CITATION')
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    assert "No data." in field.errors


def test_swissvotes_dataset_field_missing_columns():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')
    mapper = ColumnMapper()
    columns = [
        value for value in mapper.columns.values()
        if value != 'anzahl'
    ]

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    workbook.add_worksheet('CITATION')

    worksheet.write_row(0, 0, columns)
    worksheet.write_row(1, 0, columns)
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    errors = [error.interpolate() for error in field.errors]

    assert 'Some columns are missing: anzahl.' in errors


@pytest.mark.skip('Needs rework to defined wanted error messages')
def test_swissvotes_dataset_field_types_and_missing_values():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')
    mapper = ColumnMapper()
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    workbook.add_worksheet('CITATION')
    worksheet.write_row(0, 0, mapper.columns.values())
    for row, content in enumerate(('', None, 'x', 1, 1.1, date(2018, 12, 12))):
        worksheet.write_row(row + 1, 0, [
            content,  # anr / NUMERIC
            content,  # datum / DATE
            content,  # short_title_de / TEXT
            content,  # short_title_fr / TEXT
            content,  # title_de / TEXT
            content,  # title_fr / TEXT
            content,  # stichwort / TEXT
            content,  # swissvoteslink / TEXT
            content,  # anzahl / INTEGER
            content,  # rechtsform / INTEGER
            content,  # anneepolitique / TEXT
            content,  # bkchrono-de / TEXT
            content,  # bkchrono-fr / TEXT
            content,  # d1e1 / NUMERIC
            content,  # d1e2 / NUMERIC
            content,  # d1e3 / NUMERIC
            content,  # d2e1 / NUMERIC
            content,  # d2e2 / NUMERIC
            content,  # d2e3 / NUMERIC
            content,  # d3e1 / NUMERIC
            content,  # d3e2 / NUMERIC
            content,  # d3e3 / NUMERIC
            content,  # dep
            content,  # br-pos
            content,  # legislatur / INTEGER
            content,  # legisjahr / INT4RANGE
            'xxx'     # avoid being ignore because all cells are empty
        ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    error = [error.interpolate() for error in field.errors][0]

    assert "2:anr ∅" in error
    assert "2:datum ∅" in error
    assert "2:legislatur ∅" in error
    assert "2:legisjahr ∅" in error
    assert "2:titel_off_d ∅" in error
    assert "2:titel_off_f ∅" in error
    assert "2:titel_kurz_d ∅" in error
    assert "2:titel_kurz_f ∅" in error

    assert "2:anzahl ∅" in error
    assert "2:rechtsform ∅" in error

    assert "3:anr ∅" in error
    assert "3:datum ∅" in error
    assert "3:legislatur ∅" in error
    assert "3:legisjahr ∅" in error
    assert "3:titel_off_d ∅" in error
    assert "3:titel_off_f ∅" in error
    assert "3:titel_kurz_d ∅" in error
    assert "3:titel_kurz_f ∅" in error

    assert "4:anr 'x' ≠ numeric(8, 2)" in error
    assert "4:datum 'x' ≠ date" in error
    assert "4:legislatur 'x' ≠ integer" in error
    assert "4:legisjahr 'x' ≠ int4range" in error

    assert "5:legisjahr '1' ≠ int4range" in error

    assert "6:legisjahr '1' ≠ int4range" in error

    assert "7:legisjahr '43446' ≠ int4range" in error


@pytest.mark.skip('Needs rework to defined wanted error messages')
def test_swissvotes_dataset_field_all_okay():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')
    mapper = ColumnMapper()
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    workbook.add_worksheet('CITATION')
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
        'link',  # swissvoteslink / TEXT
        '2',  # anzahl / INTEGER
        '3',  # rechtsform / INTEGER
        '',  # anneepolitique / TEXT
        '',  # bkchrono-de / TEXT
        '',  # bkchrono-fr / TEXT
        '13',  # d1e1 / NUMERIC
        '',  # d1e2 / NUMERIC
        '',  # d1e3 / NUMERIC
        '12',  # d2e1 / NUMERIC
        '12.6',  # d2e2 / NUMERIC
        '',  # d2e3 / NUMERIC
        '12',  # d3e1 / NUMERIC
        '12.5',  # d3e2 / NUMERIC
        '12.55',  # d3e3 / NUMERIC
        '',  # dep
        '',  # br-pos
        '1',  # legislatur / INTEGER
        '2004-2008',  # legisjahr / INT4RANGE
    ])
    worksheet.write_row(2, 0, [
        100.2,  # anr / NUMERIC
        date(2008, 2, 1),  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
        'link',  # swissvoteslink / TEXT
        2,  # anzahl / INTEGER
        3,  # rechtsform
        '',  # anneepolitique / TEXT
        '',  # bkchrono-de / TEXT
        '',  # bkchrono-fr / TEXT
        '13',  # d1e1 / NUMERIC
        '',  # d1e2 / NUMERIC
        '',  # d1e3 / NUMERIC
        '12',  # d2e1 / NUMERIC
        '12.6',  # d2e2 / NUMERIC
        '',  # d2e3 / NUMERIC
        '12',  # d3e1 / NUMERIC
        '12.5',  # d3e2 / NUMERIC
        '12.55',  # d3e3 / NUMERIC
        '',  # dep
        '',  # br-pos
        1,  # legislatur / INTEGER
        '2004-2008',  # legisjahr / INT4RANGE
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    assert field.validate(form)
    assert not field.errors

    assert field.data[0].bfs_number == Decimal('100.10')
    assert field.data[0].date == date(2008, 2, 1)
    assert field.data[0].legislation_number == 1
    assert field.data[0].legislation_decade == NumericRange(2004, 2008)
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
    assert field.data[1].title_de == 'titel_off_d'
    assert field.data[1].title_fr == 'titel_off_f'
    assert field.data[1].short_title_de == 'titel_kurz_d'
    assert field.data[1].short_title_fr == 'titel_kurz_f'
    assert field.data[1].keyword == 'stichwort'
    assert field.data[1].votes_on_same_day == 2
    assert field.data[1]._legal_form == 3


@pytest.mark.skip('Todo: fix this test')
def test_swissvotes_dataset_skip_empty_columns():
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')

    mapper = ColumnMapper()

    file = BytesIO()
    workbook = Workbook(file)
    workbook.add_worksheet('CITATION')
    worksheet = workbook.add_worksheet('DATA')
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(8, 0, [
        '100.1',  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
        'link',  # swissvoteslink / TEXT
        '2',  # anzahl / INTEGER
        '3',  # rechtsform / INTEGER
        '',  # anneepolitique / TEXT
        '',  # bkchrono-de / TEXT
        '',  # bkchrono-fr / TEXT
        '13',  # d1e1 / NUMERIC
        '',  # d1e2 / NUMERIC
        '',  # d1e3 / NUMERIC
        '12',  # d2e1 / NUMERIC
        '12.6',  # d2e2 / NUMERIC
        '',  # d2e3 / NUMERIC
        '12',  # d3e1 / NUMERIC
        '12.5',  # d3e2 / NUMERIC
        '12.55',  # d3e3 / NUMERIC
        '',  # dep
        '',  # br-pos
        '1',  # legislatur / INTEGER
        '2004-2008',  # legisjahr / INT4RANGE
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'dataset': field_storage}))

    assert field.validate(form)
    assert not field.errors

    assert field.data[0].bfs_number == Decimal('100.10')
    assert field.data[0].date == date(2008, 2, 1)
    assert field.data[0].legislation_number == 1
    assert field.data[0].legislation_decade == NumericRange(2004, 2008)
    assert field.data[0].title_de == 'titel_off_d'
    assert field.data[0].title_fr == 'titel_off_f'
    assert field.data[0].short_title_de == 'titel_kurz_d'
    assert field.data[0].short_title_fr == 'titel_kurz_f'
    assert field.data[0].keyword == 'stichwort'
    assert field.data[0].votes_on_same_day == 2
    assert field.data[0]._legal_form == 3


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
