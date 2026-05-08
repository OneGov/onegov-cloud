from __future__ import annotations

from contextlib import suppress

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.activity import Activity
    from onegov.activity import Occasion
    from onegov.activity.types import BoundedIntegerRange
    from onegov.feriennet.request import FeriennetRequest
    from collections.abc import Iterable, Iterator
    from decimal import Decimal

NAME_SEPARATOR = '\u00A0'  # non-breaking space


def encode_name(first_name: str, last_name: str) -> str:
    names = (first_name, last_name)
    return NAME_SEPARATOR.join(n.replace(NAME_SEPARATOR, ' ') for n in names)


def decode_name(fullname: str | None) -> tuple[str | None, str | None]:
    if fullname:
        names = fullname.split(NAME_SEPARATOR)
    else:
        names = None

    if not names:
        return None, None
    if len(names) <= 1:
        return names[0], None
    else:
        return names[0], names[1]


def parse_donation_amounts(text: str) -> tuple[float, ...]:
    lines = (stripped for l in text.splitlines() if (stripped := l.strip()))

    def amounts() -> Iterator[float]:
        for line in lines:
            with suppress(ValueError):
                amount = float(line)
                amount = round(.05 * round(amount / .05), 2)

                yield amount

    return tuple(amounts())


def format_donation_amounts(amounts: Iterable[Decimal | float]) -> str:
    def lines() -> Iterator[str]:
        for amount in amounts:
            if float(amount).is_integer():
                yield f'{int(amount):d}'
            else:
                yield f'{amount:.2f}'

    return '\n'.join(lines())


def period_bound_occasions(
    activity: Activity,
    request: FeriennetRequest
) -> list[Occasion]:

    if not hasattr(request.app, 'active_period'):
        return []
    active_period = request.app.active_period

    if not active_period:
        return []

    return [o for o in activity.occasions if o.period_id == active_period.id]


def activity_ages(
    activity: Activity,
    request: FeriennetRequest
) -> tuple[BoundedIntegerRange, ...]:
    return tuple(o.age for o in period_bound_occasions(activity, request))


def activity_spots(
    activity: Activity,
    request: FeriennetRequest
) -> int:

    if not request.app.active_period:
        return 0

    if not request.app.active_period.confirmed:
        return sum(o.max_spots for o in period_bound_occasions(
            activity, request))

    return sum(o.available_spots for o in period_bound_occasions(
        activity, request))


def activity_min_cost(
    activity: Activity,
    request: FeriennetRequest
) -> Decimal | None:

    occasions = period_bound_occasions(activity, request)

    if not occasions:
        return None

    return min(o.total_cost for o in occasions)


def activity_max_cost(
    activity: Activity,
    request: FeriennetRequest
) -> Decimal | None:

    occasions = period_bound_occasions(activity, request)

    if not occasions:
        return None

    return max(o.total_cost for o in occasions)
