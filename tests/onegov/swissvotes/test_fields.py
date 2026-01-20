from __future__ import annotations

from cgi import FieldStorage
from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.form import Form
from onegov.swissvotes.fields import PolicyAreaField
from onegov.swissvotes.fields import SwissvoteDatasetField
from onegov.swissvotes.fields import SwissvoteMetadataField
from onegov.swissvotes.models import ColumnMapperDataset
from onegov.swissvotes.models import ColumnMapperMetadata
from xlsxwriter.workbook import Workbook


from typing import Any


class DummyPostData(dict[str, Any]):
    def getlist(self, key: str) -> list[Any]:
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_swissvotes_dataset_field_corrupt() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = BytesIO(b'Test')
    field.process(DummyPostData({'dataset': field_storage}))

    assert not field.validate(form)
    assert "Not a valid XLSX file." in field.errors


def test_swissvotes_dataset_field_missing_sheet() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]

    file = BytesIO()
    workbook = Workbook(file)
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


def test_swissvotes_dataset_field_empty() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]

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

    assert not field.validate(form)
    assert "No data." in field.errors


def test_swissvotes_dataset_field_missing_columns() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]
    mapper = ColumnMapperDataset()
    columns = [
        column for column in mapper.columns.values()
        if column != 'anr'
    ]

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')

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

    assert 'Some columns are missing: anr.' in errors


def test_swissvotes_dataset_field_types_and_missing_values() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]
    mapper = ColumnMapperDataset()
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    worksheet.write_row(0, 0, mapper.columns.values())
    for row, content in enumerate(('', None, 'x', 1, 1.1, date(2018, 12, 12))):
        worksheet.write_row(row + 1, 0, [
            content,  # anr / NUMERIC
            content,  # datum / DATE
            content,  # short_title_de / TEXT
            content,  # short_title_fr / TEXT
            content,  # short_title_en / TEXT
            content,  # title_de / TEXT
            content,  # title_fr / TEXT
            content,  # stichwort / TEXT
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
            content,  # br-pos
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
    assert "2:titel_off_d ∅" in error
    assert "2:titel_off_f ∅" in error
    assert "2:titel_kurz_d ∅" in error
    assert "2:titel_kurz_f ∅" in error

    assert "2:rechtsform ∅" in error

    assert "3:anr ∅" in error
    assert "3:datum ∅" in error
    assert "3:titel_off_d ∅" in error
    assert "3:titel_off_f ∅" in error
    assert "3:titel_kurz_d ∅" in error
    assert "3:titel_kurz_f ∅" in error

    assert "4:anr 'x' ≠ numeric(8, 2)" in error
    assert "4:datum 'x' ≠ date" in error


def test_swissvotes_dataset_field_all_okay() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]
    mapper = ColumnMapperDataset()
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_kurz_e',  # short_title_en / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
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
        '',  # br-pos
    ])
    worksheet.write_row(2, 0, [
        100.2,  # anr / NUMERIC
        date(2008, 2, 1),  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_kurz_e',  # short_title_en / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
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
        '',  # br-pos
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
    assert field.data[0].title_de == 'titel_off_d'
    assert field.data[0].title_fr == 'titel_off_f'
    assert field.data[0].short_title_de == 'titel_kurz_d'
    assert field.data[0].short_title_fr == 'titel_kurz_f'
    assert field.data[0].keyword == 'stichwort'
    assert field.data[0]._legal_form == 3

    assert field.data[1].bfs_number == Decimal('100.20')
    assert field.data[1].date == date(2008, 2, 1)
    assert field.data[1].title_de == 'titel_off_d'
    assert field.data[1].title_fr == 'titel_off_f'
    assert field.data[1].short_title_de == 'titel_kurz_d'
    assert field.data[1].short_title_fr == 'titel_kurz_f'
    assert field.data[1].keyword == 'stichwort'
    assert field.data[1]._legal_form == 3


def test_swissvotes_dataset_skip_empty_columns() -> None:
    form = Form()
    field = SwissvoteDatasetField()
    field = field.bind(form, 'dataset')  # type: ignore[attr-defined]

    mapper = ColumnMapperDataset()

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(8, 0, [
        '100.1',  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_kurz_e',  # short_title_en / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
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
        '',  # br-pos
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
    assert field.data[0].title_de == 'titel_off_d'
    assert field.data[0].title_fr == 'titel_off_f'
    assert field.data[0].short_title_de == 'titel_kurz_d'
    assert field.data[0].short_title_fr == 'titel_kurz_f'
    assert field.data[0].keyword == 'stichwort'
    assert field.data[0]._legal_form == 3


def test_swissvotes_metadata_field_corrupt() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = BytesIO(b'Test')
    field.process(DummyPostData({'metadata': field_storage}))

    assert not field.validate(form)
    assert "Not a valid XLSX file." in field.errors


def test_swissvotes_metadata_field_missing_sheet() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]

    file = BytesIO()
    workbook = Workbook(file)
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'metadata': field_storage}))

    # It raises for the first sheet it cant find
    assert not field.validate(form)
    assert "Sheet 'Metadaten zu Scans' is missing." in field.errors


