import sedate

from datetime import date
from itertools import groupby
from onegov.activity import Booking
from onegov.activity import Occasion
from onegov.activity import OccasionCollection
from onegov.activity import Period
from onegov.activity.models import ACTIVITY_STATES, DAYS
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.forms import VacationActivityForm
from onegov.feriennet.layout import VacationActivityCollectionLayout
from onegov.feriennet.layout import VacationActivityFormLayout
from onegov.feriennet.layout import VacationActivityLayout
from onegov.feriennet.models import VacationActivity
from onegov.org.mail import send_html_mail
from onegov.org.new_elements import Link, Confirm, Intercooler
from onegov.ticket import TicketCollection
from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from webob import exc


ACTIVITY_STATE_TRANSLATIONS = {
    'preview': _("Preview"),
    'proposed': _("Proposed"),
    'accepted': _("Published"),  # users like the term 'Published' better
    'archived': _("Archived")
}


WEEKDAYS = (
    _("Mo"),
    _("Tu"),
    _("We"),
    _("Th"),
    _("Fr"),
    _("Sa"),
    _("Su")
)


def get_activity_form_class(model, request):
    if isinstance(model, VacationActivityCollection):
        model = VacationActivity()

    return model.with_content_extensions(VacationActivityForm, request)


def occasions_by_period(session, activity, active_only):
    query = OccasionCollection(session).query()
    query = query.filter(Occasion.activity_id == activity.id)

    if active_only:
        query = query.filter(Occasion.active == True)

    query = query.join(Occasion.period)
    query = query.options(contains_eager(Occasion.period))

    query = query.order_by(
        desc(Period.active),
        Period.execution_start,
        Occasion.order)

    return tuple(
        (title, tuple(occasions)) for title, occasions in
        groupby(query.all(), key=lambda o: o.period.title)
    )


@FeriennetApp.html(
    model=VacationActivityCollection,
    template='activities.pt',
    permission=Public)
def view_activities(self, request):
    active_period = request.app.active_period
    show_activities = bool(active_period or request.is_organiser)
    layout = VacationActivityCollectionLayout(self, request)

    filters = {}

    if show_activities:
        filters['tags'] = [
            Link(
                text=request.translate(_(tag)),
                active=tag in self.tags,
                url=request.link(self.for_filter(tag=tag))
            ) for tag in self.used_tags
        ]
        filters['tags'].sort(key=lambda l: l.text)

        filters['durations'] = tuple(
            Link(
                text=request.translate(text),
                active=duration in self.durations,
                url=request.link(self.for_filter(duration=duration))
            ) for text, duration in (
                (_("Half day"), DAYS.half),
                (_("Full day"), DAYS.full),
                (_("Multiple days"), DAYS.many),
            )
        )

        filters['ages'] = tuple(
            Link(
                text=request.translate(text),
                active=self.contains_age_range(age_range),
                url=request.link(self.for_filter(age_range=age_range))
            ) for text, age_range in (
                (_(" 3 - 6 years"), (3, 6)),
                (_(" 7 - 10 years"), (7, 10)),
                (_("11 - 13 years"), (11, 13)),
                (_("14 - 17 years"), (14, 17))
            )
        )

        if active_period:
            filters['weeks'] = tuple(
                Link(
                    text='{} - {}'.format(
                        layout.format_date(daterange[0], 'date'),
                        layout.format_date(daterange[1], 'date')
                    ),
                    active=daterange in self.dateranges,
                    url=request.link(self.for_filter(daterange=daterange))
                ) for nth, daterange in enumerate(
                    sedate.weekrange(
                        active_period.execution_start,
                        active_period.execution_end
                    ),
                    start=1
                )
            )

        filters['weekdays'] = tuple(
            Link(
                text=WEEKDAYS[weekday],
                active=weekday in self.weekdays,
                url=request.link(self.for_filter(weekday=weekday))
            ) for weekday in range(0, 7)
        )

        if request.is_organiser:
            if request.app.periods:
                filters['periods'] = [
                    Link(
                        text=period.title,
                        active=period.id in self.period_ids,
                        url=request.link(self.for_filter(period_id=period.id))
                    ) for period in request.app.periods if period
                ]
                filters['periods'].sort(key=lambda l: l.text)

            filters['own'] = (
                Link(
                    text=request.translate(_("Own")),
                    active=request.current_username in self.owners,
                    url=request.link(
                        self.for_filter(owner=request.current_username)
                    )
                ),
            )

            filters['states'] = tuple(
                Link(
                    text=ACTIVITY_STATE_TRANSLATIONS[state],
                    active=state in self.states,
                    url=request.link(self.for_filter(state=state))
                ) for state in ACTIVITY_STATES
            )

    def get_period_bound_occasions(activity):
        if not active_period:
            return []

        return [
            o for o in activity.occasions
            if o.period_id == active_period.id
        ]

    def get_ages(a):
        return tuple(o.age for o in get_period_bound_occasions(a))

    def get_available_spots(a):
        if not active_period:
            return 0

        if not active_period.confirmed:
            return sum(
                o.max_spots for o in get_period_bound_occasions(a)
            )
        else:
            return sum(
                o.available_spots for o in get_period_bound_occasions(a)
            )

    def get_min_cost(a):
        occasions = get_period_bound_occasions(a)

        if not occasions:
            return None

        if active_period.all_inclusive:
            extra = 0
        else:
            extra = active_period.booking_cost or 0

        return min((o.cost or 0) + extra for o in occasions)

    return {
        'activities': self.batch if show_activities else None,
        'layout': layout,
        'title': _("Activities"),
        'filters': filters,
        'period': active_period,
        'get_ages': get_ages,
        'get_min_cost': get_min_cost,
        'get_available_spots': get_available_spots,
    }


