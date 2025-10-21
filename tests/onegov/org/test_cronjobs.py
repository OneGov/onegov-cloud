from __future__ import annotations

import json
import logging
import os
import pytest
import requests
import transaction

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from freezegun import freeze_time
from markupsafe import Markup
from onegov.core.utils import Bunch, normalize_for_url
from onegov.directory import (DirectoryEntryCollection,
                              DirectoryConfiguration,
                              DirectoryCollection)
from onegov.directory.collections.directory import EntryRecipientCollection
from onegov.event import EventCollection, OccurrenceCollection, Event
from onegov.event.utils import as_rdates
from onegov.form import FormSubmissionCollection
from onegov.org.models import (
    ResourceRecipientCollection, News, PushNotification)
from onegov.org.models.page import NewsCollection
from onegov.org.models.resource import RoomResource
from onegov.org.models.ticket import ReservationHandler, DirectoryEntryHandler
from onegov.org.notification_service import (
    TestNotificationService, set_test_notification_service)
from onegov.page import PageCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.user import UserCollection
from onegov.newsletter import (Newsletter, NewsletterCollection,
                               RecipientCollection)
from onegov.reservation import ResourceCollection
from onegov.user.collections import TANCollection
from pathlib import Path
from sedate import ensure_timezone, to_timezone, utcnow
from sqlalchemy.orm import close_all_sessions
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url
from tests.onegov.org.common import register_echo_handler
from tests.onegov.org.conftest import Client
from tests.shared.utils import add_reservation
from unittest.mock import patch, Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.org.models import ExtendedDirectory
    from onegov.ticket.handler import HandlerRegistry
    from sqlalchemy.orm import Session
    from tests.shared.capturelog import CaptureLogFixture
    from .conftest import TestOrgApp


def register_reservation_handler(handlers: HandlerRegistry) -> None:
    handlers.register('RSV', ReservationHandler)


def register_directory_handler(handlers: HandlerRegistry) -> None:
    handlers.register('DIR', DirectoryEntryHandler)


def test_daily_ticket_statistics(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_echo_handler(handlers)

    job = get_cronjob_by_name(client.app, 'daily_ticket_statistics')
    assert job is not None
    job.app = client.app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = client.app.session()
    collection = TicketCollection(session)

    tickets = [
        collection.open_ticket(
            handler_id='1',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='3',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='4',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='5',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='6',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        )
    ]

    # those will be ignored as they are inactive or not editors/admins
    request: Any = Bunch(client_addr='127.0.0.1')
    UserCollection(session).register('a', 'p@ssw0rd', request, role='editor')
    UserCollection(session).register('b', 'p@ssw0rd', request, role='member')

    users = UserCollection(session).query().all()
    user = users[0]
    users[0].data = {'ticket_statistics': 'daily'}

    for ticket in tickets:
        ticket.created = datetime(2016, 1, 2, 10, tzinfo=tz)

    for pending in tickets[1:3]:
        pending.accept_ticket(user)
        pending.modified = datetime(2016, 1, 2, 10, tzinfo=tz)

    for closed in tickets[3:6]:
        closed.accept_ticket(user)
        closed.close_ticket()
        closed.modified = datetime(2016, 1, 2, 10, tzinfo=tz)

    transaction.commit()

    with freeze_time(datetime(2016, 1, 4, tzinfo=tz)):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message is not None

    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert 'List-Unsubscribe' in headers
    assert 'List-Unsubscribe-Post' in headers
    unsubscribe = headers['List-Unsubscribe'].strip('<>')
    assert message['Subject'] == 'Govikon OneGov Cloud Status'
    txt = message['TextBody']
    assert "Folgendes ist während des Wochenendes auf der Govikon" in txt
    assert "6 Tickets wurden eröffnet." in txt
    assert "2 Tickets wurden angenommen." in txt
    assert "3 Tickets wurden geschlossen." in txt
    assert "Zur Zeit ist 1 Ticket " in txt
    assert "/tickets/ALL/open?page=0" in txt
    assert "2 Tickets sind " in txt
    assert "/tickets/ALL/pending?page=0" in txt
    assert "Wir wünschen Ihnen eine schöne Woche!" in txt
    assert "/unsubscribe?token=" in txt
    assert "abmelden" in txt
    assert unsubscribe in txt

    # do not run on the weekends
    with freeze_time(datetime(2016, 1, 2, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 3, tzinfo=tz)):
        client.get(url)

    # no additional mails have been sent
    assert len(os.listdir(client.app.maildir)) == 1


def test_weekly_ticket_statistics(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_echo_handler(handlers)

    job = get_cronjob_by_name(client.app, 'weekly_ticket_statistics')
    assert job is not None
    job.app = client.app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = client.app.session()
    collection = TicketCollection(session)

    tickets = [
        collection.open_ticket(
            handler_id='1',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 5, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 6, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='3',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 7, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='4',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 8, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='5',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 9, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='6',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 10, 10, tzinfo=tz)
        )
    ]

    # those will be ignored as they are inactive or not editors/admins
    request: Any = Bunch(client_addr='127.0.0.1')
    UserCollection(session).register('a', 'p@ssw0rd', request, role='editor')
    UserCollection(session).register('b', 'p@ssw0rd', request, role='member')

    users = UserCollection(session).query().all()
    user = users[0]
    users[1].data = {'ticket_statistics': 'never'}

    for index, ticket in enumerate(tickets):
        ticket.created = datetime(2016, 1, 5 + index, 10, tzinfo=tz)

    for pending in tickets[1:3]:
        pending.accept_ticket(user)
        pending.modified = datetime(2016, 1, 9, 10, tzinfo=tz)

    for closed in tickets[3:6]:
        closed.accept_ticket(user)
        closed.close_ticket()
        closed.modified = datetime(2016, 1, 10, 10, tzinfo=tz)

    transaction.commit()

    with freeze_time(datetime(2016, 1, 11, tzinfo=tz)):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message is not None

    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert 'List-Unsubscribe' in headers
    assert 'List-Unsubscribe-Post' in headers
    unsubscribe = headers['List-Unsubscribe'].strip('<>')
    assert message['Subject'] == 'Govikon OneGov Cloud Status'
    txt = message['TextBody']
    assert "Folgendes ist während der letzten Woche auf der Govikon" in txt
    assert "6 Tickets wurden eröffnet." in txt
    assert "2 Tickets wurden angenommen." in txt
    assert "3 Tickets wurden geschlossen." in txt
    assert "Zur Zeit ist 1 Ticket " in txt
    assert "/tickets/ALL/open?page=0" in txt
    assert "2 Tickets sind " in txt
    assert "/tickets/ALL/pending?page=0" in txt
    assert "Wir wünschen Ihnen eine schöne Woche!" in txt
    assert "/unsubscribe?token=" in txt
    assert "abmelden" in txt
    assert unsubscribe in txt

    # we only run on mondays
    with freeze_time(datetime(2016, 1, 5, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 6, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 7, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 8, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 9, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 10, tzinfo=tz)):
        client.get(url)

    # no additional mails have been sent
    assert len(os.listdir(client.app.maildir)) == 1


def test_monthly_ticket_statistics(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_echo_handler(handlers)

    job = get_cronjob_by_name(client.app, 'monthly_ticket_statistics')
    assert job is not None
    job.app = client.app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = client.app.session()
    collection = TicketCollection(session)

    tickets = [
        collection.open_ticket(
            handler_id='1',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 4, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 9, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='3',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 14, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='4',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 19, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='5',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 24, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='6',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 29, 10, tzinfo=tz)
        )
    ]

    # those will be ignored as they are inactive or not editors/admins
    request: Any = Bunch(client_addr='127.0.0.1')
    UserCollection(session).register('a', 'p@ssw0rd', request, role='editor')
    UserCollection(session).register('b', 'p@ssw0rd', request, role='member')

    users = UserCollection(session).query().all()
    user = users[0]
    users[0].data = {'ticket_statistics': 'monthly'}

    for index, ticket in enumerate(tickets):
        ticket.created = datetime(2016, 1, 4 + index * 5, 10, tzinfo=tz)

    for pending in tickets[2:3]:
        pending.accept_ticket(user)
        pending.modified = datetime(2016, 1, 22, 10, tzinfo=tz)

    for closed in tickets[3:6]:
        closed.accept_ticket(user)
        closed.close_ticket()
        closed.modified = datetime(2016, 1, 31, 10, tzinfo=tz)

    transaction.commit()

    with freeze_time(datetime(2016, 2, 1, tzinfo=tz)):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message is not None

    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert 'List-Unsubscribe' in headers
    assert 'List-Unsubscribe-Post' in headers
    unsubscribe = headers['List-Unsubscribe'].strip('<>')
    assert message['Subject'] == 'Govikon OneGov Cloud Status'
    txt = message['TextBody']
    assert "Folgendes ist während des letzten Monats auf der Govikon" in txt
    assert "6 Tickets wurden eröffnet." in txt
    assert "1 Ticket wurde angenommen." in txt
    assert "3 Tickets wurden geschlossen." in txt
    assert "Zur Zeit sind 2 Tickets " in txt
    assert "/tickets/ALL/open?page=0" in txt
    assert "1 Ticket ist " in txt
    assert "/tickets/ALL/pending?page=0" in txt
    assert "Wir wünschen Ihnen eine schöne Woche!" in txt
    assert "/unsubscribe?token=" in txt
    assert "abmelden" in txt
    assert unsubscribe in txt

    # we only run on first monday of the month
    with freeze_time(datetime(2016, 2, 2, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 3, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 4, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 5, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 6, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 7, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 8, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 15, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 22, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 29, tzinfo=tz)):
        client.get(url)

    # no additional mails have been sent
    assert len(os.listdir(client.app.maildir)) == 1


def test_daily_reservation_overview(client: Client[TestOrgApp]) -> None:
    resources = ResourceCollection(client.app.libres_context)
    gymnasium = resources.add('Gymnasium', 'Europe/Zurich', type='room')
    dailypass = resources.add('Dailypass', 'Europe/Zurich', type='daypass')
    assert isinstance(gymnasium, RoomResource)

    gymnasium.definition = """
        Name = ___
    """

    gym_allocation = gymnasium.scheduler.allocate(
        (datetime(2017, 1, 6, 12), datetime(2017, 1, 6, 16)),
        partly_available=True,
    )[0]

    day_allocation = dailypass.scheduler.allocate(
        (datetime(2017, 1, 6, 12), datetime(2017, 1, 6, 16)),
        partly_available=False,
        whole_day=True
    )[0]

    gym_reservation_token = gymnasium.scheduler.reserve(
        'gym-reservation@example.org',
        (gym_allocation.start, gym_allocation.end),
    )

    day_reservation_token = dailypass.scheduler.reserve(
        'day-reservation@example.org',
        (day_allocation.start, day_allocation.end)
    )

    gymnasium.scheduler.approve_reservations(gym_reservation_token)
    dailypass.scheduler.approve_reservations(day_reservation_token)

    submissions = FormSubmissionCollection(client.app.session())
    submissions.add_external(
        form=gymnasium.form_class(data={'name': '0xdeadbeef'}),  # type: ignore[misc]
        state='complete',
        id=gym_reservation_token
    )

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='Gym',
        medium='email',
        address='gym@example.org',
        daily_reservations=True,
        send_on=['FR'],
        resources=[
            gymnasium.id.hex
        ]
    )
    recipients.add(
        name='Day',
        medium='email',
        address='day@example.org',
        daily_reservations=True,
        send_on=['FR'],
        resources=[
            dailypass.id.hex
        ]
    )
    recipients.add(
        name='Both',
        medium='email',
        address='both@example.org',
        daily_reservations=True,
        send_on=['SA'],
        resources=[
            dailypass.id.hex,
            gymnasium.id.hex
        ]
    )

    transaction.commit()

    job = get_cronjob_by_name(client.app, 'daily_resource_usage')
    assert job is not None
    job.app = client.app

    url = get_cronjob_url(job)
    tz = ensure_timezone('Europe/Zurich')

    # do not send an e-mail outside the selected days
    for day in [2, 3, 4, 5, 8]:
        with freeze_time(datetime(2017, 1, day, tzinfo=tz), tick=True):
            client.get(url)

            assert len(os.listdir(client.app.maildir)) == 0

    # only send e-mails to the users with the right selection
    with freeze_time(datetime(2017, 1, 6, tzinfo=tz), tick=True):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 2

    with freeze_time(datetime(2017, 1, 7, tzinfo=tz), tick=True):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 3

    # there are no really confirmed reservations at this point, so the
    # e-mail will not contain any information info
    client.flush_email_queue()

    with freeze_time(datetime(2017, 1, 6, tzinfo=tz), tick=True):
        client.get(url)

    mails = [client.get_email(i) for i in range(2)]
    for mail in mails:
        assert mail is not None
        assert "Heute keine Reservationen" in mail['TextBody']
        assert "-reservation" not in mail['TextBody']

    # NOTE: These seem to not always get sent in the same order...
    #       technically we don't really care so let's determine order
    assert mails[0] is not None
    if mails[0]['To'] == 'gym@example.org':
        gym_mail, day_mail = mails
    else:
        day_mail, gym_mail = mails
    assert gym_mail is not None
    assert gym_mail['To'] == 'gym@example.org'
    assert "Allgemein - Gymnasium" in gym_mail['TextBody']
    assert "Allgemein - Dailypass" not in gym_mail['TextBody']

    assert day_mail is not None
    assert day_mail['To'] == 'day@example.org'
    assert "Allgemein - Dailypass" in day_mail['TextBody']
    assert "Allgemein - Gymnasium" not in day_mail['TextBody']

    # once we confirm the reservation it shows up in the e-mail
    client.flush_email_queue()

    gymnasium = resources.by_name('gymnasium')  # type: ignore[assignment]
    r = gymnasium.scheduler.reservations_by_token(gym_reservation_token)[0]
    r.data = {'accepted': True}

    transaction.commit()

    with freeze_time(datetime(2017, 1, 6, tzinfo=tz), tick=True):
        client.get(url)

    with freeze_time(datetime(2017, 1, 7, tzinfo=tz), tick=True):
        client.get(url)

    # NOTE: These seem to not always get sent in the same order...
    #       technically we don't really care so let's determine order
    if '0xdeadbeef' in client.get_email(0)['TextBody']:
        assert '0xdeadbeef' not in client.get_email(1)['TextBody']
    else:
        assert '0xdeadbeef' in client.get_email(1)['TextBody']

    mail = client.get_email(2)
    assert mail is not None
    assert mail['To'] == 'both@example.org'
    assert 'Gymnasium' in mail['TextBody']
    assert 'Dailypass' in mail['TextBody']
    assert '0xdeadbeef' not in mail['TextBody']  # diff. day

    # this also works for the other reservation which has no data
    client.flush_email_queue()

    dailypass = resources.by_name('dailypass')  # type: ignore[assignment]
    r = dailypass.scheduler.reservations_by_token(day_reservation_token)[0]
    r.data = {'accepted': True}

    transaction.commit()

    with freeze_time(datetime(2017, 1, 6, tzinfo=tz), tick=True):
        client.get(url)

    # NOTE: These seem to not always get sent in the same order...
    #       technically we don't really care so let's determine order
    text = client.get_email(0)['TextBody']
    if 'day-reservation' in text:
        assert 'gym-reservation' not in text
    else:
        assert 'gym-reservation' in text

    text = client.get_email(1)['TextBody']
    if 'gym-reservation' in text:
        assert 'day-reservation' not in text
    else:
        assert 'day-reservation' in text


