from __future__ import annotations

from onegov.activity import ActivityCollection
from onegov.feriennet.policy import ActivityQueryPolicy
from sqlalchemy.orm import selectinload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity, NoIdentity
    from onegov.activity.collections.activity import ActivityFilter
    from onegov.feriennet.models import VacationActivity
    from sqlalchemy.orm import Query, Session
    from typing import Self, TypeVar

    T = TypeVar('T')


class VacationActivityCollection(ActivityCollection['VacationActivity']):

    # type is ignored, but present to keep the same signature as the superclass
    def __init__(
        self,
        session: Session,
        type: None = None,
        pages: tuple[int, int] | None = (0, 0),
        filter: ActivityFilter | None = None,
        identity: Identity | NoIdentity | None = None
    ) -> None:

        super().__init__(
            session=session,
            type='vacation',
            pages=pages,
            filter=filter
        )

        self.identity = identity

    @property
    def policy(self) -> ActivityQueryPolicy:
        return ActivityQueryPolicy.for_identity(self.identity)

    def transform_batch_query(self, query: Query[T]) -> Query[T]:
        return query.options(selectinload(self.model_class.occasions))

    def query_base(self) -> Query[VacationActivity]:
        return self.policy.granted_subset(self.session.query(self.model_class))

    def by_page_range(self, page_range: tuple[int, int] | None) -> Self:
        return self.__class__(
            session=self.session,
            identity=self.identity,
            pages=page_range,
            filter=self.filter
        )