@FeriennetApp.html(
    model=VacationActivity,
    template='activity.pt',
    permission=Public)
def view_activity(self, request):

    session = request.app.session()
    layout = VacationActivityLayout(self, request)

    occasion_ids = {o.id for o in self.occasions}
    occasion_ids_with_bookings = occasion_ids and {
        b.occasion_id for b in session.query(Booking)
        .with_entities(Booking.occasion_id)
        .filter(Booking.occasion_id.in_(occasion_ids))
    } or set()

    def occasion_links(o):
        yield Link(text=_("Edit"), url=request.link(o, name='bearbeiten'))
        yield Link(text=_("Clone"), url=request.link(o, name='duplizieren'))

        title = layout.format_datetime_range(
            o.dates[0].localized_start,
            o.dates[0].localized_end
        )

        if o.cancelled and not o.period.finalized:
            yield Link(
                text=_("Reinstate"),
                url=layout.csrf_protected_url(
                    request.link(o, name='reinstate')
                ),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to reinstate "${title}"?',
                            mapping={'title': title}
                        ),
                        _("Previous attendees need to re-apply"),
                        _("Reinstate Occasion"),
                    ),
                    Intercooler(
                        request_method="POST",
                        redirect_after=request.link(self)
                    )
                )
            )
        elif o.id in occasion_ids_with_bookings and not o.period.finalized:
            yield Link(
                text=_("Rescind"),
                url=layout.csrf_protected_url(request.link(o, name='cancel')),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to rescind "${title}"?',
                            mapping={'title': title}
                        ),
                        _(
                            "${count} already accepted bookings will "
                            "be cancelled", mapping={'count': o.attendee_count}
                        ),
                        _(
                            "Rescind Occasion"
                        )
                    ),
                    Intercooler(
                        request_method="POST",
                        redirect_after=request.link(self)
                    )
                )
            )
        elif o.id not in occasion_ids_with_bookings:
            yield Link(
                text=_("Delete"),
                url=layout.csrf_protected_url(request.link(o)),
                traits=(
                    Confirm(
                        _('Do you really want to delete "${title}"?', mapping={
                            'title': title
                        }),
                        _((
                            "There are no accepted bookings associated with "
                            "this occasion, though there might be "
                            "cancelled/blocked bookings which will be deleted."
                        )),
                        _("Delete Occasion")
                    ),
                    Intercooler(
                        request_method="DELETE",
                        redirect_after=request.link(self)
                    )
                )
            )

    def show_enroll(occasion):
        if self.state != 'accepted':
            return False

        if not occasion.active:
            return False

        if occasion.cancelled:
            return False

        if occasion.full and occasion.period.phase != 'wishlist':
            return False

        if occasion.period.finalized:
            return False

        if occasion.period.phase not in ('wishlist', 'booking', 'execution'):
            return False

        if not request.is_admin and occasion.is_past_deadline(date.today()):
            return False

        if occasion.period.wishlist_phase and\
           occasion.period.is_prebooking_in_past:
            return False

        return True

    return {
        'layout': layout,
        'title': self.title,
        'activity': self,
        'show_enroll': show_enroll,
        'occasion_links': occasion_links,
        'occasions_by_period': occasions_by_period(
            session=session,
            activity=self,
            active_only=not request.is_organiser
        ),
    }


