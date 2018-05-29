from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import groupby
from onegov.core.templates import render_template
from onegov.form import FormSubmission, parse_form
from onegov.newsletter import Newsletter, NewsletterCollection
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultMailLayout
from onegov.org.models import ResourceRecipient, ResourceRecipientCollection
from onegov.org.views.newsletter import send_newsletter
from onegov.reservation import Reservation, Resource, ResourceCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.user import User, UserCollection
from sedate import replace_timezone, to_timezone, utcnow, align_date_to_day
from sqlalchemy import and_
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
def send_scheduled_newsletter(request):
    newsletters = NewsletterCollection(request.session).query().filter(and_(
        Newsletter.scheduled != None,
        Newsletter.scheduled <= (utcnow() + timedelta(seconds=60)),
    ))

    for newsletter in newsletters:
        send_newsletter(request, newsletter, newsletter.open_recipients)
        newsletter.scheduled = None


@OrgApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_daily_ticket_statistics(request):

    today = replace_timezone(datetime.utcnow(), 'UTC')
    today = to_timezone(today, 'Europe/Zurich')

    if today.weekday() in (SAT, SUN):
        return

    args = {}
    app = request.app

    # get the current ticket count
    collection = TicketCollection(app.session())
    count = collection.get_count()
    args['currently_open'] = count.open
    args['currently_pending'] = count.pending
    args['currently_closed'] = count.closed

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

    # render the email
    args['title'] = request.translate(
        _("${org} OneGov Cloud Status", mapping={
            'org': app.org.title
        })
    )
    args['layout'] = DefaultMailLayout(object(), request)
    args['is_monday'] = today.weekday() == MON
    args['org'] = app.org.title

    # send one e-mail per user
    users = UserCollection(app.session()).query()
    users = users.filter(User.active == True)
    users = users.filter(User.role.in_(app.settings.org.status_mail_roles))
    users = users.options(undefer('data'))
    users = users.all()

    for user in users:

        if user.data and not user.data.get('daily_ticket_statistics'):
            continue

        args['username'] = user.username
        content = render_template(
            'mail_daily_ticket_statistics.pt', request, args
        )

        app.send_transactional_email(
            subject=args['title'],
            receivers=(user.username, ),
            content=content
        )


@OrgApp.cronjob(hour=6, minute=5, timezone='Europe/Zurich')
def send_daily_resource_usage_overview(request):
    today = to_timezone(utcnow(), 'Europe/Zurich')
    weekday = WEEKDAYS[today.weekday()]

    # get all recipients which require an e-mail today
    q = ResourceRecipientCollection(request.session).query()
    q = q.filter(ResourceRecipient.medium == 'email')
    q = q.order_by(ResourceRecipient.address)
    q = q.with_entities(
        ResourceRecipient.address,
        ResourceRecipient.content
    )

    recipients = tuple(
        (r.address, r.content['resources'])
        for r in q if weekday in r.content['send_on']
    )

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

    forms = {
        resource.id.hex: parse_form(resource.definition)
        for resource in all_resources if resource.definition
    }

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
        'forms': forms
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
