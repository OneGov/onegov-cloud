from onegov.core.orm.mixins import content_property
from onegov.recipient import GenericRecipient, GenericRecipientCollection


class ResourceRecipient(GenericRecipient):
    __mapper_args__ = {'polymorphic_identity': 'resource'}

    daily_reservations = content_property()
    new_reservations = content_property()
    internal_notes = content_property()
    send_on = content_property()
    rejected_reservations = content_property()
    resources = content_property()


class ResourceRecipientCollection(GenericRecipientCollection):
    def __init__(self, session):
        super().__init__(session, type='resource')
