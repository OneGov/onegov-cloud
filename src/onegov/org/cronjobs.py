from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import groupby
from onegov.core.cache import lru_cache
from onegov.core.orm import find_models
from onegov.core.orm.mixins.publication import UTCPublicationMixin
from onegov.core.templates import render_template
from onegov.file import FileCollection
from onegov.form import FormSubmission, parse_form
from onegov.newsletter import Newsletter, NewsletterCollection
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultMailLayout
from onegov.org.models import ResourceRecipient, ResourceRecipientCollection
from onegov.org.views.allocation import handle_rules_cronjob
from onegov.org.views.newsletter import send_newsletter
from onegov.org.views.ticket import delete_tickets_and_related_data
from onegov.reservation import Reservation, Resource, ResourceCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.user import User, UserCollection
from sedate import replace_timezone, to_timezone, utcnow, align_date_to_day
from sqlalchemy import and_, or_
from sqlalchemy.orm import undefer
from uuid import UUID


MON = 0
TUE = 1
WED = 2
THU = 3
FRI = 4
SAT = 5
SUN = 6


WEEKDAYS = (
    'MO',
    'TU',
    'WE',
    'TH',
    'FR',
    'SA',
    'SU',
)


@OrgApp.cronjob(hour='*', minute=0, timezone='UTC')
def hourly_maintenance_tasks(request):
    publish_files(request)
    reindex_published_models(request)
    send_scheduled_newsletter(request)
    # for testing
    # archive_old_tickets(request)


def send_scheduled_newsletter(request):
    newsletters = NewsletterCollection(request.session).query().filter(and_(
        Newsletter.scheduled != None,
        Newsletter.scheduled <= (utcnow() + timedelta(seconds=60)),
    ))

    for newsletter in newsletters:
        send_newsletter(request, newsletter, newsletter.open_recipients)
        newsletter.scheduled = None


def publish_files(request):
    FileCollection(request.session).publish_files()


def reindex_published_models(request):
    """
    Reindexes all recently published objects
    in the elasticsearch database.
    """

    if not hasattr(request.app, 'es_client'):
        return

    def publication_models(base):
        yield from find_models(base, lambda cls: issubclass(
            cls, UTCPublicationMixin)
        )

    objects = []
    session = request.app.session()
    now = utcnow()
    then = now - timedelta(hours=1)
    for base in request.app.session_manager.bases:
        for model in publication_models(base):
            query = session.query(model).filter(
                or_(
                    and_(
                        then <= model.publication_start,
                        now >= model.publication_start
                    ),
                    and_(
                        then <= model.publication_end,
                        now >= model.publication_end
                    )
                )
            )
            objects.extend(query.all())

    for obj in objects:
        request.app.es_orm_events.index(request.app.schema, obj)


@OrgApp.cronjob(hour=23, minute=45, timezone='Europe/Zurich')
def process_resource_rules(request):
    resources = ResourceCollection(request.app.libres_context)

    for resource in resources.query():
        handle_rules_cronjob(resources.bind(resource), request)


def ticket_statistics_common_template_args(request, collection):
    args = {}
    layout = DefaultMailLayout(object(), request)

    # get the current ticket count
    count = collection.get_count()
    args['currently_open'] = count.open
    args['currently_pending'] = count.pending
    args['currently_closed'] = count.closed
    args['open_link'] = request.link(
        collection.for_state('open').for_owner(None))
    args['pending_link'] = request.link(
        collection.for_state('pending').for_owner(None))
    args['closed_link'] = request.link(
        collection.for_state('closed').for_owner(None))

    args['title'] = request.translate(
        _("${org} OneGov Cloud Status", mapping={
            'org': request.app.org.title
        })
    )
    args['layout'] = layout
    args['org'] = request.app.org.title

    return args


def ticket_statistics_users(app):
    users = UserCollection(app.session()).query()
    users = users.filter(User.active == True)
    users = users.filter(User.role.in_(app.settings.org.status_mail_roles))
    users = users.options(undefer('data'))
    return users.all()


@OrgApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_daily_ticket_statistics(request):

    today = replace_timezone(datetime.utcnow(), 'UTC')
    today = to_timezone(today, 'Europe/Zurich')

    if today.weekday() in (SAT, SUN):
        return

    if not request.app.send_ticket_statistics:
        return

    app = request.app
    collection = TicketCollection(app.session())
    args = ticket_statistics_common_template_args(request, collection)

    # get tickets created yesterday or on the weekend
    end = datetime(today.year, today.month, today.day, tzinfo=today.tzinfo)
    if today.weekday() == MON:
        start = end - timedelta(days=2)
    else:
        start = end - timedelta(days=1)

    query = collection.query()
    query = query.filter(Ticket.created >= start)
    query = query.filter(Ticket.created <= end)
    args['opened'] = query.count()

    query = collection.query()
    query = query.filter(Ticket.modified >= start)
    query = query.filter(Ticket.modified <= end)
    query = query.filter(Ticket.state == 'pending')
    args['pending'] = query.count()

    query = collection.query()
    query = query.filter(Ticket.modified >= start)
    query = query.filter(Ticket.modified <= end)
    query = query.filter(Ticket.state == 'closed')
    args['closed'] = query.count()

    args['is_monday'] = today.weekday() == MON

    for user in ticket_statistics_users(app):

        if not user.data or user.data.get('ticket_statistics') != 'daily':
            continue

        unsubscribe = args['layout'].unsubscribe_link(user.username)

        args['username'] = user.username
        args['unsubscribe'] = unsubscribe
        content = render_template(
            'mail_daily_ticket_statistics.pt', request, args
        )

        app.send_marketing_email(
            subject=args['title'],
            receivers=(user.username, ),
            content=content,
            headers={
                'List-Unsubscribe': f'<{unsubscribe}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
            }
        )


@OrgApp.cronjob(hour=8, minute=45, timezone='Europe/Zurich')
def send_weekly_ticket_statistics(request):

    today = replace_timezone(datetime.utcnow(), 'UTC')
    today = to_timezone(today, 'Europe/Zurich')

    if today.weekday() != MON:
        return

    if not request.app.send_ticket_statistics:
        return

    app = request.app
    collection = TicketCollection(app.session())
    args = ticket_statistics_common_template_args(request, collection)

    # get tickets created in the last week
    end = datetime(today.year, today.month, today.day, tzinfo=today.tzinfo)
    start = end - timedelta(days=7)

    query = collection.query()
    query = query.filter(Ticket.created >= start)
    query = query.filter(Ticket.created <= end)
    args['opened'] = query.count()

    query = collection.query()
    query = query.filter(Ticket.modified >= start)
    query = query.filter(Ticket.modified <= end)
    query = query.filter(Ticket.state == 'pending')
    args['pending'] = query.count()

    query = collection.query()
    query = query.filter(Ticket.modified >= start)
    query = query.filter(Ticket.modified <= end)
    query = query.filter(Ticket.state == 'closed')
    args['closed'] = query.count()

    # send one e-mail per user
    for user in ticket_statistics_users(app):

        if user.data and user.data.get('ticket_statistics') != 'weekly':
            continue

        unsubscribe = args['layout'].unsubscribe_link(user.username)

        args['username'] = user.username
        args['unsubscribe'] = unsubscribe
        content = render_template(
            'mail_weekly_ticket_statistics.pt', request, args
        )

        app.send_marketing_email(
            subject=args['title'],
            receivers=(user.username, ),
            content=content,
            headers={
                'List-Unsubscribe': f'<{unsubscribe}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
            }
        )


@OrgApp.cronjob(hour=9, minute=0, timezone='Europe/Zurich')
def send_monthly_ticket_statistics(request):

    today = replace_timezone(datetime.utcnow(), 'UTC')
    today = to_timezone(today, 'Europe/Zurich')

    if today.weekday() != MON or today.day > 7:
        return

    if not request.app.send_ticket_statistics:
        return

    args = {}
    app = request.app
    collection = TicketCollection(app.session())
    args = ticket_statistics_common_template_args(request, collection)

    # get tickets created in the last four or five weeks
    # depending on when the first monday was last month
    end = datetime(today.year, today.month, today.day, tzinfo=today.tzinfo)
    start = end - timedelta(days=28)
    if start.day > 7:
        start -= timedelta(days=7)

    query = collection.query()
    query = query.filter(Ticket.created >= start)
    query = query.filter(Ticket.created <= end)
    args['opened'] = query.count()

    query = collection.query()
    query = query.filter(Ticket.modified >= start)
    query = query.filter(Ticket.modified <= end)
    query = query.filter(Ticket.state == 'pending')
    args['pending'] = query.count()

    query = collection.query()
    query = query.filter(Ticket.modified >= start)
    query = query.filter(Ticket.modified <= end)
    query = query.filter(Ticket.state == 'closed')
    args['closed'] = query.count()

    # send one e-mail per user
    for user in ticket_statistics_users(app):

        if not user.data or user.data.get('ticket_statistics') != 'monthly':
            continue

        unsubscribe = args['layout'].unsubscribe_link(user.username)

        args['username'] = user.username
        args['unsubscribe'] = unsubscribe
        content = render_template(
            'mail_monthly_ticket_statistics.pt', request, args
        )

        app.send_marketing_email(
            subject=args['title'],
            receivers=(user.username, ),
            content=content,
            headers={
                'List-Unsubscribe': f'<{unsubscribe}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
            }
        )


