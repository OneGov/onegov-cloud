from onegov.core.orm.mixins import content_property
from onegov.recipient import GenericRecipient, GenericRecipientCollection


class ResourceRecipient(GenericRecipient):
    __mapper_args__ = {'polymorphic_identity': 'resource'}

    send_on = content_property()
    resources = content_property()


class ResourceRecipientCollection(GenericRecipientCollection):
    def __init__(self, session):
        super().__init__(session, type='resource')
