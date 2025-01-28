import json
import os
from pathlib import Path

import pytest
import transaction
from datetime import datetime, timedelta
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.directory import (DirectoryEntryCollection,
                              DirectoryConfiguration,
                              DirectoryCollection)
from onegov.directory.collections.directory import EntryRecipientCollection
from onegov.event import EventCollection, OccurrenceCollection
from onegov.event.utils import as_rdates
from onegov.form import FormSubmissionCollection
from onegov.org.models import ResourceRecipientCollection, News
from onegov.org.models.resource import RoomResource
from onegov.org.models.ticket import ReservationHandler, DirectoryEntryHandler
from onegov.page import PageCollection
from onegov.ticket import Handler, Ticket, TicketCollection
from onegov.user import UserCollection
from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.reservation import ResourceCollection
from onegov.user.collections import TANCollection
from sedate import ensure_timezone, utcnow
from sqlalchemy.orm import close_all_sessions
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url
from tests.shared import Client
from tests.shared.utils import add_reservation


class EchoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EHO'}
    es_type_name = 'echo_tickets'


class EchoHandler(Handler):
    handler_title = "Echo"

    @property
    def deleted(self):
        return False

    @property
    def email(self):
        return self.data.get('email')

    @property
    def title(self):
        return self.data.get('title')

    @property
    def subtitle(self):
        return self.data.get('subtitle')

    @property
    def group(self):
        return self.data.get('group')

    def get_summary(self, request):
        return self.data.get('summary')

    def get_links(self, request):
        return self.data.get('links')


def register_echo_handler(handlers):
    handlers.register('EHO', EchoHandler)


def register_reservation_handler(handlers):
    handlers.register('RSV', ReservationHandler)


def register_directory_handler(handlers):
    handlers.register('DIR', DirectoryEntryHandler)


def test_daily_ticket_statistics(org_app, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)

    job = get_cronjob_by_name(org_app, 'daily_ticket_statistics')
    job.app = org_app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = org_app.session()
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
    request = Bunch(client_addr='127.0.0.1')
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


def test_weekly_ticket_statistics(org_app, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)

    job = get_cronjob_by_name(org_app, 'weekly_ticket_statistics')
    job.app = org_app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = org_app.session()
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
    request = Bunch(client_addr='127.0.0.1')
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


def test_monthly_ticket_statistics(org_app, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)

    job = get_cronjob_by_name(org_app, 'monthly_ticket_statistics')
    job.app = org_app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = org_app.session()
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
    request = Bunch(client_addr='127.0.0.1')
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


