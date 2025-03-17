from __future__ import annotations
import traceback
from collections import OrderedDict

import requests
import logging
from babel.dates import get_month_names
from datetime import datetime, timedelta
from functools import lru_cache
from itertools import groupby

from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.core.orm import find_models, Base
from onegov.core.orm.mixins.publication import UTCPublicationMixin
from onegov.core.templates import render_template
from onegov.directory.collections.directory import EntryRecipientCollection
from onegov.event import Occurrence, Event
from onegov.file import FileCollection
from onegov.form import FormSubmission, parse_form, Form
from onegov.newsletter.models import Recipient
from onegov.org.mail import send_ticket_mail
from onegov.newsletter import (Newsletter, NewsletterCollection,
                               RecipientCollection)
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultMailLayout
from onegov.org.models import (
    ResourceRecipient,
    ResourceRecipientCollection,
    TANAccess,
    News,
    PushNotification
)
from onegov.org.models.extensions import (
    GeneralFileLinkExtension, DeletableContentExtension)
from onegov.org.models.ticket import ReservationHandler
from onegov.gever.encrypt import decrypt_symmetric
from cryptography.fernet import InvalidToken
from sqlalchemy.exc import IntegrityError
from onegov.org.views.allocation import handle_rules_cronjob
from onegov.org.views.directory import (
    send_email_notification_for_directory_entry)
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
from onegov.org.notification_service import (
    get_notification_service,
)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from sqlalchemy.orm import Session
    from sqlalchemy.orm import Query

    from onegov.org.request import OrgRequest


log = logging.getLogger('onegov.org.cronjobs')


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
def hourly_maintenance_tasks(request: OrgRequest) -> None:
    publish_files(request)
    handle_publication_models(request)
    send_scheduled_newsletter(request)
    delete_old_tans(request)
    delete_old_tan_accesses(request)


def send_scheduled_newsletter(request: OrgRequest) -> None:
    newsletters = NewsletterCollection(request.session).query().filter(and_(
        Newsletter.scheduled != None,
        Newsletter.scheduled <= (utcnow() + timedelta(seconds=60)),
    ))

    for newsletter in newsletters:
        send_newsletter(request, newsletter, newsletter.open_recipients)
        newsletter.scheduled = None


def publish_files(request: OrgRequest) -> None:
    FileCollection(request.session).publish_files()


def handle_publication_models(request: OrgRequest) -> None:
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
        base: type[Base]
        # NOTE: This should be Iterator[type[Base & UTCPublicationMixin]]
    ) -> Iterator[type[UTCPublicationMixin]]:
        yield from find_models(base, lambda cls: issubclass(  # type:ignore
            cls, UTCPublicationMixin)
        )

    objects = set()
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
            objects.update(query.all())

    for obj in objects:
        if isinstance(obj, GeneralFileLinkExtension):
            # manually invoke the files observer which updates access
            obj.files_observer(obj.files, set(), None, None)

        if isinstance(obj, Searchable):
            request.app.es_orm_events.index(request.app.schema, obj)

        if (isinstance(obj, ExtendedDirectoryEntry) and
                obj.published and
                obj.access in ('public', 'mtan') and
                obj.directory.enable_update_notifications):
            send_email_notification_for_directory_entry(
                obj.directory, obj, request)

    request.app.org.meta['hourly_maintenance_tasks_last_run'] = now


def delete_old_tans(request: OrgRequest) -> None:
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


def delete_old_tan_accesses(request: OrgRequest) -> None:
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
def process_resource_rules(request: OrgRequest) -> None:
    resources = ResourceCollection(request.app.libres_context)

    for resource in resources.query():
        handle_rules_cronjob(resources.bind(resource), request)