@pytest.mark.parametrize('secret_content_allowed', [False, True])
def test_send_scheduled_newsletters(
    client: Client[TestOrgApp],
    secret_content_allowed: bool
) -> None:

    def create_scheduled_newsletter() -> None:
        with freeze_time('2018-05-31 12:00'):
            news_public = news.add(
                news_parent, 'Public News', 'public-news',
                type='news', access='public')
            news_public_2 = news.add(
                news_parent,
                'Public News - not published',
                'public-news-not-published',
                type='news', access='public',
                publication_start=utcnow() + timedelta(days=1),
                publication_end=utcnow() + timedelta(days=2))
            news_secret = news.add(
                news_parent, 'Secret News', 'secret-news',
                type='news', access='secret')
            news_private = news.add(
                news_parent, 'Private News', 'private-news',
                type='news', access='private')
            newsletters.add(
                "Latest News",
                Markup("<h1>Latest News</h1>"),
                content={"news": [
                    str(news_public.id),
                    str(news_public_2.id),
                    str(news_secret.id),
                    str(news_private.id)
                ]},
                scheduled=utcnow()
            )

            transaction.commit()

    session = client.app.session()
    news = PageCollection(session)
    news_parent = news.query().filter_by(name='news').one()
    newsletters = NewsletterCollection(session)
    recipients = RecipientCollection(session)

    recipient = recipients.add('info@example.org')
    recipient.confirmed = True

    client.app.org.secret_content_allowed = secret_content_allowed
    client.app.org.enable_automatic_newsletters = True

    create_scheduled_newsletter()

    job = get_cronjob_by_name(client.app, 'hourly_maintenance_tasks')
    assert job is not None
    job.app = client.app

    with freeze_time('2018-05-31 11:00'):
        client.get(get_cronjob_url(job))
        newsletter = newsletters.query().one()

        assert newsletter.scheduled  # still scheduled, not sent yet
        assert len(os.listdir(client.app.maildir)) == 0

    with freeze_time('2018-05-31 12:00'):
        client.get(get_cronjob_url(job))
        newsletter = newsletters.query().one()

        assert not newsletter.scheduled
        assert len(os.listdir(client.app.maildir)) == 1

        mail_file = Path(client.app.maildir) / os.listdir(client.app.maildir)[
            0]
        with open(mail_file, 'r') as file:
            mail = json.loads(file.read())[0]
            assert "info@example.org" == mail['To']
            assert "Latest News" in mail['Subject']
            assert "Public News" in mail['TextBody']
            assert "Public News - not published" not in mail['TextBody']
            if secret_content_allowed:
                assert "Secret News" in mail['TextBody']
            assert "Private News" not in mail['TextBody']


