from __future__ import annotations

from onegov.fsi.models.course_event import (
    COURSE_EVENT_STATUSES_TRANSLATIONS, COURSE_EVENT_STATUSES
)
from onegov.fsi.models.course_notification_template import (
    NOTIFICATION_TYPE_TRANSLATIONS, NOTIFICATION_TYPES)
from onegov.town6.layout import DefaultLayout as BaseLayout
from onegov.fsi import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.app import FsiApp
    from onegov.fsi.models.course_event import EventStatusType
    from onegov.fsi.models.course_notification_template import NotificationType
    from onegov.fsi.request import FsiRequest


class FormatMixin:

    request: FsiRequest

    @staticmethod
    def format_status(model_status: EventStatusType) -> str:
        return COURSE_EVENT_STATUSES_TRANSLATIONS[
            COURSE_EVENT_STATUSES.index(model_status)
        ]

    @staticmethod
    def format_notification_type(notification_type: NotificationType) -> str:
        return NOTIFICATION_TYPE_TRANSLATIONS[
            NOTIFICATION_TYPES.index(notification_type)
        ]

    def format_boolean(self, val: bool) -> str:
        assert isinstance(val, bool)
        return self.request.translate(_('Yes') if val else _('No'))


class DefaultLayout(BaseLayout, FormatMixin):

    app: FsiApp
    request: FsiRequest

    def instance_link(self, instance: object) -> str:
        return self.request.link(instance)
