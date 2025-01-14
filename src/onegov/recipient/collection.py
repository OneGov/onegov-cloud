from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.recipient.model import GenericRecipient

from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

_RecipientT = TypeVar('_RecipientT', bound=GenericRecipient)


class GenericRecipientCollection(GenericCollection[_RecipientT]):

    def __init__(self, session: Session, type: str):
        super().__init__(session)
        self.type = type

    @property
    def model_class(self) -> type[_RecipientT]:
        return GenericRecipient.get_polymorphic_class(  # type:ignore
            self.type, GenericRecipient)  # type:ignore[arg-type]

    def query(self) -> Query[_RecipientT]:
        return super().query().order_by(self.model_class.order)