def test_send_daily_newsletter(client: Client[TestOrgApp]) -> None:
    tz = ensure_timezone('Europe/Zurich')

    session = client.app.session()
    client.app.org.enable_automatic_newsletters = True
    client.app.org.daily_newsletter_title = 'News aus Govikon'
    client.app.org.newsletter_times = ['10', '11', '16']

    news = PageCollection(session)
    news_parent = news.query().filter_by(name='news').one()
    recipients = RecipientCollection(session)

    recipient = recipients.add('daily@example.org', confirmed=True)
    recipient.daily_newsletter = True

    recipient = recipients.add('info@example.org', confirmed=True)
    recipient.daily_newsletter = False

    with freeze_time(datetime(2018, 3, 2, 17, 0, tzinfo=tz)):
        # Created three days ago, published yesterday at 17:00
        news.add(
            parent=news_parent, title='News1', type='news', access='public',
            publication_start=utcnow() + timedelta(days=2))

    with freeze_time(datetime(2018, 3, 4, 17, 0, tzinfo=tz)):
        # Created yesterday at 17:00, published immediately
        news.add(
            parent=news_parent, title='News2', type='news', access='public')

    with freeze_time(datetime(2018, 3, 5, 10, 0, tzinfo=tz)):
        # Created today at 10:00, published immediately
        news.add(
            parent=news_parent, title='News3', type='news', access='public')
        # Created today at 10:00, published today 10:01
        news.add(
            parent=news_parent, title='News4', type='news', access='public',
            publication_start=utcnow() + timedelta(minutes=1))

    transaction.commit()

    job = get_cronjob_by_name(client.app, 'hourly_maintenance_tasks')
    assert job is not None
    job.app = client.app

    with freeze_time(datetime(2018, 3, 5, 10, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        newsletter = NewsletterCollection(session).query().one()
        assert newsletter.title == 'Täglicher Newsletter 05.03.2018, 10:00'
        assert len(os.listdir(client.app.maildir)) == 1
        mail = client.get_email(0)
        assert mail is not None
        assert "News aus Govikon" in mail['Subject']
        assert "News1" in mail['TextBody']
        assert "News2" in mail['TextBody']
        assert "News3" not in mail['TextBody']
        assert "News4" not in mail['TextBody']

    with freeze_time(datetime(2018, 3, 5, 11, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        newsletter = NewsletterCollection(session).query().filter(
            Newsletter.title.like('%Täglicher Newsletter 05.03.2018, 11:00%'
        )).one()
        assert 'Täglicher Newsletter 05.03.2018, 11:00' in newsletter.title
        assert len(os.listdir(client.app.maildir)) == 2
        mail = client.get_email(1)
        assert mail is not None
        assert "News aus Govikon" in mail['Subject']
        assert "News1" not in mail['TextBody']
        assert "News2" not in mail['TextBody']
        assert "News3" in mail['TextBody']
        assert "News4" in mail['TextBody']

    with freeze_time(datetime(2018, 3, 5, 16, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert NewsletterCollection(session).query().count() == 2
        assert len(os.listdir(client.app.maildir)) == 2


def test_auto_archive_tickets_and_delete(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_echo_handler(handlers)

    session = client.app.session()
    transaction.begin()

    with freeze_time('2022-08-17 04:30'):
        collection = TicketCollection(session)

        tickets = [
            collection.open_ticket(
                handler_id='1',
                handler_code='EHO',
                title="Title",
                group="Group",
                email="citizen@example.org",
            ),
            collection.open_ticket(
                handler_id='2',
                handler_code='EHO',
                title="Title",
                group="Group",
                email="citizen@example.org",
            ),
        ]

        request: Any = Bunch(client_addr='127.0.0.1')
        UserCollection(session).register(
            'b', 'p@ssw0rd', request, role='admin'
        )
        users = UserCollection(session).query().all()
        user = users[0]
        for t in tickets:
            t.accept_ticket(user)
            t.close_ticket()

        client.app.org.auto_archive_timespan = 30  # days
        client.app.org.auto_delete_timespan = 30  # dclient.
        transaction.commit()

        close_all_sessions()

    # now we go forward a month for archival
    with freeze_time('2022-09-17 04:30'):

        query = session.query(Ticket)
        query = query.filter_by(state='closed')
        assert query.count() == 2

        job = get_cronjob_by_name(client.app, 'archive_old_tickets')
        assert job is not None
        job.app = client.app
        client.get(get_cronjob_url(job))

        query = session.query(Ticket)
        query = query.filter(Ticket.state == 'archived')
        assert query.count() == 2

        # this delete cronjob should have no effect (yet), since archiving
        # resets the `last_change`
        job = get_cronjob_by_name(client.app, 'delete_old_tickets')
        assert job is not None
        job.app = client.app
        client.get(get_cronjob_url(job))

        query = session.query(Ticket)
        query = query.filter(Ticket.state == 'archived')
        assert query.count() == 2

    # and another month for deletion
    with freeze_time('2022-10-17 05:30'):
        session.flush()
        assert client.app.org.auto_delete_timespan is not None

        job = get_cronjob_by_name(client.app, 'delete_old_tickets')
        assert job is not None
        job.app = client.app
        client.get(get_cronjob_url(job))

        # should be deleted
        assert session.query(Ticket).count() == 0


def test_respect_recent_reservation_for_archive(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_echo_handler(handlers)
    register_reservation_handler(handlers)

    transaction.begin()

    resources = ResourceCollection(client.app.libres_context)
    dailypass = resources.add(
        'Dailypass',
        'Europe/Zurich',
        type='daypass'
    )

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        rejected_reservations=True,
        resources=[
            dailypass.id.hex,
        ],
    )

    with freeze_time('2022-06-06 01:00'):
        # First we add some random ticket. Acts Kind of like a 'control
        # group', this is not reservation)
        collection = TicketCollection(client.app.session())
        collection.open_ticket(
            handler_id='1',
            handler_code='EHO',
            title="Control Ticket",
            group="Group",
            email="citizen@example.org",
        )

        # Secondly we add a reservation for one year in advance (indeed not
        # uncommon in practice)
        add_reservation(
            dailypass,
            client.app.session(),
            start=datetime(2023, 6, 6, 4, 30),
            end=datetime(2023, 6, 6, 5, 0),
        )

        # close all the tickets
        tickets_query = TicketCollection(client.app.session()).query()
        assert tickets_query.count() == 2
        user = UserCollection(client.app.session()).query().first()
        assert user is not None
        for ticket in tickets_query:
            ticket.accept_ticket(user)
            ticket.close_ticket()

        client.app.org.auto_archive_timespan = 365  # days
        client.app.org.auto_delete_timespan = 365  # days

        transaction.commit()

        close_all_sessions()

    # now go forward a year
    with freeze_time('2023-06-06 02:00'):

        q = TicketCollection(client.app.session()).query()
        assert q.filter_by(state='open').count() == 0
        assert q.filter_by(state='closed').count() == 2

        job = get_cronjob_by_name(client.app, 'archive_old_tickets')
        assert job is not None
        job.app = client.app
        client.get(get_cronjob_url(job))

        after_cronjob_tickets = TicketCollection(client.app.session()).query()
        for ticket in after_cronjob_tickets:
            if not isinstance(ticket.handler, ReservationHandler):
                # the control ticket has been archived
                assert ticket.state == 'archived'
            else:
                # but the ticket with reservations should not be archived
                # because the lastest reservation is still fairly recent
                assert ticket.state == 'closed'


def test_monthly_mtan_statistics(client: Client[TestOrgApp]) -> None:
    job = get_cronjob_by_name(client.app, 'monthly_mtan_statistics')
    assert job is not None
    job.app = client.app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    # don't send an email if no mTANs have been sent
    with freeze_time(datetime(2016, 2, 1, tzinfo=tz)):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = client.app.session()
    collection = TANCollection(session, scope='test')

    collection.add(  # outside
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2015, 12, 30, 10, tzinfo=tz),
    )
    collection.add(
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2016, 1, 4, 10, tzinfo=tz),
    )
    collection.add(
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2016, 1, 9, 10, tzinfo=tz)
    )
    collection.add(  # not an mtan
        client='1.2.3.4',
        created=datetime(2016, 1, 14, 10, tzinfo=tz)
    )
    collection.add(
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2016, 1, 19, 10, tzinfo=tz)
    )
    collection.add(
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2016, 1, 24, 10, tzinfo=tz)
    )
    collection.add(
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2016, 1, 29, 10, tzinfo=tz)
    )
    collection.add(  # also outside
        client='1.2.3.4',
        mobile_number='+411112233',
        created=datetime(2016, 2, 1, 10, tzinfo=tz)
    )
    transaction.commit()

    with freeze_time(datetime(2016, 2, 1, tzinfo=tz)):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message is not None
    assert message['Subject'] == (
        'Govikon: mTAN Statistik Januar 2016')
    assert "5 mTAN SMS versendet" in message['TextBody']

    # we only run on first monday of the month
    with freeze_time(datetime(2016, 2, 2, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 3, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 4, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 5, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 6, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 7, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 8, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 15, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 22, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 2, 29, tzinfo=tz)):
        client.get(url)

    # no additional mails have been sent
    assert len(os.listdir(client.app.maildir)) == 1


def test_delete_content_marked_deletable__directory_entries(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_directory_handler(handlers)

    job = get_cronjob_by_name(client.app, 'delete_content_marked_deletable')
    assert job is not None
    job.app = client.app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(client.app.session(), type='extended')
    directory_entries = directories.add(
        title='Öffentliche Planauflage',
        structure="""
            Gesuchsteller/in *= ___
            Grundeigentümer/in *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Gesuchsteller/in]",
            order=['Gesuchsteller/in'],
        )
    )

    event = directory_entries.add(values=dict(
        gesuchsteller_in='Anton Antoninio',
        grundeigentumer_in='Berta Bertinio',
        publication_start=datetime(2024, 4, 1, tzinfo=tz),
        publication_end=datetime(2024, 4, 10, tzinfo=tz),
        # delete_when_expired=True,
    ))
    event.delete_when_expired = True

    directory_entries.add(values=dict(
        gesuchsteller_in='Carmine Carminio',
        grundeigentumer_in='Doris Dorinio',
        publication_start=datetime(2024, 4, 3, tzinfo=tz),
        publication_end=datetime(2024, 4, 10, tzinfo=tz),
    ))

    event = directory_entries.add(values=dict(
        gesuchsteller_in='Emil Emilio',
        grundeigentumer_in='Franco Francinio',
        publication_start=datetime(2024, 4, 5, tzinfo=tz),
        publication_end=datetime(2024, 4, 20, tzinfo=tz),
    ))
    event.delete_when_expired = True

    event = directory_entries.add(values=dict(
        gesuchsteller_in='Guido Guidinio',
        grundeigentumer_in='Irene Irinio',
        publication_start=datetime(2024, 4, 7, tzinfo=tz),
        publication_end=datetime(2024, 4, 20, tzinfo=tz),
    ))
    event.delete_when_expired = True

    event = directory_entries.add(values=dict(
        gesuchsteller_in='Johanna Johanninio',
        grundeigentumer_in='Karl Karlinio',
        publication_start=datetime(2024, 4, 22, tzinfo=tz),
        # no end date, never gets deleted
    ))
    event.delete_when_expired = True

    transaction.commit()
    close_all_sessions()

    def count_publications(
        directories: DirectoryCollection[ExtendedDirectory]
    ) -> int:
        applications = directories.by_name('offentliche-planauflage')
        assert applications is not None
        return (DirectoryEntryCollection(applications, type='extended').
                query().count())

    assert count_publications(directories) == 5

    with freeze_time(datetime(2024, 4, 2, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_publications(directories) == 5

    with freeze_time(datetime(2024, 4, 3, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_publications(directories) == 5

    with freeze_time(datetime(2024, 4, 5, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_publications(directories) == 5

    with freeze_time(datetime(2024, 4, 11, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_publications(directories) == 4  # one entry got deleted

    with freeze_time(datetime(2024, 4, 21, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_publications(directories) == 2  # two more entries got
        # deleted

    with freeze_time(datetime(2024, 4, 23, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_publications(directories) == 2  # no end date,
        # never gets deleted

    assert count_publications(directories) == 2


def test_delete_content_marked_deletable__news(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_directory_handler(handlers)

    job = get_cronjob_by_name(client.app, 'delete_content_marked_deletable')
    assert job is not None
    job.app = client.app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()
    collection = PageCollection(client.app.session())
    news = collection.add_root('News', type='news')
    first = collection.add(
        news,
        title='First News',
        type='news',
        lead='First News Lead',
    )
    assert isinstance(first, News)
    first.publication_start = datetime(2024, 4, 1, tzinfo=tz)
    first.publication_end = datetime(2024, 4, 2, 23, 59, tzinfo=tz)
    first.delete_when_expired = True

    two = collection.add(
        news,
        title='Second News',
        type='news',
        lead='Second News Lead'
    )
    assert isinstance(two, News)
    two.publication_start = datetime(2024, 4, 5, tzinfo=tz)
    two.publication_end = datetime(2024, 4, 6, tzinfo=tz)
    two.delete_when_expired = True

    transaction.commit()
    close_all_sessions()

    def count_news() -> int:
        c = PageCollection(client.app.session()).query()
        c = c.filter(News.publication_start.isnot(None))
        c = c.filter(News.publication_end.isnot(None))
        return c.count()

    with freeze_time(datetime(2024, 4, 1, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_news() == 2

    with freeze_time(datetime(2024, 4, 2, 23, 58, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_news() == 2

    with freeze_time(datetime(2024, 4, 3, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_news() == 1

    with freeze_time(datetime(2024, 4, 7, tzinfo=tz)):
        client.get(get_cronjob_url(job))
        assert count_news() == 0


def test_delete_content_marked_deletable__events_occurrences(
    client: Client[TestOrgApp],
    handlers: HandlerRegistry
) -> None:

    register_directory_handler(handlers)

    job = get_cronjob_by_name(client.app, 'delete_content_marked_deletable')
    assert job is not None
    job.app = client.app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    title_1 = 'Antelope Canyon Tour'
    events = EventCollection(client.app.session())
    event_1 = events.add(
        title=title_1,
        start=datetime(2024, 4, 18, 11, 0),
        end=datetime(2024, 4, 18, 13, 0),
        timezone='Europe/Zurich',
        content={
            'description': 'Antelope Canyon is a stunning and picturesque '
                           'slot canyon known for its remarkable sandstone '
                           'formations and light beams, located on Navajo '
                           'land near Page, Arizona.'
        },
        location='Antelope Canyon, Page, Arizona',
        tags=['nature', 'stunning', 'canyon'],
    )
    event_1.recurrence = as_rdates('FREQ=WEEKLY;COUNT=4', event_1.start)
    event_1.submit()
    event_1.publish()  # spawns occurrences

    title_2 = 'Hiking Mount Pilatus'
    event_2 = events.add(
        title=title_2,
        start=datetime(2024, 4, 18, 6, 0),
        end=datetime(2024, 4, 18, 18, 0),
        timezone='Europe/Zurich',
        content={
            'description': 'Wandern ist des Müllers Lust!'
        }
    )
    event_2.recurrence = as_rdates('FREQ=WEEKLY;COUNT=2', event_2.start)
    event_2.submit()
    # not yet accepted and published, no additional occurrences

    transaction.commit()
    close_all_sessions()

    def count_events(title: str) -> int:
        return (EventCollection(client.app.session()).query()
                .filter_by(title=title).count())

    def count_occurrences(title: str) -> int:
        return (OccurrenceCollection(client.app.session(), outdated=True)
                .query().filter_by(title=title).count())

    with (freeze_time(datetime(2024, 4, 18, 6, 0, tzinfo=tz))):
        # default setting, no deletion of past event and past occurrences
        assert client.app.org.delete_past_events is False

        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 4
        assert count_events(title_2) == 1
        assert count_occurrences(title_2) == 0  # as it did not get published

        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 4
        assert count_events(title_2) == 1
        assert count_occurrences(title_2) == 0

        # ogc-2562
        # switch setting and see nothing gets deleted event without occurrences
        # and prior end date
        transaction.begin()
        client.app.org.delete_past_events = True
        transaction.commit()
        close_all_sessions()

        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 4
        assert count_events(title_2) == 1
        assert count_occurrences(title_2) == 0

    with (freeze_time(datetime(2024, 4, 19, 6, 0, tzinfo=tz))):
        # nothing gets deleted due to two cutoff days
        transaction.begin()
        client.app.org.delete_past_events = True
        transaction.commit()
        close_all_sessions()

        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 4
        assert count_events(title_2) == 1
        assert count_occurrences(title_2) == 0

    with (freeze_time(datetime(2024, 4, 20, 6, 0, tzinfo=tz))):
        # nothing gets deleted due to two cutoff days
        transaction.begin()
        client.app.org.delete_past_events = True
        transaction.commit()
        close_all_sessions()

        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 4
        assert count_events(title_2) == 1
        assert count_occurrences(title_2) == 0

    with (freeze_time(datetime(2024, 4, 21, 6, 0, tzinfo=tz))):
        # an old occurrence could be deleted, but the setting is not enabled
        transaction.begin()
        client.app.org.delete_past_events = False
        transaction.commit()
        close_all_sessions()

        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 4
        assert count_events(title_2) == 1
        assert count_occurrences(title_2) == 0

        # switch setting and see if past events/occurrences get deleted
        transaction.begin()
        client.app.org.delete_past_events = True
        transaction.commit()
        close_all_sessions()

        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 3
        assert count_events(title_2) == 0
        assert count_occurrences(title_2) == 0

    with (freeze_time(datetime(2024, 4, 27, 6, 0, tzinfo=tz))):
        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 3

    with (freeze_time(datetime(2024, 4, 28, 6, 0, tzinfo=tz))):
        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 2

    with (freeze_time(datetime(2024, 5, 4, 6, 0, tzinfo=tz))):
        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 2

    with (freeze_time(datetime(2024, 5, 5, 6, 0, tzinfo=tz))):
        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 1

    with (freeze_time(datetime(2024, 5, 11, 6, 0, tzinfo=tz))):
        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 1
        assert count_occurrences(title_1) == 1

    with (freeze_time(datetime(2024, 5, 12, 6, 0, tzinfo=tz))):
        # finally, after all occurrences took place, the event as well as all
        # occurrences got deleted by the cronjob
        # April 18th + 3*7 days + 2 cutoff days = May 11, hence deletion
        # happens on May 12th
        client.get(get_cronjob_url(job))
        assert count_events(title_1) == 0
        assert count_occurrences(title_1) == 0



@pytest.mark.parametrize(
    'access',
    ('private', 'member', 'mtan', 'secret', 'secret_mtan', 'public')
)
def test_send_email_notification_for_recent_directory_entry_publications(
    client: Client[TestOrgApp],
    access: str
) -> None:

    job = get_cronjob_by_name(client.app, 'hourly_maintenance_tasks')
    assert job is not None
    job.app = client.app
    tz = ensure_timezone('Europe/Zurich')

    def planauflagen() -> ExtendedDirectory:
        return (DirectoryCollection(client.app.session(), type='extended')  # type: ignore[return-value]
                .by_name('offentliche-planauflage'))

    def sport_clubs() -> ExtendedDirectory:
        return (DirectoryCollection(client.app.session(), type='extended')  # type: ignore[return-value]
                .by_name('sport-clubs'))

    def count_recipients() -> int:
        return (EntryRecipientCollection(client.app.session()).query()
                .filter_by(directory_id=planauflagen().id)
                .filter_by(confirmed=True).count())

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(client.app.session(), type='extended')
    planauflage = directories.add(
        title='Öffentliche Planauflage',
        structure="""
            Gesuchsteller/in *= ___
            Grundeigentümer/in *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Gesuchsteller/in]",
            order=['Gesuchsteller/in'],
            searchable=['title'],
        ),
        enable_update_notifications=True,
    )
    entry = planauflage.add(values=dict(
        gesuchsteller_in='Carmine Carminio',
        grundeigentumer_in='Doris Dorinio',
        publication_start=datetime(2025, 1, 6, 2, 0, tzinfo=tz),
        publication_end=datetime(2025, 1, 30, 2, 0, tzinfo=tz),
    ))
    entry.access = access
    assert entry.access == access

    entry = planauflage.add(values=dict(
        gesuchsteller_in='Emil Emilio',
        grundeigentumer_in='Franco Francinio',
        publication_start=datetime(2025, 1, 8, 6, 1, tzinfo=tz),
        publication_end=datetime(2025, 1, 31, 2, 0, tzinfo=tz),
    ))
    entry.access = access
    assert entry.access == access

    sport_club = directories.add(
        title='Sport Clubs',
        structure="""
            Name *= ___
            Category *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Name]",
            order=['Name'],
            searchable=['title']
        ),
        enable_update_notifications=False,
    )
    entry = sport_club.add(values=dict(
        name='Wanderfreunde',
        category='Hiking',
        publication_start=datetime(2025, 2, 1, 2, 0, tzinfo=tz),
        publication_end=datetime(2025, 2, 22, 2, 0, tzinfo=tz),
    ))
    entry.access = access
    assert entry.access == access

    entry = sport_club.add(values=dict(
        name='Pokerfreunde',
        category='Games',
        publication_start=datetime(2025, 2, 1, 2, 0, tzinfo=tz),
        publication_end=datetime(2025, 2, 2, 2, 0, tzinfo=tz),
    ))
    entry.access = access
    assert entry.access == access

    EntryRecipientCollection(client.app.session()).add(
        directory_id=planauflage.id,
        address='john@doe.ch',
        confirmed=True
    )
    EntryRecipientCollection(client.app.session()).add(
        directory_id=sport_club.id,
        address='john@doe.ch',
        confirmed=True
    )

    transaction.commit()
    close_all_sessions()

    assert count_recipients() == 1
    john = EntryRecipientCollection(client.app.session()).query().first()
    assert john is not None

    assert client.app.org.meta.get('hourly_maintenance_tasks_last_run') is None

    with freeze_time(datetime(2025, 1, 1, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        assert len(os.listdir(client.app.maildir)) == 0
        assert client.app.org.meta.get('hourly_maintenance_tasks_last_run')

    with freeze_time(datetime(2025, 1, 6, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        entry_1 = planauflagen().entries[0]

        if entry_1.access in ('mtan', 'public'):
            assert len(os.listdir(client.app.maildir)) == 1
            message = client.get_email(0)
            assert message is not None
            assert message['To'] == john.address
            assert planauflagen().title in message['Subject']
            assert entry_1.name in message['TextBody']
        else:
            assert len(os.listdir(client.app.maildir)) == 0

    with freeze_time(datetime(2025, 1, 8, 10, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        entry_2 = planauflagen().entries[1]

        if entry_1.access in ('mtan', 'public'):
            assert len(os.listdir(client.app.maildir)) == 2
            message = client.get_email(1)
            assert message is not None
            assert message['To'] == john.address
            assert planauflagen().title in message['Subject']
            assert entry_2.name in message['TextBody']
        else:
            assert len(os.listdir(client.app.maildir)) == 0

    # before enabling notifications for sport clubs after publication
    with freeze_time(datetime(2025, 2, 1, 6, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        # no additional mail
        if entry_1.access in ('mtan', 'public'):
            assert len(os.listdir(client.app.maildir)) == 2
        else:
            assert len(os.listdir(client.app.maildir)) == 0

    # enable notifications for sport clubs
    sport_clubs().enable_update_notifications = True
    transaction.commit()

    with freeze_time(datetime(2025, 2, 1, 1, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        # no additional mail, because the entry is not published yet
        if entry_1.access in ('mtan', 'public'):
            assert len(os.listdir(client.app.maildir)) == 2
        else:
            assert len(os.listdir(client.app.maildir)) == 0

    with freeze_time(datetime(2025, 2, 3, 10, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        entry_2 = sport_clubs().entries[1]

        if entry_1.access in ('mtan', 'public'):
            # only for still published sports club entry 'Wanderfreunde'
            assert len(os.listdir(client.app.maildir)) == 3
            message = client.get_email(2)
            assert message is not None
            assert message['To'] == john.address
            assert sport_clubs().title in message['Subject']
            assert entry_2.name in message['TextBody']
        else:
            assert len(os.listdir(client.app.maildir)) == 0


def test_update_newsletter_email_bounce_statistics(
    client: Client[TestOrgApp]
) -> None:

    # fake postmark mailer
    assert client.app.mail is not None
    client.app.mail['marketing']['mailer'] = 'postmark'

    job = get_cronjob_by_name(client.app,
                              'update_newsletter_email_bounce_statistics')
    assert job is not None
    job.app = client.app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    # create recipients Franz and Heinz
    recipients = RecipientCollection(client.app.session())
    recipients.add('franz@user.ch', confirmed=True)
    recipients.add('heinz@user.ch', confirmed=True)
    recipients.add('trudi@user.ch', confirmed=True)

    # create directory entry recipients
    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(client.app.session(), type='extended')
    directory_entries = directories.add(
        title='Baugesuche (Planauflage)',
        structure="""
            Gesuchsteller/in *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Gesuchsteller/in]",
        )
    )
    directory_entries.add(values=dict(
        gesuchsteller_in='Amon',
        publication_start=datetime(2024, 4, 1, tzinfo=tz),
        publication_end=datetime(2024, 4, 10, tzinfo=tz),
    ))
    entry_recipients = EntryRecipientCollection(client.app.session())
    entry_recipients.add(
        'marietta@user.ch', directory_entries.id, confirmed=True)
    entry_recipients.add(
        'martha@user.ch', directory_entries.id, confirmed=True)
    entry_recipients.add(
        'michu@user.ch', directory_entries.id, confirmed=True)

    transaction.commit()
    close_all_sessions()

    with patch('requests.Session.get') as mock_get:
        mock_get.side_effect = [
            Bunch(  # answer to bounce request
                status_code=200,
                json=lambda: {
                    'TotalCount': 3,
                    'Bounces': [
                        {
                            'RecordType': 'Bounce',
                            'ID': 3719297970,
                            'Inactive': False,
                            'Email': 'franz@user.ch',
                        },
                        {
                            'Inactive': True,
                            'Email': 'heinz@user.ch',
                        },
                        {
                            'Inactive': True,
                            'Email': 'martha@user.ch',
                        },
                        {
                            'Inactive': True,
                            'Email': 'trudi@user.ch',
                        },
                        {
                            'Inactive': True,
                            'Email': 'michu@user.ch',
                        },
                    ],
                },
                raise_for_status=Mock(return_value=None),
            ),
            Bunch(  # answer to the suppression request
                status_code=200,
                json=lambda: {
                    'Suppressions': [
                        {
                            'EmailAddress': 'heinz@user.ch',
                            'SuppressionReason': 'HardBounce',
                            'Origin': 'Recipient',
                            'CreatedAt': '2025-05-06T08:58:33-05:00'
                        },
                        {
                            'EmailAddress': 'martha@user.ch',
                        },
                        {
                            'EmailAddress': 'trudi@user.ch',
                        },
                        {
                            'EmailAddress': 'michu@user.ch',
                        },
                    ]
                },
                raise_for_status=Mock(return_value=None),
            )
        ]

        # execute cronjob
        client.get(get_cronjob_url(job))

        # check if the statistics are updated
        assert mock_get.called
        assert RecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'franz@user.ch').is_inactive is False
        assert RecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'heinz@user.ch').is_inactive is True
        assert RecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'trudi@user.ch').is_inactive is True
        assert EntryRecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'marietta@user.ch').is_inactive is False
        assert EntryRecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'martha@user.ch').is_inactive is True
        assert EntryRecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'michu@user.ch').is_inactive is True

    # reactivate recipients
    with patch('requests.Session.get') as mock_get:
        mock_get.side_effect = [
            Bunch(  # answer to bounce request
                status_code=200,
                json=lambda: {
                    'Bounces': [
                        {
                            'RecordType': 'Bounce',
                            'ID': 3719297470,
                            'Inactive': False,
                            'Email': 'unknown@user.ch',
                        },
                        {
                            'Inactive': True,
                            'Email': 'trudi@user.ch',
                        },
                        {
                            'Inactive': True,
                            'Email': 'michu@user.ch',
                        },
                    ]
                },
                raise_for_status=Mock(return_value=None),
            ),
            Bunch(  # answer to the suppression request
                status_code=200,
                json=lambda: {
                    'Suppressions': [
                        {
                            'EmailAddress': 'trudi@user.ch',
                        },
                        {
                            'EmailAddress': 'michu@user.ch',
                        },
                    ]
                },
                raise_for_status=Mock(return_value=None),
            )
        ]

        # execute cronjob
        client.get(get_cronjob_url(job))

        # check if the statistics are updated
        assert mock_get.called
        assert RecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'franz@user.ch').is_inactive is False
        assert RecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'heinz@user.ch').is_inactive is False
        assert RecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'trudi@user.ch').is_inactive is True
        assert EntryRecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'marietta@user.ch').is_inactive is False
        assert EntryRecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'martha@user.ch').is_inactive is False
        assert EntryRecipientCollection(client.app.session()).by_address(  # type: ignore[union-attr]
            'michu@user.ch').is_inactive is True

    # test raising runtime warning exception for status code 401
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value = Bunch(
            status_code=401,
            json=lambda: {},
            raise_for_status=Mock(
                side_effect=requests.exceptions.HTTPError('401 Unauthorized')),
        )

        # execute cronjob
        with pytest.raises(RuntimeWarning):
            client.get(get_cronjob_url(job))

    # for other 30x and 40x status codes, the cronjob shall raise an exception
    for status_code in [301, 302, 303, 400, 402, 403, 404, 405]:
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = Bunch(
                status_code=status_code,
                json=lambda: {},
                raise_for_status=Mock(
                    side_effect=requests.exceptions.HTTPError()),
            )

            # execute cronjob
            with pytest.raises(requests.exceptions.HTTPError):
                client.get(get_cronjob_url(job))

    recipients = RecipientCollection(client.app.session())
    assert recipients.query().count() == 3
    assert recipients.by_address('franz@user.ch').is_inactive is False  # type: ignore[union-attr]
    assert recipients.by_address('heinz@user.ch').is_inactive is False  # type: ignore[union-attr]
    assert recipients.by_address('trudi@user.ch').is_inactive is True  # type: ignore[union-attr]

    entry_recipients = EntryRecipientCollection(client.app.session())
    assert entry_recipients.query().count() == 3
    assert entry_recipients.by_address('marietta@user.ch').is_inactive is False  # type: ignore[union-attr]
    assert entry_recipients.by_address('martha@user.ch').is_inactive is False  # type: ignore[union-attr]
    assert entry_recipients.by_address('michu@user.ch').is_inactive is True  # type: ignore[union-attr]


