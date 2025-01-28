from __future__ import annotations

from contextlib import suppress


from typing import TYPE_CHECKING
if TYPE_CHECKING:
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