@OrgApp.cronjob(hour=6, minute=5, timezone='Europe/Zurich')
def send_daily_resource_usage_overview(request):
    today = to_timezone(utcnow(), 'Europe/Zurich')
    weekday = WEEKDAYS[today.weekday()]

    # get all recipients which require an e-mail today
    q = ResourceRecipientCollection(request.session).query()
    q = q.filter(ResourceRecipient.medium == 'email')
    q = q.order_by(None).order_by(ResourceRecipient.address)
    q = q.with_entities(
        ResourceRecipient.address,
        ResourceRecipient.content
    )

    # If the key 'daily_reservations' doesn't exist, the recipient was
    # created before anything else was an option, therefore it must be true
    recipients = [
        (r.address, r.content['resources'])
        for r in q if (
            r.content.get('daily_reservations', True)
            and weekday in r.content['send_on']
        )
    ]

    if not recipients:
        return

    # extract a list of all required resource ids
    resource_ids = {
        UUID(rid)
        for _, resources in recipients
        for rid in resources
    }

    # get the resource titles and ids
    default_group = request.translate(_("General"))

    q = ResourceCollection(request.app.libres_context).query()
    q = q.filter(Resource.id.in_(resource_ids))
    q = q.with_entities(
        Resource.id,
        Resource.group,
        Resource.title,
        Resource.definition
    )

    all_resources = tuple(
        q.order_by(Resource.group, Resource.name, Resource.id)
    )

    resources = OrderedDict(
        (r.id.hex, "{group} - {title}".format(
            group=r.group or default_group,
            title=r.title
        )) for r in all_resources
    )

    @lru_cache(maxsize=128)
    def form(definition):
        return parse_form(definition)

    # get the reservations of this day
    start = align_date_to_day(today, 'Europe/Zurich', 'down')
    end = align_date_to_day(today, 'Europe/Zurich', 'up')

    # load all approved reservations for all required resources
    q = request.session.query(Reservation)
    q = q.filter(Reservation.resource.in_(resource_ids))
    q = q.filter(Reservation.status == 'approved')
    q = q.filter(Reservation.data != None)
    q = q.filter(and_(start <= Reservation.start, Reservation.start <= end))
    q = q.order_by(Reservation.resource, Reservation.start)

    all_reservations = [r for r in q if r.data.get('accepted')]

    # load all linked form submissions
    if all_reservations:
        q = request.session.query(FormSubmission)
        q = q.filter(FormSubmission.id.in_(
            {r.token for r in all_reservations}
        ))

        submissions = {submission.id: submission for submission in q}

        for reservation in all_reservations:
            reservation.submission = submissions.get(reservation.token)

    # group th reservations by resource
    reservations = {
        resid.hex: tuple(reservations) for resid, reservations in groupby(
            all_reservations, key=lambda r: r.resource
        )
    }

    # send out the e-mails
    args = {
        'layout': DefaultMailLayout(object(), request),
        'title': request.translate(
            _("${org} Reservation Overview", mapping={
                'org': request.app.org.title
            })
        ),
        'organisation': request.app.org.title,
        'resources': resources,
        'parse_form': form
    }

    for address, included_resources in recipients:
        args['included_resources'] = included_resources
        args['reservations'] = reservations

        content = render_template(
            'mail_daily_resource_usage_overview.pt', request, args
        )

        request.app.send_transactional_email(
            subject=args['title'],
            receivers=(address, ),
            content=content
        )


@OrgApp.cronjob(hour=4, minute=30, timezone='Europe/Zurich')
def archive_old_tickets(request):

    archive_timespan = request.app.org.auto_archive_timespan

    session = request.session

    if archive_timespan is None:
        return

    if archive_timespan == 0:
        return

    archive_timespan = timedelta(days=archive_timespan)

    diff = utcnow() - archive_timespan
    query = session.query(Ticket)
    query = query.filter(Ticket.state == 'closed')
    query = query.filter(Ticket.created <= diff)

    now = utcnow()
    query.update(
        {'state': 'archived', 'last_state_change': now},
    )


@OrgApp.cronjob(hour=5, minute=30, timezone='Europe/Zurich')
def delete_old_tickets(request):
    delete_timespan = request.app.org.auto_delete_timespan
    session = request.session

    if delete_timespan is None:
        return

    if delete_timespan == 0:
        return

    delete_timespan = timedelta(days=delete_timespan)

    diff = utcnow() - delete_timespan
    query = session.query(Ticket)
    query = query.filter(Ticket.state == 'archived')
    query = query.filter(Ticket.created <= diff)

    delete_tickets_and_related_data(request, query)