def test_delete_unconfirmed_subscribers(client: Client[TestOrgApp]) -> None:

    job = get_cronjob_by_name(client.app,
                              'delete_unconfirmed_newsletter_subscriptions')
    assert job is not None
    job.app = client.app

    with freeze_time(datetime(2025, 1, 1, 4, 0)):
        transaction.begin()

        session = client.app.session()

        recipients = RecipientCollection(session)
        recipients.add('one@example.org', confirmed=False)
        recipients.add('two@example.org', confirmed=False)
        # Cronjob should only delete unconfirmed recipients
        recipients.add('three@example.org', confirmed=True)

    # And only unconfirmed subscribers older than 7 days
    recipients.add('four@example.org', confirmed=False)
    transaction.commit()

    recipients = RecipientCollection(client.app.session())
    assert recipients.query().count() == 4

    client.get(get_cronjob_url(job))

    recipients = RecipientCollection(client.app.session())
    assert recipients.query().count() == 2


def test_send_push_notifications_for_news(
    client: Client[TestOrgApp],
    firebase_json: str
) -> None:

    job = get_cronjob_by_name(client.app, 'send_push_notifications_for_news')
    assert job is not None
    job.app = client.app
    tz = ensure_timezone('Europe/Zurich')

    # Set up test data
    transaction.begin()

    # Configure Firebase credentials for the organization
    encrypted_creds = client.app.encrypt(firebase_json).decode('utf-8')
    client.app.org.firebase_adminsdk_credential = encrypted_creds

    # Define topic mapping for the organization
    client.app.org.selectable_push_notification_options = [
        [f'{client.app.schema}_news', 'News'],
        [f'{client.app.schema}_important', 'Important']
    ]

    # Create a news item that should trigger notifications
    news = PageCollection(client.app.session())
    news_parent = news.add_root('News', type='news')
    recent_news = news.add(
        parent=news_parent,
        title='Recent news with notifications',
        lead='This should trigger a notification',
        text='Test content for recent news',
        access='public',
        type='news'
    )

    # Set publication time just within the 10-minute window
    recent_news.publication_start = utcnow() - timedelta(minutes=5)

    # Set metadata
    recent_news.meta = {
        'send_push_notifications_to_app': True,
        'push_notifications': [f'{client.app.schema}_news'],
        'hashtags': ['News']
    }

    transaction.commit()
    close_all_sessions()

    # Set up test notification service
    test_service = TestNotificationService()
    set_test_notification_service(test_service)

    try:
        # Run the cronjob
        client.get(get_cronjob_url(job))

        # Verify the notification was sent
        assert (
            len(test_service.sent_messages) == 1
        ), 'Expected exactly one notification to be sent'

        # Verify the notification content
        message = test_service.sent_messages[0]
        assert message['topic'] == f'{client.app.schema}_news'
        assert message['title'] == 'Recent news with notifications'
        assert message['body'] == 'This should trigger a notification'
        assert message['data'] is not None

    finally:
        # Clean up the test service
        set_test_notification_service(None)


