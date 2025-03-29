from __future__ import annotations
import json
from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultLayout
from onegov.org.models import PushNotificationCollection
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.html(
    model=PushNotificationCollection, template='push_notifications.pt',
    permission=Private,
)
def view_push_notifications(
    self: PushNotificationCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None,
) -> RenderData:
    notifications = self.query().all()
    # Create a dictionary of formatted response data
    formatted_responses = {}

    for notification in notifications:
        if notification.response_data:
            # Pretty-print the JSON for better readability
            formatted_responses[notification.id] = json.dumps(
                notification.response_data,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )

    return {
        'layout': layout or DefaultLayout(self, request),
        'title': _('Push Notifications'),
        'notifications': notifications,
        'formatted_responses': formatted_responses,
        'is_sent': lambda notification: (
                notification.response_data and
                notification.response_data.get('status') == 'sent'
        )
    }
