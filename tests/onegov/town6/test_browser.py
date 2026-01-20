from __future__ import annotations

import functools
import pytest
import transaction

from datetime import timedelta
from onegov.org.models import PushNotification
from onegov.org.models.page import News
import json
from onegov.org.notification_service import (
    TestNotificationService,
    set_test_notification_service,
)
from sedate import utcnow, to_timezone, ensure_timezone
from sqlalchemy import exists
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url
from tests.onegov.org.test_cronjobs import register_echo_handler
from tests.shared import ExtendedBrowser


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.ticket.handler import HandlerRegistry
    from tests.shared.browser import ExtendedBrowser
    from .conftest import TestTownApp


@pytest.mark.xdist_group(name="browser")
def test_firebase_settings_form_and_push_notification_flow(
    browser: ExtendedBrowser,
    town_app: TestTownApp,
    handlers: HandlerRegistry
) -> None:
    # Adding patches until either the test passes or we run out of monkeys
    monkey_patch_fill_for_element_not_interactable(browser)
    monkey_patch_visit_to_ignore_console_errors(browser)

    browser.login_admin()

    browser.visit('/firebase')

    # 1. Test with invalid Firebase credentials (missing required keys)
    invalid_credentials = {
        "type": "service_account",
        "project_id": "test-project",
        # Missing private_key_id
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANB"
                       "gk=\n-----END PRIVATE KEY-----\n",
        # Missing client_email
        "client_id": "test-client-id",
        # Missing other required fields
    }
    assert browser.is_element_present_by_name('firebase_adminsdk_credential')
    browser.fill('firebase_adminsdk_credential', invalid_credentials)  # type: ignore[arg-type]

    browser.find_by_value('Speichern').click()
    assert browser.is_text_present(
        'Error validating Firebase credentials: Missing required keys'
    )

    # 4. Test with valid json
    assert browser.is_element_present_by_name('firebase_adminsdk_credential')
    browser.fill('firebase_adminsdk_credential', {  # type: ignore[arg-type]
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBA"
                       "jiDANBgk=\n-----END PRIVATE KEY-----\n",
        "client_email": "test@example.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth3/auth",
        "token_uri": "https://oauth3.googleapis.com/token",
        "auth_provider_x509_cert_url":
            "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url":
            "https://www.googleapis.com/robot/v1/metadata/x509/test%40example.com",
        "universe_domain": "googleapis.com"
    })


    # send with default topic (all News have it by default)
    browser.find_by_value('Speichern').click()
    assert not browser.is_text_present('Ungültiges JSON-Format')

    now = utcnow()
    create_news_with_push_notification(browser, now, title='foo')

    # test News was saved to the db
    query = town_app.session().query(News)
    query = query.filter(News.published == True)
    query = query.filter(News.publication_start <= now)
    only_public_with_send_push_notification = query.filter(
        News.meta['send_push_notifications_to_app'].astext == 'true'
    )
    assert only_public_with_send_push_notification.count() == 1

    # Might as well test the cronjob as well.
    # Dependency Injection of the Test Double:
    test_service = TestNotificationService()
    set_test_notification_service(test_service)

    register_echo_handler(handlers)
    job = get_cronjob_by_name(town_app, 'send_push_notifications_for_news')
    assert job is not None
    job.app = town_app
    transaction.begin()
    browser.visit(get_cronjob_url(job))
    transaction.commit()

    assert (town_app.session()
        .query(exists().where(PushNotification.id.isnot(None)))
        .scalar()
    )

    # Deleting the news should be no problem
    browser.visit('/news/foo')
    browser.find_by_value('Löschen').click()

    # and delete the push notification
    browser.visit('/push-notifications')
    browser.find_by_value('Keine Benachrichtigungen')


def create_news_with_push_notification(
    browser: ExtendedBrowser,
    dt: datetime,
    title: str = 'My push notification News'
) -> None:
    # in a real browser scenario, form submission is is timezone naive, but the
    # user of course still selects in local time. Regardless Europe/Zurich
    # is assumed throughout the codebase.
    local_publication_start = to_timezone(
        dt, ensure_timezone('Europe/Zurich')
    )
    browser.visit('/news')
    new_news_link = browser.find_by_css(
        'a.new-news.show-new-content-placeholder'
    ).first['href']
    browser.visit(new_news_link)
    browser.fill('title', title)
    browser.set_datetime_element(
        '#publication_start', local_publication_start
    )
    assert browser.find_by_css('#send_push_notifications_to_app') is not None
    browser.execute_script(
        "document.querySelector('#send_push_notifications_to_app').click()"
    )
    # So now the firebase topic to select has appeared:
    assert browser.find_by_id('push_notifications-0').is_visible()
    # The firebase topic should be auto selected – there is only one
    # See auto_select_topic_id_if_only_one_exists() in forms.js
    assert browser.find_by_id('push_notifications-0').checked is True
    # Save the news item

    browser.find_by_value('Speichern').click()


