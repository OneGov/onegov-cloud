from __future__ import annotations

import math

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models.rate_set import RateSet


@dataclass(frozen=True)
class Compensation:
    base: Decimal
    adjusted: Decimal

    @classmethod
    def zero(cls) -> Compensation:
        return cls(base=Decimal('0'), adjusted=Decimal('0'))

    @property
    def adjustment(self) -> Decimal:
        return self.adjusted - self.base

    def __add__(self, other: Compensation) -> Compensation:
        return Compensation(
            base=self.base + other.base,
            adjusted=self.adjusted + other.adjusted,
        )


def round_to_five_rappen(value: Decimal | int) -> Decimal:
    if isinstance(value, int):
        value = Decimal(value)

    return (value / Decimal('0.05')).quantize(
        Decimal('1'), rounding=ROUND_HALF_UP
    ) * Decimal('0.05')


def cost_of_living_multiplier(
    percentage: Decimal | float | int,
) -> Decimal:
    return Decimal('1') + Decimal(str(percentage)) / Decimal('100')


def calculate_compensation(
    amount: Decimal | float | int,
    cost_of_living_adjustment: Decimal | float | int,
) -> Compensation:
    base = Decimal(str(amount))
    adjusted = base * cost_of_living_multiplier(cost_of_living_adjustment)
    return Compensation(
        base=round_to_five_rappen(base),
        adjusted=round_to_five_rappen(adjusted),
    )


def calculate_attendance_compensation(
    rate_set: RateSet,
    attendence_type: str,
    duration_minutes: Decimal | int,
    is_president: bool,
    commission_type: str | None = None,
) -> Compensation:
    amount = calculate_rate(
        rate_set=rate_set,
        attendence_type=attendence_type,
        duration_minutes=duration_minutes,
        is_president=is_president,
        commission_type=commission_type,
    )
    return calculate_compensation(
        amount,
        rate_set.cost_of_living_adjustment,
    )


def periods_of(duration_minutes: Decimal | int, minutes: int) -> int:
    """How many started periods a duration covers, rounded up."""
    return math.ceil(Decimal(duration_minutes) / minutes)


def calculate_rate(
    rate_set: RateSet,
    attendence_type: str,
    duration_minutes: Decimal | int,
    is_president: bool,
    commission_type: str | None = None,
) -> Decimal:
    """Calculate the rate for an attendance based on type, duration and role.
    """

    if attendence_type == 'plenary':
        # Entry of plenary session is always half a day. Duration (minutes)
        # therefore ignored (!)
        base_rate = (
            rate_set.plenary_none_president_halfday
            if is_president
            else rate_set.plenary_none_member_halfday
        )
        return Decimal(str(base_rate))

    elif attendence_type == 'commission' and commission_type:
        if commission_type == 'normal':
            # First 2 hours have initial rate, then additional per 30min
            if duration_minutes <= 120:  # 2 hours
                rate = (
                    rate_set.commission_normal_president_initial
                    if is_president
                    else rate_set.commission_normal_member_initial
                )
            else:
                initial = (
                    rate_set.commission_normal_president_initial
                    if is_president
                    else rate_set.commission_normal_member_initial
                )
                additional_per_30min = (
                    rate_set.commission_normal_president_additional
                    if is_president
                    else rate_set.commission_normal_member_additional
                )
                # This line calculates how many additional 30-minute periods
                # are needed after the initial 2 hours (120 minutes), with
                # rounding up.
                additional_periods = periods_of(duration_minutes - 120, 30)
                rate = initial + (additional_periods * additional_per_30min)

        else:  # intercantonal
            assert commission_type == 'intercantonal'
            # Per half day rates
            rate = (
                rate_set.commission_intercantonal_president_halfday
                if is_president
                else rate_set.commission_intercantonal_member_halfday
            )

        return Decimal(str(rate))

    elif attendence_type == 'study' and commission_type:
        # Study time is per half hour or hour depending on commission type
        if commission_type == 'normal':
            rate_per_30min = (
                rate_set.study_normal_president_halfhour
                if is_president
                else rate_set.study_normal_member_halfhour
            )
            periods = periods_of(duration_minutes, 30)
            return Decimal(str(rate_per_30min * periods))

        else:  # intercantonal
            rate_per_hour = (
                rate_set.study_intercantonal_president_hour
                if is_president
                else rate_set.study_intercantonal_member_hour
            )
            periods = periods_of(duration_minutes, 60)
            return Decimal(str(rate_per_hour * periods))

    elif attendence_type == 'shortest':
        # Shortest meetings are per 30min
        rate_per_30min = (
            rate_set.shortest_all_president_halfhour
            if is_president
            else rate_set.shortest_all_member_halfhour
        )
        periods = periods_of(duration_minutes, 30)
        return Decimal(str(rate_per_30min * periods))

    raise ValueError(
        f'Invalid attendance type {attendence_type} or commission '
        f'type {commission_type}'
    )
