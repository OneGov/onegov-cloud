import transaction

from base64 import b64decode
from datetime import datetime
from freezegun import freeze_time
from onegov.ticket import Handler, Ticket, TicketCollection
from onegov.user import UserCollection
from webtest import TestApp as Client
from sedate import ensure_timezone


def get_cronjob_by_name(app, name):
    for cronjob in app.config.cronjob_registry.cronjobs.values():
        if name in cronjob.name:
            return cronjob


def get_cronjob_url(cronjob):
    return '/cronjobs/{}'.format(cronjob.id)


def register_echo_handler(handlers):

    class EchoTicket(Ticket):
        __mapper_args__ = {'polymorphic_identity': 'ECO'}
        es_type_name = 'eco_tickets'

    @handlers.registered_handler('ECO')
    class EchoHandler(Handler):

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


def get_mail(outbox, index):
    message = outbox[0]

    return {
        'from': message['From'],
        'reply_to': message['Reply-To'],
        'subject': message['Subject'],
        'text': b64decode(
            ''.join(message.get_payload(0).as_string().splitlines()[3:])
        ).decode('utf-8'),
        'html': b64decode(
            ''.join(message.get_payload(1).as_string().splitlines()[3:])
        ).decode('utf-8')
    }


def test_ticket_statistics(town_app, smtp, handlers):
    register_echo_handler(handlers)

    client = Client(town_app)

    job = get_cronjob_by_name(town_app, 'ticket_statistics')
    job.app = town_app

    url = get_cronjob_url(job)

    tz = ensure_timezone('Europe/Zurich')

    assert len(smtp.outbox) == 0

    # do not run on the weekends
    with freeze_time(datetime(2016, 1, 2, tzinfo=tz)):
        client.get(url)

    with freeze_time(datetime(2016, 1, 3, tzinfo=tz)):
        client.get(url)

    assert len(smtp.outbox) == 0

    session = town_app.session()
    collection = TicketCollection(session)

    tickets = [
        collection.open_ticket(
            handler_id='1',
            handler_code='ECO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='ECO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='3',
            handler_code='ECO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='4',
            handler_code='ECO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='5',
            handler_code='ECO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        ),
        collection.open_ticket(
            handler_id='6',
            handler_code='ECO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz)
        )
    ]

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