@pytest.mark.xdist_group(name="browser")
def test_firebase_push_notifications_date_in_future_should_not_send(
    browser: ExtendedBrowser,
    town_app: TestTownApp,
    handlers: HandlerRegistry
) -> None:

    session = town_app.session()
    monkey_patch_fill_for_element_not_interactable(browser)
    monkey_patch_visit_to_ignore_console_errors(browser)

    browser.login_admin()

    browser.visit('/firebase')

    assert browser.is_element_present_by_name('firebase_adminsdk_credential')
    browser.fill('firebase_adminsdk_credential', {  # type: ignore[arg-type]
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBA"
                       "jiDANBgk=\n-----END PRIVATE KEY-----\n",
        "client_email": "test@example.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth3/auth",
        "token_uri": "https://oauth3.googleapis.com/token",
        "auth_provider_x509_cert_url":
            "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url":
            "https://www.googleapis.com/robot/v1/metadata/x509/test%40example.com",
        "universe_domain": "googleapis.com"
    })

    # send with default topic (all News have it by default)
    browser.find_by_value('Speichern').click()
    assert not browser.is_text_present('Ungültiges JSON-Format')

    # Create a publication some time in the future
    in_one_hour = utcnow() + timedelta(hours=1)

    create_news_with_push_notification(browser, in_one_hour, title='1 h')

    test_service = TestNotificationService()
    set_test_notification_service(test_service)

    register_echo_handler(handlers)
    job = get_cronjob_by_name(town_app, 'send_push_notifications_for_news')
    assert job is not None
    job.app = town_app
    transaction.begin()
    browser.visit(get_cronjob_url(job))
    transaction.commit()
    no = session.query(PushNotification).all()

    assert not (session.query(exists().where(PushNotification.id.isnot(None)))
        .scalar()
    )

@pytest.mark.xdist_group(name="browser")
def test_send_push_notification_checkbox_not_present_by_default(
    browser: ExtendedBrowser,
    town_app: TestTownApp
) -> None:

    monkey_patch_visit_to_ignore_console_errors(browser)
    browser.login_admin()
    browser.visit('/news')
    new_news_link = browser.find_by_css(
        'a.new-news.show-new-content-placeholder'
    ).first['href']
    browser.visit(new_news_link)

    # By default the push notification checkbox should not be present at all
    # Because it's a disabled extension
    assert not browser.find_by_id('send_push_notifications_to_app')


def monkey_patch_fill_for_element_not_interactable(
    browser: ExtendedBrowser
) -> None:
    """ Prevent `ElementNotInteractableException` error for text in textarea.

    The caller is not aware of this, but if we can't fill in text we do the
    following: Clicking the element and literally simulating the keypresses
    for each char in the text to fill.

     """
    original_fill = browser.__class__.fill
    def custom_fill(
        self: ExtendedBrowser,
        name: str,
        value: str | dict[str, Any]
    ) -> Any:
        if name == 'firebase_adminsdk_credential':
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)

            # If the element exists, use the specialized method
            if self.is_element_present_by_name(name):
                ace_editor_present = self.is_element_present_by_css(
                    '.ace_editor'
                )
                if ace_editor_present:
                    return self.interact_with_ace_editor(content=value)

        return original_fill(self, name, value)  # type: ignore[arg-type]

    browser.__class__.fill = custom_fill  # type: ignore[assignment, method-assign]


def monkey_patch_visit_to_ignore_console_errors(
    browser: ExtendedBrowser
) -> None:
    """ A lot of times, completely unrelated console errors make the test
    fail. So we avoid this by patching it for this session."""
    original_visit = browser.visit
    browser.visit = functools.partial(  # type: ignore[method-assign]
        original_visit, ignore_all_console_errors=True
    )
