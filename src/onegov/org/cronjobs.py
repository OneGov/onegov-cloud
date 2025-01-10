from collections import OrderedDict
from babel.dates import get_month_names
from datetime import datetime, timedelta
from itertools import groupby
from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.core.cache import lru_cache
from onegov.core.orm import find_models
from onegov.core.orm.mixins.publication import UTCPublicationMixin
from onegov.core.templates import render_template
from onegov.event import Occurrence, Event
from onegov.file import FileCollection
from onegov.form import FormSubmission, parse_form
from onegov.org.mail import send_ticket_mail
from onegov.newsletter import Newsletter, NewsletterCollection
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultMailLayout
from onegov.org.models import (
    ResourceRecipient, ResourceRecipientCollection, TANAccess, News)
from onegov.org.models.extensions import (
    GeneralFileLinkExtension, DeletableContentExtension)
from onegov.org.models.ticket import ReservationHandler
from onegov.org.views.allocation import handle_rules_cronjob
from onegov.org.views.directory import \
    send_email_notification_for_directory_entry
from onegov.org.views.newsletter import send_newsletter
from onegov.org.views.ticket import delete_tickets_and_related_data
from onegov.reservation import Reservation, Resource, ResourceCollection
from onegov.search import Searchable
from onegov.ticket import Ticket, TicketCollection
from onegov.org.models import TicketMessage, ExtendedDirectoryEntry
from onegov.user import User, UserCollection
from onegov.user.models import TAN
from sedate import to_timezone, utcnow, align_date_to_day
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import undefer
from uuid import UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.orm import Base
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.org.request import OrgRequest


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
def hourly_maintenance_tasks(request: 'OrgRequest') -> None:
    publish_files(request)
    handle_publication_models(request)
    send_scheduled_newsletter(request)
    delete_old_tans(request)
    delete_old_tan_accesses(request)


def send_scheduled_newsletter(request: 'OrgRequest') -> None:
    newsletters = NewsletterCollection(request.session).query().filter(and_(
        Newsletter.scheduled != None,
        Newsletter.scheduled <= (utcnow() + timedelta(seconds=60)),
    ))

    for newsletter in newsletters:
        send_newsletter(request, newsletter, newsletter.open_recipients)
        newsletter.scheduled = None


def publish_files(request: 'OrgRequest') -> None:
    FileCollection(request.session).publish_files()


def handle_publication_models(request: 'OrgRequest') -> None:
    """
    Reindexes all recently published/unpublished objects
    in the elasticsearch database.

    For pages it also updates the propagated access to any
    associated files.

    For directory entries it also sends out e-mail notifications if
    published within the last hour.
    """

    if not hasattr(request.app, 'es_client'):
        return

    def publication_models(
        base: type['Base']
        # NOTE: This should be Iterator[type[Base & UTCPublicationMixin]]
    ) -> 'Iterator[type[UTCPublicationMixin]]':
        yield from find_models(base, lambda cls: issubclass(  # type:ignore
            cls, UTCPublicationMixin)
        )

    objects = []
    session = request.app.session()
    now = utcnow()
    then = request.app.org.meta.get('hourly_maintenance_tasks_last_run',
                                    now - timedelta(hours=1))
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
        if isinstance(obj, GeneralFileLinkExtension):
            # manually invoke the files observer which updates access
            obj.files_observer(obj.files, set(), None, None)

        if isinstance(obj, Searchable):
            request.app.es_orm_events.index(request.app.schema, obj)

        if (isinstance(obj, ExtendedDirectoryEntry) and obj.published and
                obj.directory.enable_update_notifications):
            send_email_notification_for_directory_entry(
                obj.directory, obj, request)

    request.app.org.meta['hourly_maintenance_tasks_last_run'] = now


def delete_old_tans(request: 'OrgRequest') -> None:
    """
    Deletes TANs that are older than half a year.

    Technically we could delete them as soon as they expire
    but for debugging purposes it makes sense to keep them
    around a while longer.
    """

    cutoff = utcnow() - timedelta(days=180)
    query = request.session.query(TAN).filter(TAN.created < cutoff)
    # cronjobs happen outside a regular request, so we don't need
    # to synchronize with the session
    query.delete(synchronize_session=False)


def delete_old_tan_accesses(request: 'OrgRequest') -> None:
    """
    Deletes TAN accesses that are older than half a year.

    Technically we could delete them as soon as they expire
    but for debugging purposes it makes sense to keep them
    around a while longer.
    """

    cutoff = utcnow() - timedelta(days=180)
    query = request.session.query(TANAccess).filter(TANAccess.created < cutoff)
    # cronjobs happen outside a regular request, so we don't need
    # to synchronize with the session
    query.delete(synchronize_session=False)


@OrgApp.cronjob(hour=23, minute=45, timezone='Europe/Zurich')
def process_resource_rules(request: 'OrgRequest') -> None:
    resources = ResourceCollection(request.app.libres_context)

    for resource in resources.query():
        handle_rules_cronjob(resources.bind(resource), request)


