from __future__ import annotations

from onegov.core.collection import Pagination
from onegov.core.orm.utils import QueryChain
from onegov.pay import Payment
from sqlalchemy.orm import joinedload, selectinload


from typing import overload, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase, Session
    from typing import Self


# FIXME: This should be Intersection[DeclarativeBase, Payable] once this
#        feature gets added to typing_extensions
_P = TypeVar('_P', bound='DeclarativeBase')


class PayableCollection(Pagination[_P]):
    """ Provides a collection of all payable models. This collection is
    meant to be read-only, so there's no add/delete methods.

    To add payments to payable models just use the payment property and
    directly assign a new or an existing payment.

    """

    page: int

    @overload
    def __init__(
        self: PayableCollection[_P],
        session: Session,
        cls: type[_P],
        page: int = 0
    ): ...

    @overload
    def __init__(
        self: PayableCollection[DeclarativeBase],
        session: Session,
        cls: Literal['*'] = '*',
        page: int = 0
    ): ...

    def __init__(
        self,
        session: Session,
        cls: Literal['*'] | type[_P] = '*',
        page: int = 0
    ):
        self.session = session
        self.cls = cls
        self.page = page

    if TYPE_CHECKING:
        # we override the method that would not be type safe since the type
        # of query changed from the base class Pagination
        def transform_batch_query(  # type:ignore[override]
            self,
            query: QueryChain[_P]  # type:ignore[override]
        ) -> QueryChain[_P]: ...

    @property
    def classes(self) -> tuple[type[DeclarativeBase], ...]:
        if self.cls != '*':
            return (self.cls, )

        assert Payment.registered_links is not None
        return tuple(link.cls for link in Payment.registered_links.values())

    def query(self) -> QueryChain[_P]:
        return QueryChain(tuple(
            self.session.query(cls).options(  # type: ignore[misc]
                joinedload(cls.payment)
                if hasattr(cls, 'payment') else
                selectinload(cls.payments)  # type: ignore[attr-defined]
            )
            for cls in self.classes
        ))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PayableCollection):
            return False

        return self.cls == other.cls and self.page == other.page

    def subset(self) -> QueryChain[_P]:  # type:ignore[override]
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, self.cls, index)
