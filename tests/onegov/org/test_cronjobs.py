import transaction

from datetime import datetime
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.org.models.resource import RoomResource
from onegov.ticket import Handler, Ticket, TicketCollection
from onegov.user import UserCollection
from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.reservation import ResourceCollection
from webtest import TestApp as Client
from sedate import ensure_timezone, utcnow
from onegov.form import FormSubmissionCollection
from onegov.org.models import ResourceRecipientCollection
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url, \
    get_mail


def register_echo_handler(handlers):

    class EchoTicket(Ticket):
        __mapper_args__ = {'polymorphic_identity': 'EHO'}
        es_type_name = 'echo_tickets'

    @handlers.registered_handler('EHO')
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


def test_ticket_statistics(org_app, smtp, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)

    job = get_cronjob_by_name(org_app, 'ticket_statistics')
    job.app = org_app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(smtp.outbox) == 0

    # do not run on the weekends
    with freeze_time(datetime(2016, 1, 2, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 3, tzinfo=tz)):
        client.get(url)

    assert len(smtp.outbox) == 0

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
    users[1].data = {'daily_ticket_statistics': False}

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

    assert len(smtp.outbox) == 1
    message = get_mail(smtp.outbox, 0)

    assert message['subject'] == 'Govikon OneGov Cloud Status'
    txt = message['text']
    assert "Folgendes ist während des Wochenendes auf der Govikon" in txt
    assert "6 Tickets wurden eröffnet." in txt
    assert "2 Tickets wurden angenommen." in txt
    assert "3 Tickets wurden geschlossen." in txt
    assert "Zur Zeit ist 1 Ticket offen" in txt
    assert "2 Tickets sind in Bearbeitung" in txt
    assert "Wir wünschen Ihnen eine schöne Woche!" in txt
    assert "Das OneGov Cloud Team" in txt
    assert "/unsubscribe?token=" in txt
    assert "abmelden" in txt


def test_daily_reservation_overview(org_app, smtp):
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
        send_on=['FR'],
        resources=[
            gymnasium.id.hex
        ]
    )
    recipients.add(
        name='Day',
        medium='email',
        address='day@example.org',
        send_on=['FR'],
        resources=[
            dailypass.id.hex
        ]
    )
    recipients.add(
        name='Both',
        medium='email',
        address='both@example.org',
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
        with freeze_time(datetime(2017, 1, day, tzinfo=tz)):
            client.get(url)

            assert len(smtp.outbox) == 0

    # only send e-mails to the users with the right selection
    with freeze_time(datetime(2017, 1, 6, tzinfo=tz)):
        client.get(url)

    assert len(smtp.outbox) == 2

    with freeze_time(datetime(2017, 1, 7, tzinfo=tz)):
        client.get(url)

    assert len(smtp.outbox) == 3

    # there are no really confirmed reservations at this point, so the
    # e-mail will not contain any information info
    del smtp.outbox[:]

    with freeze_time(datetime(2017, 1, 6, tzinfo=tz)):
        client.get(url)

    for i in (0, 1):
        message = get_mail(smtp.outbox, i)
        assert "Heute keine Reservationen" in message['text']
        assert "-reservation" not in message['text']

    assert get_mail(smtp.outbox, 0)['to'] == 'day@example.org'
    assert "Allgemein - Dailypass" in get_mail(smtp.outbox, 0)['text']
    assert "Allgemein - Gymnasium" not in get_mail(smtp.outbox, 0)['text']

    assert get_mail(smtp.outbox, 1)['to'] == 'gym@example.org'
    assert "Allgemein - Gymnasium" in get_mail(smtp.outbox, 1)['text']
    assert "Allgemein - Dailypass" not in get_mail(smtp.outbox, 1)['text']

    # once we confirm the reservation it shows up in the e-mail
    del smtp.outbox[:]

    gymnasium = resources.by_name('gymnasium')
    r = gymnasium.scheduler.reservations_by_token(gym_reservation_token)[0]
    r.data = {'accepted': True}

    transaction.commit()

    with freeze_time(datetime(2017, 1, 6, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2017, 1, 7, tzinfo=tz)):
        client.get(url)

    assert '0xdeadbeef' not in get_mail(smtp.outbox, 0)['text']
    assert '0xdeadbeef' in get_mail(smtp.outbox, 1)['text']

    assert get_mail(smtp.outbox, 2)['to'] == 'both@example.org'
    assert 'Gymnasium' in get_mail(smtp.outbox, 2)['text']
    assert 'Dailypass' in get_mail(smtp.outbox, 2)['text']
    assert '0xdeadbeef' not in get_mail(smtp.outbox, 2)['text']  # diff. day

    # this also works for the other reservation which has no data
    del smtp.outbox[:]

    dailypass = resources.by_name('dailypass')
    r = dailypass.scheduler.reservations_by_token(day_reservation_token)[0]
    r.data = {'accepted': True}

    transaction.commit()

    with freeze_time(datetime(2017, 1, 6, tzinfo=tz)):
        client.get(url)

    assert 'gym-reservation' not in get_mail(smtp.outbox, 0)['text']
    assert 'day-reservation' in get_mail(smtp.outbox, 0)['text']

    assert 'day-reservation' not in get_mail(smtp.outbox, 1)['text']
    assert 'gym-reservation' in get_mail(smtp.outbox, 1)['text']


def test_send_scheduled_newsletters(org_app, smtp):
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
        assert len(smtp.outbox) == 0

    with freeze_time('2018-05-31 12:00'):
        client = Client(org_app)
        client.get(get_cronjob_url(job))

        newsletter = newsletters.query().one()
        assert not newsletter.scheduled
        assert len(smtp.outbox) == 1