def ticket_statistics_common_template_args(
    request: OrgRequest,
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
def send_daily_ticket_statistics(request: OrgRequest) -> None:

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
def send_weekly_ticket_statistics(request: OrgRequest) -> None:

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
def send_monthly_ticket_statistics(request: OrgRequest) -> None:

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
def send_daily_resource_usage_overview(request: OrgRequest) -> None:
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
    def form(definition: str) -> type[Form]:
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
def end_chats_and_create_tickets(request: OrgRequest) -> None:
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
def archive_old_tickets(request: OrgRequest) -> None:

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
def delete_old_tickets(request: OrgRequest) -> None:
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
def send_monthly_mtan_statistics(request: OrgRequest) -> None:

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
def delete_content_marked_deletable(request: OrgRequest) -> None:
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


@OrgApp.cronjob(hour=7, minute=0, timezone='Europe/Zurich')
def update_newsletter_email_bounce_statistics(
    request: OrgRequest
) -> None:
    # I choose hour=7 as the maximum time difference between Eastern Standard
    # Time (EST) and Central European Summer Time (CEST) is 7 hours. This
    # occurs when EST is observing standard time (UTC-5) and CEST is observing
    # daylight saving time (UTC+2).
    # Postmark uses EST in `fromdate` and `todate`, see
    # https://postmarkapp.com/developer/api/bounce-api.

    def get_postmark_token() -> str:
        # read postmark token from the applications configuration
        mail_config = request.app.mail
        if mail_config:
            mailer = mail_config.get('marketing', {}).get('mailer', None)
            if mailer == 'postmark':
                return mail_config.get('marketing', {}).get('token', '')

        return ''

    def get_bounces() -> list[dict[str, Any]]:
        token = get_postmark_token()
        yesterday = utcnow() - timedelta(days=1)
        r = None

        try:
            r = requests.get(
                'https://api.postmarkapp.com/bounces?count=500&offset=0',
                f'fromDate={yesterday.date()}&toDate='
                f'{yesterday.date()}&inactive=true',
                headers={
                    'Accept': 'application/json',
                    'X-Postmark-Server-Token': token,
                },
                timeout=30,
            )
            r.raise_for_status()
            bounces = r.json().get('Bounces', [])
        except requests.exceptions.HTTPError as http_err:
            if r and r.status_code == 401:
                raise RuntimeWarning(
                    f'Postmark API token is not set or invalid: {http_err}'
                ) from None
            else:
                raise

        return bounces

    postmark_bounces = get_bounces()
    collections = (RecipientCollection, EntryRecipientCollection)
    for collection in collections:
        recipients = collection(request.session)

        for bounce in postmark_bounces:
            email = bounce.get('Email', '')
            inactive = bounce.get('Inactive', False)
            recipient = recipients.by_address(email)

            if recipient and inactive:
                print(f'Mark recipient {recipient.address} as inactive')
                recipient.mark_inactive()


@OrgApp.cronjob(hour=4, minute=30, timezone='Europe/Zurich')
def delete_unconfirmed_newsletter_subscriptions(request: OrgRequest) -> None:
    """ Delete unconfirmed newsletter subscriptions older than 7 days. """

    now = to_timezone(utcnow(), 'Europe/Zurich')
    cutoff_date = now - timedelta(days=7)
    count = 0

    query = request.session.query(Recipient)
    query = query.filter(Recipient.confirmed == False)
    query = query.filter(Recipient.created < cutoff_date)
    for obj in query:
        request.session.delete(obj)
        count += 1

    if count:
        print(f'Cron: Deleted {count} unconfirmed newsletter subscriptions')


def get_news_for_push_notification(session: Session) -> Query[News]:
    # Use UTC time for database comparisons since publication_start is stored
    # in UTC
    now = utcnow()

    # Get all news items that should trigger push notifications
    query = session.query(News)
    query = query.filter(News.published.is_(True))
    query = query.filter(News.publication_start <= now)

    news_with_sent_notifications = session.query(
        PushNotification.news_id
    ).subquery()
    query = query.filter(~News.id.in_(news_with_sent_notifications))
    only_public_news = query.filter(
        or_(
            News.meta['access'].astext == 'public',
            News.meta['access'].astext.is_(None)
        )
    )

    only_public_with_send_push_notification = only_public_news.filter(
        News.meta['send_push_notifications_to_app'].astext == 'true'
    )
    return only_public_with_send_push_notification


@OrgApp.cronjob(hour='*', minute='*/10', timezone='UTC')
def send_push_notifications_for_news(request: OrgRequest) -> None:
    """
    Cronjob that runs every 10 minutes to send push notifications for news
    items that were published within the last 10 minutes.

    It collects all news items with:
    - Publication start date within the last 10 minutes
    - send_push_notifications_to_app flag enabled
    - Defined push_notifications topics

    Then uses Firebase to send notifications to the corresponding topics.
    """
    session = request.session
    org = request.app.org

    # Skip if no Firebase credentials are configured
    if not org.firebase_adminsdk_credential:
        print('No Firebase credentials configured')
        return

    news_items = get_news_for_push_notification(session).all()
    if not news_items:
        print('No news items found with push notifications enabled')
        return

    # Get the mapping
    topic_mapping = org.meta.get('selectable_push_notification_options', [])
    if not topic_mapping:
        print('selectable_push_notification_options is empty')
        return

    # Decrypt the Firebase credentials
    key_base64 = request.app.hashed_identity_key
    encrypted_creds = org.firebase_adminsdk_credential
    if not encrypted_creds:
        return

    try:
        firebase_creds_json = decrypt_symmetric(
            encrypted_creds.encode('utf-8'), key_base64
        )
    except InvalidToken:
        log.warning('Failed to decrypt Firebase credentials: InvalidToken')
        return

    try:
        # Get notification service
        notification_service = get_notification_service(firebase_creds_json)

        # Process each news item for notifications
        sent_count = 0
        duplicate_count = 0
        for news in news_items:
            # Get the topics to send to
            topics = news.meta.get('push_notifications', [])
            if not topics:
                print(f'No topics configured for news item: {news.title}')
                continue

            print(
                f'Processing notification for news: {news.title} to '
                f'{len(topics)} topics'
            )

            for topic_id in topics:
                if isinstance(topic_id, str):
                    print(f'String entry: {topic_id}')
                else:
                    print('Invalid topic entry')
                    continue

                # Check if notification was already sent
                if PushNotification.was_notification_sent(
                    session, news.id, topic_id
                ):
                    log.info(
                        f"Skipping duplicate notification to topic "
                        f"'{topic_id}' for news '{news.title}'."
                    )
                    duplicate_count += 1
                    continue

                notification_title = news.title
                notification_body = news.lead or ''
                notification_data = {
                    'id': str(request.link(news)),
                    'title': news.title,
                    'lead': notification_body,
                }

                try:
                    # Create a "pending" notification record
                    notification = PushNotification(
                        news_id=news.id,
                        topic_id=topic_id,
                        sent_at=utcnow(),
                        response_data={'status': 'pending'},
                    )
                    session.add(notification)
                    session.flush()  # This will raise IntegrityError if record
                    # exists

                    # If we got here, we're the first process to try sending
                    # this notification
                    response = notification_service.send_notification(
                        topic=topic_id,
                        title=notification_title,
                        body=notification_body,
                        data=notification_data,
                    )

                    # Update the record with actual response data
                    notification.response_data = {
                        'message_id': response,
                        'timestamp': utcnow().isoformat(),
                        'status': 'sent',
                    }
                    session.flush()

                    sent_count += 1
                    log.debug(
                        f"Successfully sent notification to topic '{topic_id}'"
                        f" for news '{news.title}'. Response: {response}"
                    )

                except IntegrityError:
                    # Another process probably already created a record for
                    # this notification
                    session.rollback()
                    duplicate_count += 1
                    log.info(
                        f"Skipping duplicate notification to topic "
                        f"'{topic_id}' for news '{news.title}'. "
                    )

                except Exception as e:
                    # For other exceptions (like notification service failures)
                    error_details = str(e)
                    log.error(
                        f"Error sending notification to topic '{topic_id}' "
                        f"for news '{news.title}': {error_details}"
                    )

        if sent_count:
            print(f'Cron: Sent {sent_count} push notifications for news items')
        if duplicate_count:
            print(f'Cron: Skipped {duplicate_count} duplicate notifications')
        if not sent_count and not duplicate_count:
            print('No notifications were sent')

    except Exception as e:
        # Rollback in case of error
        session.rollback()
        print(traceback.format_exc())
        print(f'Error sending notifications: {e}')
