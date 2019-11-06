from cached_property import cached_property

from onegov.core.collection import GenericCollection


class FsiNotificationTemplateCollection(GenericCollection):

    def __init__(self, session, owner_id=None):
        super().__init__(session)
        self.owner_id = owner_id

    @cached_property
    def model_class(self):

        # XXX circular import
        from onegov.fsi.models.notification_template import \
            FsiNotificationTemplate
        return FsiNotificationTemplate

    def query(self):
        query = super().query()
        query.filter_by(owner_id=self.owner_id)
        return query
