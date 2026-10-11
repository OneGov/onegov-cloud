from decimal import Decimal

from onegov.pas.calculate_pay import calculate_compensation
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.calculate_pay import cost_of_living_multiplier
from onegov.pas.calculate_pay import round_to_five_rappen
from onegov.pas.models import RateSet


def test_financial_rounding() -> None:
    assert round_to_five_rappen(Decimal('0.024')) == Decimal('0.00')
    assert round_to_five_rappen(Decimal('0.025')) == Decimal('0.05')
    assert round_to_five_rappen(Decimal('0.0749')) == Decimal('0.05')
    assert round_to_five_rappen(Decimal('0.075')) == Decimal('0.10')
    assert round_to_five_rappen(Decimal('-0.025')) == Decimal('-0.05')

    multiplier = cost_of_living_multiplier(Decimal('0.988'))
    assert multiplier == Decimal('1.00988')
    assert round_to_five_rappen(Decimal('625') * multiplier) == Decimal(
        '631.20'
    )


def test_compensation_totals_sum_rounded_bookings() -> None:
    booking = calculate_compensation(
        Decimal('43'),
        Decimal('21.935'),
    )
    total = booking + booking
    rounded_after_aggregation = calculate_compensation(
        Decimal('86'),
        Decimal('21.935'),
    )

    assert booking.base == Decimal('43.00')
    assert booking.adjusted == Decimal('52.45')
    assert total.base == Decimal('86.00')
    assert total.adjustment == Decimal('18.90')
    assert total.adjusted == Decimal('104.90')
    assert rounded_after_aggregation.adjusted == Decimal('104.85')


def test_zero_duration_has_no_compensation() -> None:
    rate_set = RateSet(commission_normal_member_initial=170)

    assert calculate_rate(
        rate_set=rate_set,
        attendence_type='commission',
        duration_minutes=0,
        is_president=False,
        commission_type='normal',
    ) == Decimal('0')