def test_daily_reservation_overview(org_app):
    resources = ResourceCollection(org_app.libres_context)
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

    submissions = FormSubmissionCollection(org_app.session())
    submissions.add_external(
        form=gymnasium.form_class(data={'name': '0xdeadbeef'}),
        state='complete',
        id=gym_reservation_token
    )

    recipients = ResourceRecipientCollection(org_app.session())
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

    client = Client(org_app)

    job = get_cronjob_by_name(org_app, 'daily_resource_usage')
    job.app = org_app

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
        assert "Heute keine Reservationen" in mail['TextBody']
        assert "-reservation" not in mail['TextBody']

    # NOTE: These seem to not always get sent in the same order...
    #       technically we don't really care so let's determine order
    if mails[0]['To'] == 'gym@example.org':
        gym_mail, day_mail = mails
    else:
        day_mail, gym_mail = mails
    assert gym_mail['To'] == 'gym@example.org'
    assert "Allgemein - Gymnasium" in gym_mail['TextBody']
    assert "Allgemein - Dailypass" not in gym_mail['TextBody']

    assert day_mail['To'] == 'day@example.org'
    assert "Allgemein - Dailypass" in day_mail['TextBody']
    assert "Allgemein - Gymnasium" not in day_mail['TextBody']

    # once we confirm the reservation it shows up in the e-mail
    client.flush_email_queue()

    gymnasium = resources.by_name('gymnasium')
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
    assert mail['To'] == 'both@example.org'
    assert 'Gymnasium' in mail['TextBody']
    assert 'Dailypass' in mail['TextBody']
    assert '0xdeadbeef' not in mail['TextBody']  # diff. day

    # this also works for the other reservation which has no data
    client.flush_email_queue()

    dailypass = resources.by_name('dailypass')
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
def test_send_scheduled_newsletters(client, org_app, secret_content_allowed):
    def create_scheduled_newsletter():
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
                "<h1>Latest News</h1>",
                content={"news": [
                    str(news_public.id),
                    str(news_public_2.id),
                    str(news_secret.id),
                    str(news_private.id)
                ]},
                scheduled=utcnow()
            )

            transaction.commit()

    session = org_app.session()
    news = PageCollection(session)
    news_parent = news.query().filter_by(name='news').one()
    newsletters = NewsletterCollection(session)
    recipients = RecipientCollection(session)

    recipient = recipients.add('info@example.org')
    recipient.confirmed = True

    org_app.org.secret_content_allowed = secret_content_allowed

    create_scheduled_newsletter()

    job = get_cronjob_by_name(org_app, 'hourly_maintenance_tasks')
    job.app = org_app

    with freeze_time('2018-05-31 11:00'):
        client = Client(org_app)
        client.get(get_cronjob_url(job))
        newsletter = newsletters.query().one()

        assert newsletter.scheduled  # still scheduled, not sent yet
        assert len(os.listdir(client.app.maildir)) == 0

    with freeze_time('2018-05-31 12:00'):
        client = Client(org_app)
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


def test_auto_archive_tickets_and_delete(org_app, handlers):
    register_echo_handler(handlers)

    session = org_app.session()
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

        request = Bunch(client_addr='127.0.0.1')
        UserCollection(session).register(
            'b', 'p@ssw0rd', request, role='admin'
        )
        users = UserCollection(session).query().all()
        user = users[0]
        for t in tickets:
            t.accept_ticket(user)
            t.close_ticket()

        org_app.org.auto_archive_timespan = 30  # days
        org_app.org.auto_delete_timespan = 30  # days

        transaction.commit()

        close_all_sessions()

    # now we go forward a month for archival
    with freeze_time('2022-09-17 04:30'):

        query = session.query(Ticket)
        query = query.filter_by(state='closed')
        assert query.count() == 2

        job = get_cronjob_by_name(org_app, 'archive_old_tickets')
        job.app = org_app
        client = Client(org_app)
        client.get(get_cronjob_url(job))

        query = session.query(Ticket)
        query = query.filter(Ticket.state == 'archived')
        assert query.count() == 2

        # this delete cronjob should have no effect (yet), since archiving
        # resets the `last_change`
        job = get_cronjob_by_name(org_app, 'delete_old_tickets')
        job.app = org_app
        client = Client(org_app)
        client.get(get_cronjob_url(job))

        query = session.query(Ticket)
        query = query.filter(Ticket.state == 'archived')
        assert query.count() == 2

    # and another month for deletion
    with freeze_time('2022-10-17 05:30'):
        session.flush()
        assert org_app.org.auto_delete_timespan is not None

        job = get_cronjob_by_name(org_app, 'delete_old_tickets')
        job.app = org_app
        client = Client(org_app)
        client.get(get_cronjob_url(job))

        # should be deleted
        assert session.query(Ticket).count() == 0


