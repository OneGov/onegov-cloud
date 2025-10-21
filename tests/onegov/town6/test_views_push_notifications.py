from __future__ import annotations

import json
import transaction

from freezegun import freeze_time
from onegov.org.models import PushNotification
from onegov.page import PageCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_push_notification_overview(client: Client) -> None:
    transaction.begin()
    session = client.app.session()
    collection = PageCollection(session)
    news = collection.add_root("News", type='news')
    news_1 = collection.add(news, title='One', type='news', lead='lead')
    session.add(news_1)
    session.flush()
    news_id = news_1.id

    with freeze_time('2016-09-01 12:00'):
        PushNotification.record_sent_notification(
            session,
            news_id,
            "topic1",
            {
                "message_id": "projects/test/messages/1234",
                "status": "sent",
                "timestamp": "2025-03-07T21:50:29.135133+00:00",
            },
        )
    transaction.commit()

    client.login_admin()
    page = client.get('/push-notifications')
    assert 'Keine Benachrichtigungen' not in page
    # Get the message text
    message_text = page.pyquery(
        '.notifications table tbody tr.sent-notification td:nth-child(1)'
    )[0].text
    assert message_text == "One"

    # Get the topic
    topic = page.pyquery(
        '.notifications table tbody tr.sent-notification td:nth-child(2)'
    )[0].text
    assert topic == "topic1"

    # Get the sent date
    sent_date = page.pyquery(
        '.notifications table tbody tr.sent-notification td:nth-child(3)'
    )[0].text

    # Ensure time is displayed correctly with timezone
    assert sent_date == "01.09.2016 14:00"

    # Get the Firebase message_id from the pre JSON
    parsed_data = json.loads(page.pyquery(
        '.notifications table tbody tr.sent-notification td:nth-child(4) pre'
        )[0].text)
    assert parsed_data['message_id'] == 'projects/test/messages/1234'
    assert parsed_data['status'] == 'sent'