def ticket_statistics_common_template_args(
    request: 'OrgRequest',
    collection: TicketCollection
) -> dict[str, Any]:

    args: dict[str, Any] = {}
    layout = DefaultMailLayout(object(), request)

    # get the current ticket count
    count = collection.get_count()
    args['currently_open'] = count.open
    args['currently_pending'] = count.pending
    args['currently_closed'] = count.closed
    # FIXME: a owner of None is not actually valid at runtime
    #        we use this only for generating a link where
    #        owner is not part of the query string, we should
    #        probably come up with a more clean way to handle
    #        situations like that. Ideally morepath would elide
    #        query parameters if they're at their default value.
    args['open_link'] = request.link(
        collection.for_state('open').for_owner(None))  # type:ignore
    args['pending_link'] = request.link(
        collection.for_state('pending').for_owner(None))  # type:ignore
    args['closed_link'] = request.link(
        collection.for_state('closed').for_owner(None))  # type:ignore

    args['title'] = request.translate(
        _('${org} OneGov Cloud Status', mapping={
            'org': request.app.org.title
        })
    )
    args['layout'] = layout
    args['org'] = request.app.org.title

    return args


def ticket_statistics_users(app: OrgApp) -> list[User]:
    users = UserCollection(app.session()).query()
    users = users.filter(User.active == True)
    users = users.filter(User.role.in_(app.settings.org.status_mail_roles))
    users = users.options(undefer('data'))
    return users.all()


@OrgApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_daily_ticket_statistics(request: 'OrgRequest') -> None:

    today = to_timezone(utcnow(), 'Europe/Zurich')

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
def send_weekly_ticket_statistics(request: 'OrgRequest') -> None:

    today = to_timezone(utcnow(), 'Europe/Zurich')

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
def send_monthly_ticket_statistics(request: 'OrgRequest') -> None:

    today = to_timezone(utcnow(), 'Europe/Zurich')

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
def send_daily_resource_usage_overview(request: 'OrgRequest') -> None:
    today = to_timezone(utcnow(), 'Europe/Zurich')
    weekday = WEEKDAYS[today.weekday()]

    # get all recipients which require an e-mail today
    recipients_q = (
        ResourceRecipientCollection(request.session).query()
        .filter(ResourceRecipient.medium == 'email')
        .order_by(None)
        .order_by(ResourceRecipient.address)
        .with_entities(
            ResourceRecipient.address,
            ResourceRecipient.content
        )
    )

    # If the key 'daily_reservations' doesn't exist, the recipient was
    # created before anything else was an option, therefore it must be true
    recipients = [
        (address, content['resources'])
        for address, content in recipients_q
        if content.get('daily_reservations', True)
        and weekday in content['send_on']
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
    default_group = request.translate(_('General'))

    all_resources = tuple(
        ResourceCollection(request.app.libres_context).query()
        .filter(Resource.id.in_(resource_ids))
        .with_entities(
            Resource.id,
            Resource.group,
            Resource.title,
            Resource.definition
        )
        .order_by(Resource.group, Resource.name, Resource.id)
    )

    resources = OrderedDict(
        (r.id.hex, f'{r.group or default_group} - {r.title}')
        for r in all_resources
    )

    @lru_cache(maxsize=128)
    def form(definition: str) -> type['Form']:
        return parse_form(definition)

    # get the reservations of this day
    start = align_date_to_day(today, 'Europe/Zurich', 'down')
    end = align_date_to_day(today, 'Europe/Zurich', 'up')

    # load all approved reservations for all required resources
    all_reservations = [
        r for r in request.session.query(Reservation)
        .filter(Reservation.resource.in_(resource_ids))
        .filter(Reservation.status == 'approved')
        .filter(Reservation.data != None)
        .filter(and_(start <= Reservation.start, Reservation.start <= end))
        .order_by(Reservation.resource, Reservation.start)
        if r.data and r.data.get('accepted')
    ]

    # load all linked form submissions
    if all_reservations:
        q = request.session.query(FormSubmission)
        q = q.filter(FormSubmission.id.in_(
            {r.token for r in all_reservations}
        ))

        submissions = {submission.id: submission for submission in q}

        for reservation in all_reservations:
            submission = submissions.get(reservation.token)
            # FIXME: Is this an actual relationship that exists or do
            #        we set this attribute temporarily for the mail
            #        template? It might be cleaner to do this lookup
            #        inside the template, rather than rely on a
            #        temporary attribute
            reservation.submission = submission  # type:ignore

    # group th reservations by resource
    reservations = {
        resid.hex: tuple(reservations) for resid, reservations in groupby(
            all_reservations, key=lambda r: r.resource
        )
    }

    # send out the e-mails
    args: RenderData = {
        'layout': DefaultMailLayout(object(), request),
        'title': request.translate(
            _('${org} Reservation Overview', mapping={
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


@OrgApp.cronjob(hour='*', minute='*/30', timezone='UTC')
def end_chats_and_create_tickets(request: 'OrgRequest') -> None:
    half_hour_ago = utcnow() - timedelta(minutes=30)

    chats = ChatCollection(request.session).query().filter(
        Chat.active == True).filter(Chat.chat_history != []).filter(
            Chat.last_change < half_hour_ago)

    for chat in chats:
        chat.active = False
        with chats.session.no_autoflush:
            ticket = TicketCollection(request.session).open_ticket(
                handler_code='CHT', handler_id=chat.id.hex
            )
            TicketMessage.create(ticket, request, 'opened')

            send_ticket_mail(
                request=request,
                template='mail_turned_chat_into_ticket.pt',
                subject=_('Your Chat has been turned into a ticket'),
                receivers=(chat.email, ),
                ticket=ticket,
                content={
                    'model': chats,
                    'ticket': ticket,
                    'chat': chat,
                    'organisation': request.app.org.title,
                }
            )


@OrgApp.cronjob(hour=4, minute=30, timezone='Europe/Zurich')
def archive_old_tickets(request: 'OrgRequest') -> None:

    archive_timespan = request.app.org.auto_archive_timespan
    session = request.session

    if archive_timespan is None:
        return  # type:ignore[unreachable]

    if archive_timespan == 0:
        return

    cutoff_date = utcnow() - timedelta(days=archive_timespan)
    query = session.query(Ticket)
    query = query.filter(Ticket.state == 'closed')
    query = query.filter(Ticket.last_change <= cutoff_date)
    further_back = cutoff_date - timedelta(days=712)
    for ticket in query:
        if isinstance(ticket.handler, ReservationHandler):
            if ticket.handler.has_future_reservation:
                continue
            most_future_reservation = ticket.handler.most_future_reservation
            if (
                most_future_reservation is not None
                and most_future_reservation.end is not None
                and most_future_reservation.end > further_back
            ):
                continue
        ticket.archive_ticket()


@OrgApp.cronjob(hour=5, minute=30, timezone='Europe/Zurich')
def delete_old_tickets(request: 'OrgRequest') -> None:
    delete_timespan = request.app.org.auto_delete_timespan
    session = request.session

    if delete_timespan is None:
        return  # type:ignore[unreachable]

    if delete_timespan == 0:
        return

    cutoff_date = utcnow() - timedelta(days=delete_timespan)
    query = session.query(Ticket)
    query = query.filter(Ticket.state == 'archived')
    query = query.filter(Ticket.last_change <= cutoff_date)

    delete_tickets_and_related_data(request, query)


@OrgApp.cronjob(hour=9, minute=30, timezone='Europe/Zurich')
def send_monthly_mtan_statistics(request: 'OrgRequest') -> None:

    today = to_timezone(utcnow(), 'Europe/Zurich')

    if today.weekday() != MON or today.day > 7:
        return

    year = today.year
    month = today.month

    # rewind to previous month
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1

    # count all the mTAN created in that period
    # we use UTC as a reference for day boundaries so we don't have to
    # calculate the boundaries ourselves and risk creating overlapping
    # intervals
    mtan_count: int = request.session.query(func.count(TAN.id)).filter(and_(
        func.extract('year', TAN.created) == year,
        func.extract('month', TAN.created) == month,
        TAN.meta['mobile_number'].isnot(None)
    )).scalar()
    if not mtan_count:
        # don't send a mail if we generated no mTANs
        return

    month_name = get_month_names('wide', locale='de_CH')[month]
    org_name = request.app.org.name

    # FIXME: Make e-mail configurable and text translatable
    # TODO: Include more detailed stats? E.g. volume per country code
    #       or numbers that triggered more than a configured amount
    #       to catch suspicious activity
    request.app.send_transactional_email(
        receivers='info@seantis.ch',
        subject=f'{org_name}: mTAN Statistik {month_name} {year}',
        plaintext=(
            f'{org_name} hatte im {month_name} {year}\n'
            f'{mtan_count} mTAN SMS versendet'
        )
    )


@OrgApp.cronjob(hour=4, minute=0, timezone='Europe/Zurich')
def delete_content_marked_deletable(request: 'OrgRequest') -> None:
    """ Find all models inheriting from DeletableContentExtension, iterate
    over objects marked as `deletable` and delete them if expired.

    Currently extended directory entries, news, events and occurrences.

    """

    now = to_timezone(utcnow(), 'Europe/Zurich')
    count = 0

    for base in request.app.session_manager.bases:
        for model in find_models(base, lambda cls: issubclass(
                cls, DeletableContentExtension)):

            query = request.session.query(model)
            query = query.filter(model.delete_when_expired == True)
            for obj in query:
                # delete entry if end date passed
                if isinstance(obj, (News, ExtendedDirectoryEntry)):
                    if obj.publication_end and obj.publication_end < now:
                        request.session.delete(obj)
                        count += 1

    # check on past events and its occurrences
    if request.app.org.delete_past_events:
        query = request.session.query(Occurrence)
        query = query.filter(Occurrence.end < now)
        for obj in query:
            request.session.delete(obj)
            count += 1

        query = request.session.query(Event)
        for obj in query:
            if not obj.future_occurrences(limit=1).all():
                request.session.delete(obj)
                count += 1

    if count:
        print(f'Cron: Deleted {count} expired deletable objects in db')
