from cached_property import cached_property

from onegov.core.collection import GenericCollection


class FsiNotificationTemplateCollection(GenericCollection):

    @cached_property
    def model_class(self):

        # XXX circular import
        from onegov.fsi.models.notification_template import \
            FsiNotificationTemplate
        return FsiNotificationTemplate

    def query(self):
        query = super().query()
        return query
