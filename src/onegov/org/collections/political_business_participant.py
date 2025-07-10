from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.org.models import PoliticalBusinessParticipation

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class PoliticalBusinessParticipationCollection(
    GenericCollection[PoliticalBusinessParticipation]
):

    def __init__(self, session: Session, active: bool | None = None):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[PoliticalBusinessParticipation]:
        return PoliticalBusinessParticipation
