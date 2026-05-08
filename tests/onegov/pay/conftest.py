from __future__ import annotations

import pytest
import transaction

from onegov.pay.models import Payment


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope='function', autouse=True)
def reset_payment() -> Iterator[None]:
    classes = [Payment]
    registered_links: dict[type[Payment], set[str]] = {}
    while classes:
        cls = classes.pop()
        registered_links[cls] = set(cls.registered_links or ())
        classes.extend(cls.__subclasses__())
    yield

    transaction.abort()

    # during testing we need to reset the links created on the payment
    # model by our test code - in reality this is not an issue as we
    # don't define the same models over and over
    for cls, links in registered_links.items():
        if cls.registered_links is None:
            continue

        for link_name in tuple(cls.registered_links.keys()):
            if link_name not in links:
                if link_name in cls.__mapper__._props:
                    del cls.__mapper__._props[link_name]
                    # HACK: Disables protections against removal
                    type.__setattr__(cls, link_name, None)
                    mgr = cls.__mapper__.class_manager
                    mgr.uninstrument_attribute(link_name)  # type: ignore[no-untyped-call]

    for cls, links in registered_links.items():
        if cls.registered_links is None:
            continue

        for link_name in tuple(cls.registered_links.keys()):
            if link_name not in links:
                del cls.registered_links[link_name]
