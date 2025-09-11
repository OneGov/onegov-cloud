from __future__ import annotations

import pytest
import transaction

from onegov.pay.models import Payment


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope='function', autouse=True)
def reset_payment() -> Iterator[None]:
    yield

    # during testing we need to reset the links created on the payment
    # model - in reality this is not an issue as we don't define the same
    # models over and over
    classes = [Payment]

    while classes:
        cls = classes.pop()

        for key in (Payment.registered_links or ()):
            try:
                del cls.__mapper__._props[key]  # type: ignore[attr-defined]
            except KeyError:
                pass

        classes.extend(cls.__subclasses__())

    if Payment.registered_links:
        Payment.registered_links.clear()

    transaction.abort()
