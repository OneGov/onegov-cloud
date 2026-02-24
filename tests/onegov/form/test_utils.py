from __future__ import annotations

from decimal import Decimal
from onegov.form import decimal_range
from wtforms import Form
from wtforms.fields import StringField
from wtforms.validators import InputRequired


def test_decimal_range() -> None:
    assert list(decimal_range('0', '2')) == [
        Decimal('0'),
        Decimal('1')
    ]

    assert list(decimal_range('2', '0')) == [
        Decimal('2'),
        Decimal('1')
    ]

    assert list(decimal_range('0', '1', '0.25')) == [
        Decimal('0'),
        Decimal('0.25'),
        Decimal('0.5'),
        Decimal('0.75')
    ]

    assert decimal_range('0', '1') == decimal_range('0', '1')
    assert decimal_range('1', '0') != decimal_range('0', '1')
    assert decimal_range('0', '1', '0.1') != decimal_range('0', '1', '0.2')

    assert repr(decimal_range('0', '1')) == "decimal_range('0', '1')"


def test_disable_required_attributes() -> None:
    field = StringField(validators=[InputRequired()])
    field = field.bind(Form(), 'field')  # type: ignore[attr-defined]
    field.data = ''

    html = field().replace('aria-required', 'aria-req')
    assert 'required' not in html
    assert 'aria-req' in html