def test_respect_recent_reservation_for_archive(org_app, handlers):
    register_echo_handler(handlers)
    register_reservation_handler(handlers)

    transaction.begin()

    resources = ResourceCollection(org_app.libres_context)
    dailypass = resources.add(
        'Dailypass',
        'Europe/Zurich',
        type='daypass'
    )

    recipients = ResourceRecipientCollection(org_app.session())
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
        collection = TicketCollection(org_app.session())
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
            org_app.session(),
            start=datetime(2023, 6, 6, 4, 30),
            end=datetime(2023, 6, 6, 5, 0),
        )

        # close all the tickets
        tickets_query = TicketCollection(org_app.session()).query()
        assert tickets_query.count() == 2
        user = UserCollection(org_app.session()).query().first()
        for ticket in tickets_query:
            ticket.accept_ticket(user)
            ticket.close_ticket()

        org_app.org.auto_archive_timespan = 365  # days
        org_app.org.auto_delete_timespan = 365  # days

        transaction.commit()

        close_all_sessions()

    # now go forward a year
    with freeze_time('2023-06-06 02:00'):

        q = TicketCollection(org_app.session()).query()
        assert q.filter_by(state='open').count() == 0
        assert q.filter_by(state='closed').count() == 2

        job = get_cronjob_by_name(org_app, 'archive_old_tickets')
        job.app = org_app
        client = Client(org_app)
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


def test_monthly_mtan_statistics(org_app, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)

    job = get_cronjob_by_name(org_app, 'monthly_mtan_statistics')
    job.app = org_app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    # don't send an email if no mTANs have been sent
    with freeze_time(datetime(2016, 2, 1, tzinfo=tz)):
        client.get(url)

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    session = org_app.session()
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