def test_swissvotes_metadata_field_empty() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]

    file = BytesIO()
    workbook = Workbook(file)
    workbook.add_worksheet('Metadaten zu Scans')
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'metadata': field_storage}))

    assert not field.validate(form)
    assert "No data." in field.errors


def test_swissvotes_metadata_field_missing_columns() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]
    mapper = ColumnMapperMetadata()
    columns = [
        column for column in mapper.columns.values()
        if column != 'Dateiname'
    ]

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('Metadaten zu Scans')

    worksheet.write_row(0, 0, columns)
    worksheet.write_row(1, 0, columns)
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'metadata': field_storage}))

    assert not field.validate(form)
    errors = [error.interpolate() for error in field.errors]

    assert 'Some columns are missing: Dateiname.' in errors


def test_swissvotes_metadata_field_types_and_missing_values() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]
    mapper = ColumnMapperMetadata()
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('Metadaten zu Scans')
    worksheet.write_row(0, 0, mapper.columns.values())
    for row, content in enumerate(('', None, 'x', 1, 1.1)):
        worksheet.write_row(row + 1, 0, [
            content,  # Abst-Nummer
            content,  # Dateiname
            content,  # Titel des Dokuments
            content,  # Position zur Vorlage
            content,  # AutorIn (Nachname Vorname) des Dokuments
            content,  # AuftraggeberIn/HerausgeberIn des Dokuments
            content,  # Datum Jahr
            content,  # Datum Monat
            content,  # Datum Tag
            content,  # Sprache DE
            content,  # Sprache EN
            content,  # Sprache FR
            content,  # Sprache IT
            content,  # Sprache RR
            content,  # Sprache Gemischt
            content,  # Sprache Anderes
            content,  # Typ ARGUMENTARIUM
            content,  # Typ BRIEF
            content,  # Typ DOKUMENTATION
            content,  # Typ FLUGBLATT
            content,  # Typ MEDIENMITTEILUNG
            content,  # Typ MITGLIEDERVERZEICHNIS
            content,  # Typ PRESSEARTIKEL
            content,  # Typ RECHTSTEXT
            content,  # Typ REFERATSTEXT
            content,  # Typ STATISTIK
            'xxx'     # avoid being ignore because all cells are empty
        ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'metadata': field_storage}))

    assert not field.validate(form)
    error = [error.interpolate() for error in field.errors][0]

    assert "2:Abst-Nummer ∅" in error
    assert "2:Dateiname ∅" in error

    assert "3:Abst-Nummer ∅" in error
    assert "3:Dateiname ∅" in error

    assert "4:Abst-Nummer 'x' ≠ numeric" in error
    assert "4:Datum Jahr 'x' ≠ integer" in error
    assert "4:Datum Monat 'x' ≠ integer" in error
    assert "4:Datum Tag 'x' ≠ integer" in error