def test_push_notification_duplicate_detection(
    client: Client[TestOrgApp],
    firebase_json: str
) -> None:
    """Test that validates the duplicate detection logic properly."""
    session = client.app.session()
    job = get_cronjob_by_name(client.app, 'send_push_notifications_for_news')
    assert job is not None
    job.app = client.app

    # Set up test data
    transaction.begin()
    encrypted_creds = client.app.encrypt(firebase_json).decode('utf-8')
    client.app.org.firebase_adminsdk_credential = encrypted_creds
    client.app.org.selectable_push_notification_options = [
        [f'{client.app.schema}_news', 'News']
    ]

    # Create a news item
    news = PageCollection(session)
    news_parent = news.add_root('News', type='news')
    test_news = news.add(
        news_parent,
        title='Test news for duplicate detection',
        lead='Test content',
        text='Test content body',
        access='public',
        type='news'
    )
    news_id = test_news.id

    # Set publication time and metadata
    test_news.publication_start = utcnow() - timedelta(minutes=2)
    test_news.meta = {
        'send_push_notifications_to_app': 'true',
        'push_notifications': [[f'{client.app.schema}_news', 'News']],
    }

    # Create a PushNotification record directly in the database
    # to simulate a notification that was already sent
    push_notification = PushNotification(
        news_id=news_id,
        topic_id=f'{client.app.schema}_news',
        sent_at=utcnow(),
        response_data={'status': 'sent', 'message_id': 'test-message-id'},
    )
    session.add(push_notification)

    # Commit transaction to ensure everything is saved to the database
    transaction.commit()

    # Setup test notification service
    test_service = TestNotificationService()
    set_test_notification_service(test_service)

    try:
        # Run the cronjob - this should detect the existing notification and
        # skip it
        client.get(get_cronjob_url(job))
        assert (
            len(test_service.sent_messages) == 0
        ), "No notifications should be sent for duplicates"

        # Count PushNotification records - should still be just 1
        count = (
            session.query(PushNotification)
            .filter(
                PushNotification.news_id == news_id,  # Use stored ID
                PushNotification.topic_id == f'{client.app.schema}_news',
                )
            .count()
        )
        assert (
            count == 1
        ), "There should be exactly one notification record"

    finally:
        # Clean up
        set_test_notification_service(None)