def test_delete_content_marked_deletable__directory_entries(org_app, handlers):
    register_echo_handler(handlers)
    register_directory_handler(handlers)

    client = Client(org_app)
    job = get_cronjob_by_name(org_app, 'delete_content_marked_deletable')
    job.app = org_app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    directories = DirectoryCollection(org_app.session(), type='extended')
    directory_entries = directories.add(
        title='Öffentliche Planauflage',
        structure="""
            Gesuchsteller/in *= ___
            Grundeigentümer/in *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Gesuchsteller/in]",
            order=('Gesuchsteller/in'),
        )
    )

    event = directory_entries.add(values=dict(
        gesuchsteller_in='Anton Antoninio',
        grundeigentumer_in='Berta Bertinio',
        publication_start=datetime(2024, 4, 1, tzinfo=tz),
        publication_end=datetime(2024, 4, 10, tzinfo=tz),
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

    def count_publications(directories):
        applications = directories.by_name('offentliche-planauflage')
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


def test_delete_content_marked_deletable__news(org_app, handlers):
    register_echo_handler(handlers)
    register_directory_handler(handlers)

    client = Client(org_app)
    job = get_cronjob_by_name(org_app, 'delete_content_marked_deletable')
    job.app = org_app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()
    collection = PageCollection(org_app.session())
    news = collection.add_root('News', type='news')
    first = collection.add(
        news,
        title='First News',
        type='news',
        lead='First News Lead',
    )
    first.publication_start = datetime(2024, 4, 1, tzinfo=tz)
    first.publication_end = datetime(2024, 4, 2, 23, 59, tzinfo=tz)
    first.delete_when_expired = True

    two = collection.add(
        news,
        title='Second News',
        type='news',
        lead='Second News Lead'
    )
    two.publication_start = datetime(2024, 4, 5, tzinfo=tz)
    two.publication_end = datetime(2024, 4, 6, tzinfo=tz)
    two.delete_when_expired = True

    transaction.commit()
    close_all_sessions()

    def count_news():
        c = PageCollection(org_app.session()).query()
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


def test_delete_content_marked_deletable__events_occurrences(org_app,
                                                             handlers):
    register_echo_handler(handlers)
    register_directory_handler(handlers)

    client = Client(org_app)
    job = get_cronjob_by_name(org_app, 'delete_content_marked_deletable')
    job.app = org_app
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    title = 'Antelope Canyon Tour'
    events = EventCollection(org_app.session())
    event = events.add(
        title=title,
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
    event.recurrence = as_rdates('FREQ=WEEKLY;COUNT=4', event.start)
    event.submit()
    event.publish()

    transaction.commit()
    close_all_sessions()

    def count_events():
        return (EventCollection(org_app.session()).query()
                .filter_by(title=title).count())

    def count_occurrences():
        return (OccurrenceCollection(org_app.session(), outdated=True)
                .query().filter_by(title=title).count())

    with (freeze_time(datetime(2024, 4, 18, tzinfo=tz))):
        # default setting, no deletion of past event and past occurrences
        assert org_app.org.delete_past_events is False

        assert count_events() == 1
        assert count_occurrences() == 4

        client.get(get_cronjob_url(job))
        assert count_events() == 1
        assert count_occurrences() == 4

    with (freeze_time(datetime(2024, 4, 19, 6, 0, tzinfo=tz))):
        # an old occurrence could be deleted but the setting is not enabled
        client.get(get_cronjob_url(job))
        assert count_events() == 1
        assert count_occurrences() == 4

        # switch setting and see if past events and past occurrences are
        # deleted
        transaction.begin()
        org_app.org.delete_past_events = True
        transaction.commit()
        close_all_sessions()

        client.get(get_cronjob_url(job))
        assert count_events() == 1
        assert count_occurrences() == 3

    with (freeze_time(datetime(2024, 5, 9, tzinfo=tz))):
        client.get(get_cronjob_url(job))
        assert count_events() == 1
        assert count_occurrences() == 1

    with (freeze_time(datetime(2024, 5, 10, tzinfo=tz))):
        # finally after all occurrences took place, the event as well as all
        # occurrences got deleted by the cronjob (April 18th + 3*7 days =
        # May 10)
        client.get(get_cronjob_url(job))
        assert count_events() == 0
        assert count_occurrences() == 0


def test_send_email_notification_for_recent_directory_entry_publications(
    es_org_app,
    handlers
):
    org_app = es_org_app
    register_echo_handler(handlers)
    register_directory_handler(handlers)

    client = Client(org_app)
    job = get_cronjob_by_name(org_app, 'hourly_maintenance_tasks')
    job.app = org_app
    tz = ensure_timezone('Europe/Zurich')

    assert len(os.listdir(client.app.maildir)) == 0

    transaction.begin()

    directories = DirectoryCollection(org_app.session(), type='extended')
    planauflage = directories.add(
        title='Öffentliche Planauflage',
        structure="""
            Gesuchsteller/in *= ___
            Grundeigentümer/in *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Gesuchsteller/in]",
            order=('Gesuchsteller/in'),
            searchable=['title'],
        ),
        enable_update_notifications=True,
    )
    planauflage.add(values=dict(
        gesuchsteller_in='Carmine Carminio',
        grundeigentumer_in='Doris Dorinio',
        publication_start=datetime(2025, 1, 6, 2, 0, tzinfo=tz),
        publication_end=datetime(2025, 1, 30, 2, 0, tzinfo=tz),
    ))
    planauflage.add(values=dict(
        gesuchsteller_in='Emil Emilio',
        grundeigentumer_in='Franco Francinio',
        publication_start=datetime(2025, 1, 8, 6, 1, tzinfo=tz),
        publication_end=datetime(2025, 1, 31, 2, 0, tzinfo=tz),
    ))

    sport_clubs = directories.add(
        title='Sport Clubs',
        structure="""
            Name *= ___
            Category *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[Name]",
            order=('Name'),
            searchable=['title']
        ),
        enable_update_notifications=False,
    )
    sport_clubs.add(values=dict(
        name='Wanderfreunde',
        category='Hiking',
        publication_start=datetime(2025, 2, 1, 2, 0, tzinfo=tz),
        publication_end=datetime(2025, 2, 22, 2, 0, tzinfo=tz),
    ))
    sport_clubs.add(values=dict(
        name='Pokerfreunde',
        category='Games',
        publication_start=datetime(2025, 2, 1, 2, 0, tzinfo=tz),
        publication_end=datetime(2025, 2, 2, 2, 0, tzinfo=tz),
    ))

    EntryRecipientCollection(org_app.session()).add(
        directory_id=planauflage.id,
        address='john@doe.ch',
        confirmed=True
    )
    EntryRecipientCollection(org_app.session()).add(
        directory_id=sport_clubs.id,
        address='john@doe.ch',
        confirmed=True
    )

    transaction.commit()
    close_all_sessions()

    def planauflagen():
        return (DirectoryCollection(org_app.session(), type='extended')
                .by_name('offentliche-planauflage'))

    def sport_clubs():
        return (DirectoryCollection(org_app.session(), type='extended')
                .by_name('sport-clubs'))

    def count_recipients():
        return (EntryRecipientCollection(org_app.session()).query()
                .filter_by(directory_id=planauflagen().id)
                .filter_by(confirmed=True).count())

    assert count_recipients() == 1
    john = EntryRecipientCollection(org_app.session()).query().first()

    assert org_app.org.meta.get('hourly_maintenance_tasks_last_run') is None

    with freeze_time(datetime(2025, 1, 1, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        assert len(os.listdir(client.app.maildir)) == 0
        assert org_app.org.meta.get('hourly_maintenance_tasks_last_run')

    with freeze_time(datetime(2025, 1, 6, 4, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        entry_1 = planauflagen().entries[0]

        assert len(os.listdir(client.app.maildir)) == 1
        message = client.get_email(0)
        assert message['To'] == john.address
        assert planauflagen().title in message['Subject']
        assert entry_1.name in message['TextBody']

    with freeze_time(datetime(2025, 1, 8, 10, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        entry_2 = planauflagen().entries[1]

        assert len(os.listdir(client.app.maildir)) == 2
        message = client.get_email(1)
        assert message['To'] == john.address
        assert planauflagen().title in message['Subject']
        assert entry_2.name in message['TextBody']

    # before enabling notifications for sport clubs after publication
    with freeze_time(datetime(2025, 2, 1, 6, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        assert len(os.listdir(client.app.maildir)) == 2  # no additional mail

    # enable notifications for sport clubs
    sport_clubs().enable_update_notifications = True
    transaction.commit()

    with freeze_time(datetime(2025, 2, 1, 1, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        # no additional mail, because the entry is not published yet
        assert len(os.listdir(client.app.maildir)) == 2

    with freeze_time(datetime(2025, 2, 3, 10, 0, tzinfo=tz)):
        client.get(get_cronjob_url(job))

        entry_2 = sport_clubs().entries[1]

        # only for still published sports club entry 'Wanderfreunde'
        assert len(os.listdir(client.app.maildir)) == 3
        message = client.get_email(2)
        assert message['To'] == john.address
        assert sport_clubs().title in message['Subject']
        assert entry_2.name in message['TextBody']


def test_delete_unconfirmed_subscribers(org_app, handlers):
    register_echo_handler(handlers)

    job = get_cronjob_by_name(org_app,
                              'delete_unconfirmed_newsletter_subscriptions')
    job.app = org_app

    with freeze_time(datetime(2025, 1, 1, 4, 0)):
        transaction.begin()

        session = org_app.session()

        recipients = RecipientCollection(session)
        recipients.add('one@example.org', confirmed=False)
        recipients.add('two@example.org', confirmed=False)
        # Cronjob should only delete unconfirmed recipients
        recipients.add('three@example.org', confirmed=True)

    # And only unconfirmed subscribers older than 7 days
    recipients.add('four@example.org', confirmed=False)
    transaction.commit()

    recipients = RecipientCollection(org_app.session())
    assert recipients.query().count() == 4

    client = Client(org_app)

    client.get(get_cronjob_url(job))

    recipients = RecipientCollection(org_app.session())
    assert recipients.query().count() == 2