def test_swissvotes_metadata_field_all_okay() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]
    mapper = ColumnMapperMetadata()
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('Metadaten zu Scans')
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # Abst-Nummer
        'letter.pdf',  # Dateiname
        'Brief',  # Titel des Dokuments
        'Ja',  # Position zur Vorlage
        'Autor',  # AutorIn (Nachname Vorname) des Dokuments
        'Herausgeber',  # AuftraggeberIn/HerausgeberIn des Dokuments
        '1970',  # Datum Jahr
        '12',  # Datum Monat
        '31',  # Datum Tag
        'x',  # Sprache DE
        'x',  # Sprache EN
        'x',  # Sprache FR
        'x',  # Sprache IT
        'x',  # Sprache RR
        'x',  # Sprache Gemischt
        'x',  # Sprache Anderes
        'x',  # Typ ARGUMENTARIUM
        'x',  # Typ BRIEF
        'x',  # Typ DOKUMENTATION
        'x',  # Typ FLUGBLATT
        'x',  # Typ MEDIENMITTEILUNG
        'x',  # Typ MITGLIEDERVERZEICHNIS
        'x',  # Typ PRESSEARTIKEL
        'x',  # Typ RECHTSTEXT
        'x',  # Typ REFERATSTEXT
        'x',  # Typ STATISTIK
        'x',  # Typ ANDERES
        'x',  # Typ WEBSITE
    ])
    worksheet.write_row(2, 0, [
        '100.1',  # Abst-Nummer
        'article.pdf',  # Dateiname
        'Presseartikel',  # Titel des Dokuments
        'Gemischt',  # Position zur Vorlage
        'A.',  # AutorIn (Nachname Vorname) des Dokuments
        'H.',  # AuftraggeberIn/HerausgeberIn des Dokuments
        '1980',  # Datum Jahr
        '',  # Datum Monat
        '',  # Datum Tag
        'x',  # Sprache DE
        '',  # Sprache EN
        '',  # Sprache FR
        '',  # Sprache IT
        '',  # Sprache RR
        '',  # Sprache Gemischt
        '',  # Sprache Anderes
        '',  # Typ ARGUMENTARIUM
        '',  # Typ BRIEF
        '',  # Typ DOKUMENTATION
        '',  # Typ FLUGBLATT
        '',  # Typ MEDIENMITTEILUNG
        '',  # Typ MITGLIEDERVERZEICHNIS
        'x',  # Typ PRESSEARTIKEL
        '',  # Typ RECHTSTEXT
        '',  # Typ REFERATSTEXT
        '',  # Typ STATISTIK
        '',  # Typ ANDERES
        '',  # Typ WEBSITE
    ])
    worksheet.write_row(3, 0, [
        '100.2',  # Abst-Nummer
        'other.pdf',  # Dateiname
        '',  # Titel des Dokuments
        '',  # Position zur Vorlage
        '',  # AutorIn (Nachname Vorname) des Dokuments
        '',  # AuftraggeberIn/HerausgeberIn des Dokuments
        '',  # Datum Jahr
        '',  # Datum Monat
        '',  # Datum Tag
        '',  # Sprache DE
        '',  # Sprache EN
        '',  # Sprache FR
        '',  # Sprache IT
        '',  # Sprache RR
        '',  # Sprache Gemischt
        '',  # Sprache Anderes
        '',  # Typ ARGUMENTARIUM
        '',  # Typ BRIEF
        '',  # Typ DOKUMENTATION
        '',  # Typ FLUGBLATT
        '',  # Typ MEDIENMITTEILUNG
        '',  # Typ MITGLIEDERVERZEICHNIS
        '',  # Typ PRESSEARTIKEL
        '',  # Typ RECHTSTEXT
        '',  # Typ REFERATSTEXT
        '',  # Typ STATISTIK
        '',  # Typ ANDERES
        '',  # Typ WEBSITE
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'metadata': field_storage}))

    assert field.validate(form)
    assert not field.errors
    assert field.data == {
        Decimal('100.10'): {
            'letter.pdf': {
                'author': 'Autor',
                'bfs_number': Decimal('100.10'),
                'date_day': 31,
                'date_month': 12,
                'date_year': 1970,
                'doctype': [
                    'argument',
                    'letter',
                    'documentation',
                    'leaflet',
                    'release',
                    'memberships',
                    'article',
                    'legal',
                    'lecture',
                    'statistics',
                    'other',
                    'website'
                ],
                'editor': 'Herausgeber',
                'filename': 'letter.pdf',
                'language': [
                    'de',
                    'en',
                    'fr',
                    'it',
                    'rm',
                    'mixed',
                    'other'
                ],
                'position': 'yes',
                'title': 'Brief'
            },
            'article.pdf': {
                'author': 'A.',
                'bfs_number': Decimal('100.10'),
                'date_day': None,
                'date_month': None,
                'date_year': 1980,
                'doctype': ['article'],
                'editor': 'H.',
                'filename': 'article.pdf',
                'language': ['de'],
                'position': 'mixed',
                'title': 'Presseartikel'
            }
        },
        Decimal('100.20'): {
            'other.pdf': {
                'author': None,
                'bfs_number': Decimal('100.20'),
                'date_day': None,
                'date_month': None,
                'date_year': None,
                'doctype': [],
                'editor': None,
                'filename': 'other.pdf',
                'language': [],
                'position': None,
                'title': None
            },
        }
    }