@FeriennetApp.form(
    model=VacationActivityCollection,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='neu')
def new_activity(self, request, form):

    if form.submitted(request):
        activity = self.add(
            title=form.title.data,
            username=request.current_username)

        form.populate_obj(activity)

        return request.redirect(request.link(activity))

    return {
        'layout': VacationActivityFormLayout(self, request, _("New Activity")),
        'title': _("New Activity"),
        'form': form
    }


@FeriennetApp.form(
    model=VacationActivity,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='bearbeiten')
def edit_activity(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))

        return request.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': VacationActivityFormLayout(self, request, self.title),
        'title': self.title,
        'form': form
    }


@FeriennetApp.view(
    model=VacationActivity,
    permission=Private,
    request_method='DELETE')
def discard_activity(self, request):

    request.assert_valid_csrf_token()

    # discard really is like delete, but activites can only be deleted
    # before they are submitted for publication, so 'discard' is a more
    # accurate description
    if self.state != 'preview':
        raise exc.HTTPMethodNotAllowed()

    activities = VacationActivityCollection(
        request.app.session(),
        request.identity
    )
    activities.delete(self)

    request.success(_("The activity was discarded"))


@FeriennetApp.view(
    model=VacationActivity,
    permission=Private,
    name='beantragen',
    request_method='POST')
def propose_activity(self, request):

    session = request.app.session()

    with session.no_autoflush:
        self.propose()
        ticket = TicketCollection(session).open_ticket(
            handler_code='FER', handler_id=self.id.hex
        )

    if request.is_organiser_only or request.current_username != self.username:
        send_html_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("A ticket has been opened"),
            receivers=(self.username, ),
            content={
                'model': ticket
            }
        )

    request.success(_("Thank you for your proposal!"))

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(ticket, 'status'))

    # do not redirect here, intercooler doesn't deal well with that...
    return


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='annehmen',
    request_method='POST')
def accept_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='accept',
        template='mail_activity_accepted.pt',
        subject=_("Your activity has been published")
    )


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='archivieren',
    request_method='POST')
def archive_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='archive',
        template='mail_activity_archived.pt',
        subject=_("Your activity has been archived")
    )


def administer_activity(model, request, action, template, subject):
    session = request.app.session()
    ticket = TicketCollection(session).by_handler_id(model.id.hex)

    # execute state change
    getattr(model, action)()

    if request.current_username != model.username:
        send_html_mail(
            request=request,
            template=template,
            subject=subject,
            receivers=(model.username, ),
            content={
                'model': model,
                'ticket': ticket
            }
        )

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(ticket))

    # do not redirect here, intercooler doesn't deal well with that...
    return