def _create_news_hierarchy(
    session: Session,
    parent: News | None,
    items_data: Iterable[tuple[str, Decimal | None]]
) -> list[News]:
    created_items = []
    for title, order in items_data:
        name = normalize_for_url(title)
        # NOTE: Even though order is not nullable it has a default value
        #       so SQLAlchemy will use that if you set it to `None`, we
        #       shouldn't really rely on this behavior too much, but we
        #       still want to test it works correctly.
        item = News(  # type: ignore[misc]
            title=title,
            name=name,
            type='news',
            parent=parent,
            order=order
        )
        session.add(item)
        created_items.append(item)
    session.flush()
    return created_items


def test_normalize_adjacency_list_order(client: Client[TestOrgApp]) -> None:
    session = client.app.session()
    job = get_cronjob_by_name(client.app, 'normalize_adjacency_list_order')
    assert job is not None
    job.app = client.app

    orders = [Decimal('1.0'), Decimal('5.0'), Decimal('10.0')]
    titles = [f'News {i+1}' for i in range(len(orders))]
    items_data = list(zip(titles, orders))

    pages = PageCollection(session)
    root_title = 'Aktuelles'
    root_name = normalize_for_url(root_title)
    root_item = News(title=root_title, name=root_name, type='news')
    session.add(root_item)
    session.flush()
    default_root_order = root_item.order
    news_root_id = root_item.id

    _create_news_hierarchy(session, root_item, items_data)
    transaction.commit()

    # Verify initial order
    news_items = pages.query().filter(
        News.parent_id == news_root_id).order_by(News.order).all()

    assert [n.order for n in news_items] == [
        Decimal('1.0'), Decimal('5.0'), Decimal('10.0')
    ]
    assert [n.title for n in news_items] == ['News 1', 'News 2', 'News 3']

    # Execute the cron job
    client.get(get_cronjob_url(job))
    session.expire_all()  # Force reload from DB

    # Verify normalized order
    request: Any = Bunch(session=session)
    news_items_after = NewsCollection(request).query().filter(
        News.parent_id == news_root_id).order_by(News.order).all()

    # Order should now be sequential integers (represented as Decimals)
    assert [n.order for n in news_items_after] == [
        Decimal('1.0'), Decimal('2.0'), Decimal('3.0')
    ]

    # Relative order must be preserved
    assert [n.title for n in news_items_after] == ['News 1',
                                                   'News 2', 'News 3']
    # Verify the root page order was not affected
    root = pages.by_id(news_root_id)
    assert root is not None
    assert root.order == default_root_order