def test_swissvotes_metadata_skip_empty_columns() -> None:
    form = Form()
    field = SwissvoteMetadataField()
    field = field.bind(form, 'metadata')  # type: ignore[attr-defined]

    mapper = ColumnMapperMetadata()

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('Metadaten zu Scans')
    worksheet.write_row(0, 0, mapper.columns.values())
    worksheet.write_row(8, 0, [
        '100.2',  # Abst-Nummer
        'other.pdf',  # Dateiname
        '',  # Titel des Dokuments
        '',  # Position zur Vorlage
        '',  # AutorIn (Nachname Vorname) des Dokuments
        '',  # AuftraggeberIn/HerausgeberIn des Dokuments
        '',  # Datum Jahr
        '',  # Datum Monat
        '',  # Datum Tag
        '',  # Sprache DE
        '',  # Sprache EN
        '',  # Sprache FR
        '',  # Sprache IT
        '',  # Sprache RR
        '',  # Sprache Gemischt
        '',  # Sprache Anderes
        '',  # Typ ARGUMENTARIUM
        '',  # Typ BRIEF
        '',  # Typ DOKUMENTATION
        '',  # Typ FLUGBLATT
        '',  # Typ MEDIENMITTEILUNG
        '',  # Typ MITGLIEDERVERZEICHNIS
        '',  # Typ PRESSEARTIKEL
        '',  # Typ RECHTSTEXT
        '',  # Typ REFERATSTEXT
        '',  # Typ STATISTIK
        '',  # Typ ANDERES
        '',  # Typ WEBSITE
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'
    field_storage.file = file
    field.process(DummyPostData({'metadata': field_storage}))

    assert field.validate(form)
    assert not field.errors
    assert field.data == {
        Decimal('100.20'): {
            'other.pdf': {
                'author': None,
                'bfs_number': Decimal('100.20'),
                'date_day': None,
                'date_month': None,
                'date_year': None,
                'doctype': [],
                'editor': None,
                'filename': 'other.pdf',
                'language': [],
                'position': None,
                'title': None
            }
        }
    }


def test_policy_area_field() -> None:
    form = Form()
    field = PolicyAreaField()
    field = field.bind(form, 'policy_area')  # type: ignore[attr-defined]

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
