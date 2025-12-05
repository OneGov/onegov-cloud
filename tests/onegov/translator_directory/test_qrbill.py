from __future__ import annotations
from datetime import date
from decimal import Decimal

from onegov.translator_directory.request import TranslatorAppRequest
from unittest.mock import Mock
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.models.time_report import TranslatorTimeReport
from onegov.translator_directory.qrbill import (
    generate_translator_qr_bill,
    is_valid_iban,
)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import TestApp


def test_is_valid_iban() -> None:
    assert is_valid_iban('CH93 0076 2011 6238 5295 7')
    assert is_valid_iban('CH9300762011623852957')
    assert is_valid_iban('LI21 0881 0000 2324 013A A')
    assert is_valid_iban('DE89 3704 0044 0532 0130 00')

    assert not is_valid_iban(None)
    assert not is_valid_iban('')
    assert not is_valid_iban('invalid')
    assert not is_valid_iban('CH00 0000 0000 0000 0000 0')


def test_generate_qr_bill_for_self_employed(translator_app: 'TestApp') -> None:
    session = translator_app.session()

    translator = Translator(
        first_name='Hans',
        last_name='Muster',
        email='hans.muster@example.com',
        pers_id=12345,
        admission='certified',
        withholding_tax=False,
        self_employed=True,
        social_sec_number='756.1234.5678.97',
        tel_mobile='+41791234567',
        address='Musterstrasse 123',
        zip_code='8000',
        city='Zürich',
        iban='CH93 0076 2011 6238 5295 7',
    )
    session.add(translator)
    session.flush()

    time_report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_date=date(2024, 3, 15),
        finanzstelle='test',
        duration=120,
        hourly_rate=Decimal('100.00'),
        total_compensation=Decimal('200.00'),
        status='confirmed',
    )
    session.add(time_report)
    session.flush()

    request = Mock(spec=TranslatorAppRequest)
    request.locale = 'de_CH'

    qr_bill_bytes = generate_translator_qr_bill(
        translator, time_report, request
    )

    assert qr_bill_bytes is not None
    assert isinstance(qr_bill_bytes, bytes)
    assert len(qr_bill_bytes) > 0
    assert qr_bill_bytes.startswith(b'%PDF')


def test_generate_qr_bill_missing_iban(translator_app: 'TestApp') -> None:
    session = translator_app.session()

    translator = Translator(
        first_name='Hans',
        last_name='Muster',
        email='hans.muster@example.com',
        pers_id=12345,
        admission='certified',
        withholding_tax=False,
        self_employed=True,
        social_sec_number='756.1234.5678.97',
        tel_mobile='+41791234567',
        address='Musterstrasse 123',
        zip_code='8000',
        city='Zürich',
        iban=None,
    )
    session.add(translator)
    session.flush()

    time_report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_date=date(2024, 3, 15),
        finanzstelle='test',
        duration=120,
        hourly_rate=Decimal('100.00'),
        total_compensation=Decimal('200.00'),
        status='confirmed',
    )
    session.add(time_report)
    session.flush()

    request = Mock(spec=TranslatorAppRequest)
    request.locale = 'de_CH'

    qr_bill_bytes = generate_translator_qr_bill(
        translator, time_report, request
    )

    assert qr_bill_bytes is None


def test_generate_qr_bill_missing_address(translator_app: 'TestApp') -> None:
    session = translator_app.session()

    translator = Translator(
        first_name='Hans',
        last_name='Muster',
        email='hans.muster@example.com',
        pers_id=12345,
        admission='certified',
        withholding_tax=False,
        self_employed=True,
        social_sec_number='756.1234.5678.97',
        tel_mobile='+41791234567',
        address=None,
        zip_code='8000',
        city='Zürich',
        iban='CH93 0076 2011 6238 5295 7',
    )
    session.add(translator)
    session.flush()

    time_report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_date=date(2024, 3, 15),
        finanzstelle='test',
        duration=120,
        hourly_rate=Decimal('100.00'),
        total_compensation=Decimal('200.00'),
        status='confirmed',
    )
    session.add(time_report)
    session.flush()

    request = Mock(spec=TranslatorAppRequest)
    request.locale = 'de_CH'

    qr_bill_bytes = generate_translator_qr_bill(
        translator, time_report, request
    )

    assert qr_bill_bytes is None