def test_normalize_adjacency_list_order_with_null_becomes_default(
    client: Client[TestOrgApp]
) -> None:

    session = client.app.session()
    job = get_cronjob_by_name(client.app, 'normalize_adjacency_list_order')
    assert job is not None
    job.app = client.app

    # Define items with one potentially becoming default order
    # Corresponds to default value set in AdjacencyList.order
    default_order_value = Decimal('65536')
    items_data = [
        ('Item C', Decimal('1.0')),
        ('Item A', Decimal('5.0')),
        ('Item B', None),  # Pass None, expecting it to take the default value
    ]

    pages = PageCollection(session)
    root_title = 'Default Order Test Root'
    root_name = normalize_for_url(root_title)
    root_item = News(title=root_title, name=root_name, type='news')
    session.add(root_item)
    session.flush()
    default_root_order = root_item.order
    news_root_id = root_item.id

    _create_news_hierarchy(session, root_item, items_data)
    transaction.commit()

    # Verify initial state
    news_items_initial = pages.query().filter(
        News.parent_id == news_root_id).order_by(News.title).all()
    orders_initial = {n.title: n.order for n in news_items_initial}
    assert orders_initial == {
        'Item A': Decimal('5.0'),
        'Item B': default_order_value,  # Check it received the default
        'Item C': Decimal('1.0'),
    }

    client.get(get_cronjob_url(job))
    session.expire_all()  # Force reload from DB

    # Verify normalized order
    # The SQL uses ORDER BY "order" ASC, "pk" ASC.
    # Initial sort order for ROW_NUMBER() would be:
    # Item C (1.0), Item A (5.0), Item B (65536.0)
    # Normalization should result in: Item C (1.0), Item A (2.0), Item B (3.0)
    request: Any = Bunch(session=session)
    news_items_after = NewsCollection(request).query().filter(
        News.parent_id == news_root_id).order_by(News.order).all()

    expected_orders = [Decimal('1.0'), Decimal('2.0'), Decimal('3.0')]
    expected_titles = ['Item C', 'Item A', 'Item B']

    assert [n.order for n in news_items_after] == expected_orders
    assert [n.title for n in news_items_after] == expected_titles

    # Verify the root page order was not affected
    root = pages.by_id(news_root_id)
    assert root is not None
    assert root.order == default_root_order


def test_wil_daily_event_import_wrong_app(client: Client[TestOrgApp]) -> None:
    session = client.app.session()
    org_job = get_cronjob_by_name(client.app, 'wil_daily_event_import')
    assert org_job is not None
    org_job.app = client.app

    # test not being the right organisation
    client.get(get_cronjob_url(org_job))


