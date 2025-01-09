from decimal import Decimal
from babel.numbers import format_decimal


def format_swiss_number(value: Decimal | int) -> str:
    if isinstance(value, int):
        value = Decimal(value)
    return format_decimal(value, format='#,##0.00', locale='de_CH')
