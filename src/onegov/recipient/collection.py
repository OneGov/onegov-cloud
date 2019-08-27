from onegov.core.collection import GenericCollection
from onegov.recipient.model import GenericRecipient


class GenericRecipientCollection(GenericCollection):

    def __init__(self, session, type):
        super().__init__(session)
        self.type = type

    @property
    def model_class(self):
        return GenericRecipient.get_polymorphic_class(
            self.type, GenericRecipient)
