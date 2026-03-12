from __future__ import annotations

import transaction
from contextlib import contextmanager


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterator
    from sqlalchemy.orm import Session

    _T = TypeVar('_T')


class BaseScenario:

    def __init__(self, session: Session, test_password: str) -> None:
        self.session = session
        self.test_password = test_password

    def __getattribute__(self, name: str) -> Any:
        if name.startswith('add_') and not transaction.manager.manager._txn:  # type: ignore[attr-defined]
            transaction.begin()

        return super().__getattribute__(name)

    def commit(self) -> None:
        transaction.commit()

    @property
    def cached_attributes(self) -> Collection[str]:
        raise NotImplementedError

    @contextmanager
    def update(self) -> Iterator[None]:
        self.refresh()
        yield
        self.commit()

    def add(self, model: Callable[..., _T], **columns: Any) -> _T:
        obj = model(**columns)
        self.session.add(obj)

        return obj

    def refresh(self) -> None:
        transaction.begin()

        for name in self.cached_attributes:
            cache = getattr(self, name)

            for ix, item in enumerate(cache):
                cache[ix] = self.session.merge(item)
                self.session.refresh(cache[ix])
