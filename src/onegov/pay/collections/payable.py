from onegov.core.collection import Pagination
from onegov.core.orm.utils import QueryChain
from onegov.pay import Payment
from sqlalchemy.orm import joinedload


from typing import overload, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base
    from sqlalchemy.orm import Query, Session
    from typing_extensions import Self


# FIXME: This should be Intersection[Base, Payable] once this feature
#        gets added to typing_extensions
_P = TypeVar('_P', bound='Base')


class PayableCollection(Pagination[_P]):
    """ Provides a collection of all payable models. This collection is
    meant to be read-only, so there's no add/delete methods.

    To add payments to payable models just use the payment property and
    directly assign a new or an existing payment.

    """

    page: int

    @overload
    def __init__(
        self: 'PayableCollection[_P]',
        session: 'Session',
        cls: type[_P],
        page: int = 0
    ): ...

    @overload
    def __init__(
        self: 'PayableCollection[Base]',
        session: 'Session',
        cls: Literal['*'] = '*',
        page: int = 0
    ): ...

    def __init__(
        self,
        session: 'Session',
        cls: Literal['*'] | type[_P] = '*',
        page: int = 0
    ):
        self.session = session
        self.cls = cls
        self.page = page

    @property
    def classes(self) -> tuple[type['Base'], ...]:
        if self.cls != '*':
            return (self.cls, )

        assert Payment.registered_links is not None
        return tuple(link.cls for link in Payment.registered_links.values())

    def query(self) -> 'Query[_P]':
        return QueryChain((
            self.session.query(cls).options(
                joinedload(cls.payment)  # type:ignore[attr-defined]
            )
            for cls in self.classes
        ))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PayableCollection):
            return False

        return self.cls == other.cls and self.page == other.page

    def subset(self) -> 'Query[_P]':
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> 'Self':
        return self.__class__(self.session, self.cls, index)
