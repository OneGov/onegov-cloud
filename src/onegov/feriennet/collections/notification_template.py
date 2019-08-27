from cached_property import cached_property
from onegov.core.collection import GenericCollection


class NotificationTemplateCollection(GenericCollection):

    @cached_property
    def model_class(self):

        # XXX circular import
        from onegov.feriennet.models import NotificationTemplate
        return NotificationTemplate
