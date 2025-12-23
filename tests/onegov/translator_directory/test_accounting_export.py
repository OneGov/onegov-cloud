from __future__ import annotations

import csv
import pytest
import transaction

from datetime import date
from decimal import Decimal
from io import StringIO
from onegov.translator_directory.collections.translator import (
    TranslatorCollection,
)
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.translator_directory.views.time_report import (
    generate_accounting_export_rows,
)
from onegov.translator_directory.constants import FINANZSTELLE

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def test_finanzstelle_kostenstelle_field() -> None:
    '''Validates that all Finanzstelle entries have a kostenstelle.'''
    for key, finanzstelle in FINANZSTELLE.items():
        assert finanzstelle.kostenstelle, (
            f'Finanzstelle {key} ({finanzstelle.name}) is missing '
            f'kostenstelle field'
        )


def test_accounting_export_kostenstelle_mapping(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()
    translator_id = translator.id

    finanzstelle_mappings = [
        ('migrationsamt_und_passbuero', '2122'),
        ('staatsanwaltschaft', '2466'),
        ('gefaengnisverwaltung', '2472'),
        ('polizei', '2550-DO00'),
        ('obergericht', '3010'),
        ('kantonsgericht', '3030'),
    ]

    for finanzstelle_key, expected_kostenstelle in finanzstelle_mappings:
        report = TranslatorTimeReport(
            translator_id=translator_id,
            assignment_type='consecutive',
            finanzstelle=finanzstelle_key,
            duration=90,
            case_number='CASE-001',
            assignment_date=date(2025, 1, 15),
            hourly_rate=Decimal('90.0'),
            travel_compensation=Decimal('50.0'),
            total_compensation=Decimal('185.0'),
            status='confirmed',
        )
        session.add(report)
        session.flush()

        rows = list(generate_accounting_export_rows([report]))

        row_2603 = rows[0]
        assert row_2603[12] == expected_kostenstelle, (
            f'Kostenstelle mismatch for {finanzstelle_key}: '
            f'expected {expected_kostenstelle}, got {row_2603[12]}'
        )

        if report.travel_compensation > 0:
            row_8102_travel = rows[1]
            assert row_8102_travel[12] == expected_kostenstelle, (
                f'Kostenstelle mismatch in travel row for '
                f'{finanzstelle_key}: expected {expected_kostenstelle}, '
                f'got {row_8102_travel[12]}'
            )

        session.delete(report)
        session.flush()

    transaction.commit()


def test_accounting_export_unknown_finanzstelle(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='unknown_finanzstelle',
        duration=90,
        case_number='CASE-001',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('135.0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    with pytest.raises(ValueError, match='Unknown finanzstelle'):
        list(generate_accounting_export_rows([report]))

    transaction.commit()


def test_accounting_export_all_row_types(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=360,
        case_number='CASE-001',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('50.0'),
        total_compensation=Decimal('210.0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    rows = list(generate_accounting_export_rows([report]))

    assert len(rows) == 3, f'Expected 3 rows, got {len(rows)}'

    row_2603 = rows[0]
    assert row_2603[0] == 'L001'
    assert row_2603[1] == '12345'
    assert row_2603[4] == '2603'
    assert row_2603[12] == '2550-DO00'

    row_8102_travel = rows[1]
    assert row_8102_travel[0] == 'L001'
    assert row_8102_travel[1] == '12345'
    assert row_8102_travel[4] == '8102'
    assert row_8102_travel[12] == '2550-DO00'

    row_8102_meal = rows[2]
    assert row_8102_meal[0] == 'L001'
    assert row_8102_meal[1] == '12345'
    assert row_8102_meal[4] == '8102'
    assert row_8102_meal[12] == '2550-DO00'

    transaction.commit()


def test_accounting_export_csv_format(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='99999',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='obergericht',
        duration=120,
        case_number='CASE-002',
        assignment_date=date(2025, 2, 20),
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('30.0'),
        total_compensation=Decimal('210.0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    rows = list(generate_accounting_export_rows([report]))

    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    for row in rows:
        writer.writerow(row)

    csv_content = output.getvalue()
    lines = csv_content.strip().split('\n')

    assert len(lines) == 2, f'Expected 2 lines, got {len(lines)}'

    first_line_parts = lines[0].split(';')
    assert first_line_parts[0] == 'L001'
    assert first_line_parts[1] == '99999'
    assert first_line_parts[2] == '20.02.2025'
    assert first_line_parts[4] == '2603'
    assert first_line_parts[12] == '3010'

    second_line_parts = lines[1].split(';')
    assert second_line_parts[12] == '3010'

    transaction.commit()
