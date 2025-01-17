from __future__ import annotations

from onegov.chat.models import TextModule
from onegov.core.collection import GenericCollection
from sqlalchemy import or_


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session


class TextModuleCollection(GenericCollection[TextModule]):

    def __init__(
        self,
        session: Session,
        type: str = '*',
        handler: str = 'ALL',
        owner: str = '*'
    ):
        super().__init__(session)
        self.type = type
        self.handler = handler
        self.owner = owner

    @property
    def model_class(self) -> type[TextModule]:
        return TextModule

    def query(self) -> Query[TextModule]:
        query = super().query()

        if self.owner != '*':
            query = query.filter(or_(
                TextModule.user_id == self.owner,
                TextModule.user_id.is_(None)
            ))
        else:
            query = query.filter(TextModule.user_id.is_(None))

        if self.type != '*':
            query = query.filter(TextModule.message_type == self.type)

        if self.handler != 'ALL':
            query = query.filter(TextModule.handler_code == self.handler)

        return query