@freeze_time('2025-09-01', tick=True)
def test_wil_daily_event_import(
    wil_app: TestOrgApp,
    capturelog: CaptureLogFixture
) -> None:

    client = Client(wil_app)
    session = wil_app.session()
    wil_job = get_cronjob_by_name(wil_app, 'wil_daily_event_import')
    assert wil_job is not None
    wil_job.app = wil_app
    capturelog.setLevel(logging.ERROR, logger='onegov.org.cronjobs')

    # no api token
    client.get(get_cronjob_url(wil_job))

    # set api test token
    wil_app.azizi_api_token = 'mytoken'

    # connection error
    with patch('requests.get',
               side_effect=requests.exceptions.ConnectionError):
        client.get(get_cronjob_url(wil_job))

        assert ('Failed to retrieve events for Wil from' in
                capturelog.records()[-1].message)

    # server error
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response

        client.get(get_cronjob_url(wil_job))

        assert ('Failed to retrieve events for Wil from' in
                capturelog.records()[-1].message)
        assert 'status code: 500' in capturelog.records()[-1].message

    # test with successful response
    tz = timezone(timedelta(hours=2))
    first_date = datetime.now(tz).replace(
        hour=8, microsecond=0) + timedelta(days=1)
    start_dates = [
        first_date,  # event 1
        first_date + timedelta(days=2),  # event 2
        first_date + timedelta(weeks=1),  # event 3 and 4
    ]
    event_status = [
        'scheduled',  # event 1
        'scheduled',  # event 2
        'scheduled',  # event 3, 4
    ]

    # missing daily event
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <minasa xsi:schemaLocation="https://azizi.2mp.ch/schemas/minasa_xml_v1.xsd"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="https://minasa.ch/schema/v1">
      <events>
        <event>
          <uuid7>E132456</uuid7>
          <locationUuid7>L132456</locationUuid7>
          <organizerUuid7>O789565</organizerUuid7>
          <title>Pole Vault Lesson</title>
          <description>Pole Vault description</description>
          <originalEventUrl>polevaultassociation.sport/first-lession</originalEventUrl>
          <schedules>
            <schedule>
              <uuid7>S132450</uuid7>
              <eventStatus>{event_status[0]}</eventStatus>
              <locationUuid7>S132456</locationUuid7>>
              <start>{start_dates[0].strftime('%Y-%m-%dT%H:%M:%S%z')}</start>
              <recurrence>
                <frequency>single</frequency>
              </recurrence>
            </schedule>
          </schedules>
        </event>
        <event>
          <uuid7>E132499</uuid7>
          <locationUuid7>L132488</locationUuid7>
          <organizerUuid7>O789588</organizerUuid7>
          <title>Reading with Johanna Beehrens</title>
          <abstract>Best book reader in town</abstract>
          <description>Reading a Book</description>
          <category>
            <mainCategory>Literature</mainCategory>
          </category>
          <originalEventUrl></originalEventUrl>
          <providerReference>
            <url>https://www.lemington.ch/events/reading-johanna-beehrens</url>
          </providerReference>
          <schedules>
            <schedule>
              <uuid7>S132451</uuid7>
              <eventStatus>{event_status[1]}</eventStatus>
              <locationUuid7>S132456</locationUuid7>>
              <start>{start_dates[1].strftime('%Y-%m-%dT%H:%M:%S%z')}</start>
              <end>{(start_dates[1] + timedelta(
        hours=2)).strftime('%Y-%m-%dT%H:%M:%S%z')}</end>
              <recurrence>
                <frequency>weekly</frequency>
                  <interval>2</interval>
                  <until>{start_dates[1] + timedelta(weeks=4)}</until>
              </recurrence>
            </schedule>
          </schedules>
        </event>
        <event>
          <uuid7>E132500</uuid7>
          <locationUuid7>L132456</locationUuid7>
          <organizerUuid7>O789565</organizerUuid7>
          <title>100 Meter Race of the Year</title>
          <description>Event of the year!</description>
          <category>
            <mainCategory>Sports</mainCategory>
          </category>
          <originalEventUrl>www.100race.org</originalEventUrl>
          <schedules>
            <schedule>
              <uuid7>S999101</uuid7>
              <eventStatus>{event_status[2]}</eventStatus>
              <locationUuid7>S132456</locationUuid7>>
              <start>{start_dates[2].strftime('%Y-%m-%dT%H:%M:%S%z')}</start>
              <end>{(start_dates[2] + timedelta(
        minutes=100)).strftime('%Y-%m-%dT%H:%M:%S%z')}</end>
              <recurrence>
                <frequency>single</frequency>
              </recurrence>
            </schedule>
            <schedule>
              <uuid7>S999102</uuid7>
              <locationUuid7>S132456</locationUuid7>>
              <eventStatus>{event_status[2]}</eventStatus>
              <start>{(start_dates[2] + timedelta(
        days=1, hours=8)).strftime('%Y-%m-%dT%H:%M:%S%z')}</start>
              <end>{(start_dates[2] + timedelta(
        days=1, hours=8, minutes=100)).strftime('%Y-%m-%dT%H:%M:%S%z')}</end>
              <recurrence>
                <frequency>single</frequency>
              </recurrence>
            </schedule>
          </schedules>
        </event>
      </events>
      <locations>
        <location>
          <uuid7>L132456</uuid7>
          <address>
            <title>Pole Vault Stadium</title>
            <street>Stadium Road</street>
            <number>1</number>
            <zip>6000</zip>
            <city>Pole Town</city>
            <latitude>47.5</latitude>
            <longitude>9.01</longitude>
          </address>
        </location>
        <location>
          <uuid7>L132488</uuid7>
          <address>
            <title>Library</title>
            <street>Book Ct</street>
            <number>7</number>
            <zip>6001</zip>
            <city>Lemington</city>
            <latitude>47.6</latitude>
            <longitude>8.4</longitude>
          </address>
        </location>
      </locations>
      <organizers>
        <organizer>
          <uuid7>O789565</uuid7>
          <address>
            <title>Pole Vault Association</title>
            <street>Main Street</street>
            <number>1</number>
            <zip>8000</zip>
            <city>Pole Town</city>
            <phone>041 123 4567</phone>
            <email>info@polevault.sport</email>
            <url>polevaultassociation.sport</url>
          </address>
        </organizer>
        <organizer>
          <uuid7>O789588</uuid7>
          <address>
            <title>Culture Club</title>
            <street>Culture Plaza</street>
            <number>3</number>
            <zip>6010</zip>
            <city>Coin Town</city>
            <phone>044 321 7744</phone>
            <email>info@cultureclub.io</email>
            <url>cultureclub.io</url>
          </address>
        </organizer>
      </organizers>
    </minasa>
    """

    # remove all existing/initial events from collection
    collection = EventCollection(session)
    for e in collection.query():
        collection.delete(e)

    added, updated, purged = collection.from_minasa(xml.encode('utf-8'))

    events = collection.query().order_by(Event.start).all()
    assert len(events) == 4  # number of event schedules
    assert len(added) == 4  # number of event schedules
    assert len(updated) == 0
    assert len(purged) == 0

    assert events[0] == added[0]
    assert events[0].title == 'Pole Vault Lesson'
    assert events[0].description == 'Pole Vault description'
    assert events[0].tags == []
    assert events[0].start == start_dates[0]
    assert events[0].end == start_dates[0] + timedelta(hours=2)
    assert events[0].recurrence == None
    assert events[0].occurrence_dates() == [start_dates[0]]
    assert (events[0].location ==
            'Pole Vault Stadium, Stadium Road, 6000, Pole Town')
    assert events[0].organizer == 'Pole Vault Association'
    assert events[0].organizer_email == 'info@polevault.sport'
    assert events[0].organizer_phone == '041 123 4567'
    assert (events[0].external_event_url ==
            'polevaultassociation.sport/first-lession')

    assert events[1] == added[1]
    assert events[1].title == 'Reading with Johanna Beehrens'
    assert (events[1].description ==
            'Best book reader in town\n\nReading a Book')
    assert events[1].tags == ['Literature']
    assert events[1].start == start_dates[1]
    assert events[1].end == start_dates[1] + timedelta(hours=2)
    recurrence1 = to_timezone(start_dates[1] + timedelta(weeks=2), 'UTC')
    recurrence2 = to_timezone(start_dates[1] + timedelta(weeks=4), 'UTC')
    assert events[1].recurrence == (
        f'RDATE:{recurrence1:%Y%m%dT%H%M%SZ}\n'
        f'RDATE:{recurrence2:%Y%m%dT%H%M%SZ}'
    )
    assert events[1].occurrence_dates() == [
        start_dates[1],
        start_dates[1] + timedelta(weeks=2),
        start_dates[1] + timedelta(weeks=4)
    ]
    assert events[1].location == 'Library, Book Ct, 6001, Lemington'
    assert events[1].organizer == 'Culture Club'
    assert events[1].organizer_email == 'info@cultureclub.io'
    assert events[1].organizer_phone == '044 321 7744'
    assert events[1].external_event_url == 'https://www.lemington.ch/events/reading-johanna-beehrens'

    # events 3 and 4 are actually the same event but different schedules
    for i, start in zip(
        [2, 3],
        [start_dates[2], start_dates[2] + timedelta(days=1, hours=8)]
    ):
        assert events[i] == added[i]
        assert events[i].title == '100 Meter Race of the Year'
        assert events[i].tags == ['Sports']
        assert events[i].start == start
        assert events[i].end == start + timedelta(minutes=100)
        assert events[i].recurrence == None
        assert events[i].occurrence_dates() == [start]
        assert (events[i].location ==
                'Pole Vault Stadium, Stadium Road, 6000, Pole Town')
        assert events[i].organizer == 'Pole Vault Association'
        assert events[i].organizer_email == 'info@polevault.sport'
        assert events[i].organizer_phone == '041 123 4567'
        assert events[i].external_event_url == 'www.100race.org'

    occurrences = OccurrenceCollection(session)
    assert occurrences.query().count() == 6

    expected_titles = [  # sorted by start date
        'Pole Vault Lesson',
        'Reading with Johanna Beehrens',
        '100 Meter Race of the Year',
        '100 Meter Race of the Year',
        'Reading with Johanna Beehrens',
        'Reading with Johanna Beehrens',
    ]
    for occurrence, expected_title in zip(
            occurrences.query(), expected_titles):
        assert occurrence.title == expected_title

    # test updated

    # test purged
    xml_2 = xml.replace(  # replace first event status with 'deleted'
        '<eventStatus>scheduled</eventStatus>',
        '<eventStatus>deleted</eventStatus>',
        2
    )
    collection = EventCollection(session)
    assert collection.query().count() == 4

    added, updated, purged = collection.from_minasa(xml_2.encode('utf-8'))

    assert len(added) == 0  # number of event schedules
    assert len(updated) == 0
    assert len(purged) == 2
    assert collection.query().count() == 2
    assert [o.title for o in collection.query()] == [
        '100 Meter Race of the Year',
        '100 Meter Race of the Year'
    ]
