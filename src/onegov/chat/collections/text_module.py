from onegov.chat.models import TextModule
from onegov.core.collection import GenericCollection
from sqlalchemy import or_


class TextModuleCollection(GenericCollection):

    def __init__(self, session, type='*', handler='ALL', owner='*'):
        super().__init__(session)
        self.type = type
        self.handler = handler
        self.owner = owner

    @property
    def model_class(self):
        return TextModule

    def query(self):
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
