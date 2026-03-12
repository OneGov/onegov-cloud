from __future__ import annotations

from functools import cached_property
from onegov.core.collection import GenericCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.models import NotificationTemplate


class NotificationTemplateCollection(
    GenericCollection['NotificationTemplate']
):

    @cached_property
    def model_class(self) -> type[NotificationTemplate]:

        # XXX circular import
        from onegov.feriennet.models import NotificationTemplate
        return NotificationTemplate
