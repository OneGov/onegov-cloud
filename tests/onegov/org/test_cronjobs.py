import os
import transaction
from datetime import datetime
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.org.models.resource import RoomResource
from onegov.org.models.tan import TANCollection
from onegov.org.models.ticket import ReservationHandler
from onegov.ticket import Handler, Ticket, TicketCollection
from onegov.user import UserCollection
from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.reservation import ResourceCollection
from sedate import ensure_timezone, utcnow
from onegov.form import FormSubmissionCollection
from onegov.org.models import ResourceRecipientCollection
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url
from tests.shared import Client
from tests.shared.utils import add_reservation


class EchoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EHO'}
    es_type_name = 'echo_tickets'


def register_reservation_handler(handlers):
    handlers.register('RSV', ReservationHandler)


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


def test_send_scheduled_newsletters(org_app):
    newsletters = NewsletterCollection(org_app.session())
    recipients = RecipientCollection(org_app.session())

    recipient = recipients.add('info@example.org')
    recipient.confirmed = True

    with freeze_time('2018-05-31 12:00'):
        newsletters.add("Foo", "Bar", scheduled=utcnow())

    transaction.commit()

    newsletter = newsletters.query().one()
    assert newsletter.scheduled

    job = get_cronjob_by_name(org_app, 'hourly_maintenance_tasks')
    job.app = org_app

    with freeze_time('2018-05-31 11:00'):
        client = Client(org_app)
        client.get(get_cronjob_url(job))

        newsletter = newsletters.query().one()
        assert newsletter.scheduled
        assert len(os.listdir(client.app.maildir)) == 0

    with freeze_time('2018-05-31 12:00'):
        client = Client(org_app)
        client.get(get_cronjob_url(job))

        newsletter = newsletters.query().one()
        assert not newsletter.scheduled
        assert len(os.listdir(client.app.maildir)) == 1


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

        transaction.commit()

    # now we go forward a month for archival
    with freeze_time('2022-09-17 04:30'):
        org_app.org.auto_archive_timespan = 30  # days
        org_app.org.auto_delete_timespan = 30  # days

        session.flush()
        # without this assert, the values are somehow not set?
        assert org_app.org.auto_archive_timespan
        assert org_app.org.auto_delete_timespan

        query = session.query(Ticket)
        query = query.filter_by(state='closed')
        assert query.count() == 2

        job = get_cronjob_by_name(org_app, 'archive_old_tickets')
        job.app = org_app
        client = Client(org_app)
        client.get(get_cronjob_url(job))

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

        transaction.commit()

    # now go forward a year
    with freeze_time('2023-06-06 02:00'):
        org_app.org.auto_archive_timespan = 365  # days
        org_app.org.auto_delete_timespan = 365  # days
        org_app.session().flush()

        # without this assert, the values are somehow not set?
        assert org_app.org.auto_archive_timespan
        assert org_app.org.auto_delete_timespan

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
    collection = TANCollection(session)

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
