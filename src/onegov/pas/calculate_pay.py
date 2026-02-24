from __future__ import annotations

from decimal import Decimal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models.rate_set import RateSet


def calculate_rate(
    rate_set: RateSet,
    attendence_type: str,
    duration_minutes: int,
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
                additional_periods = (
                    duration_minutes - 120 + 29
                ) // 30  # round up
                rate = initial + (
                    additional_periods * additional_per_30min
                )

        elif commission_type == 'intercantonal':
            # Per half day rates
            rate = (
                rate_set.commission_intercantonal_president_halfday
                if is_president
                else rate_set.commission_intercantonal_member_halfday
            )

        else:  # official
            # Has both half day and full day rates
            # todo: What is the way to determine if it is full day?
            is_full_day = duration_minutes > 240  # more than 4 hours
            if is_president:
                rate = (
                    rate_set.commission_official_president_fullday
                    if is_full_day
                    else rate_set.commission_official_president_halfday
                )
            else:
                rate = (
                    rate_set.commission_official_vice_president_fullday
                    if is_full_day
                    else rate_set.commission_official_vice_president_halfday
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
            periods = (
                duration_minutes + 29
            ) // 30  # round up to next 30min
            return Decimal(str(rate_per_30min * periods))

        elif commission_type == 'intercantonal':
            rate_per_hour = (
                rate_set.study_intercantonal_president_hour
                if is_president
                else rate_set.study_intercantonal_member_hour
            )
            periods = (
                duration_minutes + 59
            ) // 60  # round up to next hour
            return Decimal(str(rate_per_hour * periods))

        else:  # official
            rate_per_30min = (
                rate_set.study_official_president_halfhour
                if is_president
                else rate_set.study_official_member_halfhour
            )
            periods = (
                duration_minutes + 29
            ) // 30  # round up to next 30min
            return Decimal(str(rate_per_30min * periods))

    elif attendence_type == 'shortest':
        # Shortest meetings are per 30min
        rate_per_30min = (
            rate_set.shortest_all_president_halfhour
            if is_president
            else rate_set.shortest_all_member_halfhour
        )
        periods = (duration_minutes + 29) // 30  # round up to next 30min
        return Decimal(str(rate_per_30min * periods))

    raise ValueError(
        f'Invalid attendance type {attendence_type} or commission '
        f'type {commission_type}'
    )
