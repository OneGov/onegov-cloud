from datetime import datetime, timedelta
from onegov.core.templates import render_template
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultMailLayout
from onegov.ticket import Ticket, TicketCollection
from onegov.user import User, UserCollection
from sedate import replace_timezone, to_timezone
from sqlalchemy.orm import undefer


MON = 0
SAT = 5
SUN = 6


@OrgApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_daily_ticket_statistics(request):

    today = replace_timezone(datetime.utcnow(), 'UTC')
    today = to_timezone(today, 'Europe/Zurich')

    if today.weekday() in (SAT, SUN):
        return

    args = {}

    # get the current ticket count
    collection = TicketCollection(request.app.session())
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
            'org': request.app.org.name
        })
    )
    args['layout'] = DefaultMailLayout(object(), request)
    args['is_monday'] = today.weekday() == MON
    args['org'] = request.app.org.name

    # send one e-mail per user
    users = UserCollection(request.app.session()).query()
    users = users.filter(User.active == True)
    users = users.filter(User.role.in_(('admin', 'editor')))
    users = users.options(undefer('data'))
    users = users.all()

    for user in users:

        if user.data and not user.data.get('daily_ticket_statistics'):
            continue

        args['username'] = user.username
        content = render_template(
            'mail_daily_ticket_statistics.pt', request, args
        )

        request.app.send_email(
            subject=args['title'],
            receivers=(user.username, ),
            content=content
        )
