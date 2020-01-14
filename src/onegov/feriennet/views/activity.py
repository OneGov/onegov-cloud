import sedate

from datetime import date, timedelta
from itertools import groupby
from onegov.activity import Booking
from onegov.activity import Occasion
from onegov.activity import OccasionCollection
from onegov.activity import Period
from onegov.activity.models import ACTIVITY_STATES, DAYS
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.core.utils import normalize_for_url
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.forms import VacationActivityForm
from onegov.feriennet.layout import VacationActivityCollectionLayout
from onegov.feriennet.layout import VacationActivityFormLayout
from onegov.feriennet.layout import VacationActivityLayout
from onegov.feriennet.models import ActivityMessage
from onegov.feriennet.models import VacationActivity
from onegov.feriennet.models import VolunteerCart
from onegov.feriennet.models import VolunteerCartAction
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.ticket import TicketCollection
from purl import URL
from sedate import dtrange, overlaps
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


def occasions_by_period(session, activity, show_inactive, show_archived):
    query = OccasionCollection(session).query()
    query = query.filter(Occasion.activity_id == activity.id)

    query = query.join(Occasion.period)
    query = query.options(contains_eager(Occasion.period))

    if not show_inactive:
        query = query.filter(Period.active == True)

    if not show_archived:
        query = query.filter(Period.archived == False)

    query = query.order_by(
        desc(Period.active),
        Period.execution_start,
        Occasion.order)

    return tuple(
        (title, tuple(occasions)) for title, occasions in
        groupby(query.all(), key=lambda o: o.period.title)
    )


def filter_link(text, active, url, rounded=False):
    return Link(text=text, active=active, url=url, rounded=rounded, attrs={
        'ic-get-from': url
    })


def filter_timelines(activity, request):
    links = [
        filter_link(
            text=request.translate(_("Elapsed")),
            active='past' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='past'))
        ),
        filter_link(
            text=request.translate(_("Now")),
            active='now' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='now'))
        ),
        filter_link(
            text=request.translate(_("Scheduled")),
            active='future' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='future'))
        ),
    ]

    if request.is_organiser:
        links.insert(0, filter_link(
            text=request.translate(_("Without")),
            active='undated' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='undated'))
        ))

    return links


def filter_tags(activity, request):
    links = [
        filter_link(
            text=request.translate(_(tag)),
            active=tag in activity.filter.tags,
            url=request.link(activity.for_filter(tag=tag)),
        ) for tag in activity.used_tags
    ]
    links.sort(key=lambda l: l.text)

    return links


def filter_durations(activity, request):
    return tuple(
        filter_link(
            text=request.translate(text),
            active=duration in activity.filter.durations,
            url=request.link(activity.for_filter(duration=duration))
        ) for text, duration in (
            (_("Half day"), DAYS.half),
            (_("Full day"), DAYS.full),
            (_("Multiple days"), DAYS.many),
        )
    )


def filter_ages(activity, request):
    ages = activity.available_ages()

    if not ages:
        return

    def age_filters():
        for age in range(*ages):
            if age < 16:
                yield str(age), (age, age)
            else:
                yield "16+", (16, 99)
                break

    return tuple(
        filter_link(
            text=request.translate(text),
            active=activity.filter.contains_age_range(age_range),
            url=request.link(activity.for_filter(age_range=age_range))
        ) for text, age_range in age_filters()
    )


def filter_price_range(activity, request):
    return tuple(
        filter_link(
            text=request.translate(text),
            active=activity.filter.contains_price_range(price_range),
            url=request.link(activity.for_filter(price_range=price_range))
        ) for text, price_range in (
            (_("Free of Charge"), (0, 0)),
            (_("Up to 25 CHF"), (1, 25)),
            (_("Up to 50 CHF"), (26, 50)),
            (_("Up to 100 CHF"), (51, 100)),
            (_("More than 100 CHF"), (101, 100000)),
        )
    )


def filter_weeks(activity, request):
    layout = VacationActivityCollectionLayout(activity, request)

    return tuple(
        filter_link(
            text='{} - {}'.format(
                layout.format_date(daterange[0], 'date'),
                layout.format_date(daterange[1], 'date')
            ),
            active=daterange in activity.filter.dateranges,
            url=request.link(activity.for_filter(daterange=daterange))
        ) for nth, daterange in enumerate(
            activity.available_weeks(request.app.active_period),
            start=1
        )
    )


def filter_weekdays(activity, request):
    return tuple(
        filter_link(
            text=WEEKDAYS[weekday],
            active=weekday in activity.filter.weekdays,
            url=request.link(activity.for_filter(weekday=weekday))
        ) for weekday in range(0, 7)
    )


def filter_available(activity, request):
    return tuple(
        filter_link(
            text=request.translate(text),
            active=available in activity.filter.available,
            url=request.link(activity.for_filter(available=available))
        ) for text, available in (
            (_("None"), 'none'),
            (_("Few"), 'few'),
            (_("Many"), 'many'),
        )
    )


def filter_municipalities(activity, request):
    links = [
        filter_link(
            text=municipality,
            active=municipality in activity.filter.municipalities,
            url=request.link(activity.for_filter(municipality=municipality))
        ) for municipality in activity.used_municipalities
    ]

    links.sort(key=lambda l: normalize_for_url(l.text))

    return links


def filter_periods(activity, request):
    links = [
        filter_link(
            text=period.title,
            active=period.id in activity.filter.period_ids,
            url=request.link(activity.for_filter(period_id=period.id))
        ) for period in request.app.periods if period
    ]
    links.sort(key=lambda l: l.text)

    return links


def filter_own(activity, request):
    return (
        filter_link(
            text=request.translate(_("Own")),
            active=request.current_username in activity.filter.owners,
            url=request.link(
                activity.for_filter(owner=request.current_username)
            )
        ),
    )


def filter_states(activity, request):
    return tuple(
        filter_link(
            text=ACTIVITY_STATE_TRANSLATIONS[state],
            active=state in activity.filter.states,
            url=request.link(activity.for_filter(state=state))
        ) for state in ACTIVITY_STATES
    )


def period_bound_occasions(activity, request):
    active_period = request.app.active_period

    if not active_period:
        return []

    return [o for o in activity.occasions if o.period_id == active_period.id]


def activity_ages(activity, request):
    return tuple(o.age for o in period_bound_occasions(activity, request))


def activity_spots(activity, request):
    if not request.app.active_period:
        return 0

    if not request.app.active_period.confirmed:
        return sum(o.max_spots for o in period_bound_occasions(
            activity, request))

    return sum(o.available_spots for o in period_bound_occasions(
        activity, request))


def activity_min_cost(activity, request):
    occasions = period_bound_occasions(activity, request)

    if not occasions:
        return None

    return min(o.total_cost for o in occasions)


def is_filtered(filters):
    for links in filters.values():
        for link in links:
            if link.active:
                return True

    return False


def adjust_filter_path(filters, suffix):

    for links in filters.values():
        for link in links:
            link.attrs['href'] = link.attrs['ic-get-from'] = \
                URL(link.attrs['href']).add_path_segment(suffix).as_string()


def exclude_filtered_dates(activities, dates):
    result = []

    if not activities.filter.dateranges:
        result = dates
    else:
        for dt in dates:
            for s, e in activities.filter.dateranges:
                if overlaps(dt.start.date(), dt.end.date(), s, e):
                    result.append(dt)
                    break

    dates = result
    result = []

    if not activities.filter.weekdays:
        result = dates
    else:
        for dt in dates:
            for day in dtrange(dt.start, dt.end):
                if day.weekday() not in activities.filter.weekdays:
                    break
            else:
                result.append(dt)

    return result


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
        filters['timelines'] = filter_timelines(self, request)
        filters['tags'] = filter_tags(self, request)
        filters['durations'] = filter_durations(self, request)
        filters['ages'] = filter_ages(self, request)
        filters['price_range'] = filter_price_range(self, request)

        if active_period:
            filters['weeks'] = filter_weeks(self, request)

        filters['weekdays'] = filter_weekdays(self, request)
        filters['available'] = filter_available(self, request)
        filters['municipalities'] = filter_municipalities(self, request)

        if request.is_organiser:
            if request.app.periods:
                filters['periods'] = filter_periods(self, request)

            filters['own'] = filter_own(self, request)
            filters['states'] = filter_states(self, request)

    filters = {k: v for k, v in filters.items() if v}

    return {
        'activities': self.batch if show_activities else None,
        'layout': layout,
        'title': _("Activities"),
        'filters': filters,
        'filtered': is_filtered(filters),
        'period': active_period,
        'activity_ages': activity_ages,
        'activity_min_cost': activity_min_cost,
        'activity_spots': activity_spots,
        'current_location': request.link(
            self.by_page_range((0, self.pages[-1])))
    }


@FeriennetApp.html(
    model=VacationActivityCollection,
    template='activities-for-volunteers.pt',
    permission=Public,
    name='volunteer')
def view_activities_for_volunteers(self, request):
    if not request.app.show_volunteers(request):
        raise exc.HTTPForbidden()

    active_period = request.app.active_period
    show_activities = bool(active_period or request.is_organiser)

    layout = VacationActivityCollectionLayout(self, request)
    layout.breadcrumbs[-1].text = _("Join as a Volunteer")

    # always limit to activities seeking volunteers
    self.filter.volunteers = {True}

    # include javascript part
    request.include('volunteer-cart')

    filters = {}

    if show_activities:
        filters['tags'] = filter_tags(self, request)
        filters['durations'] = filter_durations(self, request)

        if active_period:
            filters['weeks'] = filter_weeks(self, request)

        filters['weekdays'] = filter_weekdays(self, request)
        filters['municipalities'] = filter_municipalities(self, request)

    filters = {k: v for k, v in filters.items() if v}
    adjust_filter_path(filters, suffix='volunteer')

    return {
        'activities': self.batch if show_activities else None,
        'layout': layout,
        'title': _("Join as a Volunteer"),
        'filters': filters,
        'filtered': is_filtered(filters),
        'period': active_period,
        'activity_ages': activity_ages,
        'activity_min_cost': activity_min_cost,
        'activity_spots': activity_spots,
        'exclude_filtered_dates': exclude_filtered_dates,
        'cart_url': request.class_link(VolunteerCart),
        'cart_submit_url': request.class_link(VolunteerCart, name='submit'),
        'cart_action_url': request.class_link(VolunteerCartAction, {
            'action': 'action',
            'target': 'target',
        }),
        'current_location': request.link(
            self.by_page_range((0, self.pages[-1])), name='volunteer')
    }


@FeriennetApp.html(
    model=VacationActivity,
    template='activity.pt',
    permission=Public)
def view_activity(self, request):

    session = request.session
    layout = VacationActivityLayout(self, request)

    occasion_ids = {o.id for o in self.occasions}
    occasion_ids_with_bookings = occasion_ids and {
        b.occasion_id for b in session.query(Booking)
        .with_entities(Booking.occasion_id)
        .filter(Booking.occasion_id.in_(occasion_ids))
    } or set()

    def occasion_links(o):

        if not o.period.archived and (o.period.active or request.is_admin):
            yield Link(text=_("Edit"), url=request.link(o, name='edit'))

        yield Link(text=_("Clone"), url=request.link(o, name='clone'))

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
                        _("Cancel")
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
                        ),
                        _(
                            "Cancel"
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
                        _("Delete Occasion"),
                        _("Cancel")
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

        if not occasion.period.active:
            return False

        if occasion.cancelled:
            return False

        if occasion.full and occasion.period.phase != 'wishlist':
            return False

        # the rest of the restrictions only apply to non-admins
        if request.is_admin:
            return True

        if occasion.period.finalized and not occasion.period.book_finalized:
            return False

        if occasion.period.finalized and occasion.period.book_finalized:
            acceptable_phases = ('wishlist', 'booking', 'execution', 'payment')
        else:
            acceptable_phases = ('wishlist', 'booking', 'execution')

        if occasion.period.phase not in acceptable_phases:
            return False

        if occasion.is_past_deadline(date.today()):
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
            show_inactive=request.is_organiser,
            show_archived=request.is_admin or (
                request.is_organiser
                and self.username == request.current_username
            )
        ),
    }


@FeriennetApp.form(
    model=VacationActivityCollection,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='new')
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
    name='edit')
def edit_activity(self, request, form):

    if form.submitted(request):
        old_username = self.username
        form.populate_obj(self)
        new_username = self.username

        if old_username != new_username:

            # if there is already a ticket..
            ticket = relevant_ticket(self, request)

            if ticket:

                # ..note the change
                ActivityMessage.create(ticket, request, 'reassign', {
                    'old_username': old_username,
                    'new_username': new_username,
                })

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
        request.session,
        request.identity
    )
    activities.delete(self)

    request.success(_("The activity was discarded"))


@FeriennetApp.view(
    model=VacationActivity,
    permission=Private,
    name='propose',
    request_method='POST')
def propose_activity(self, request):
    assert request.app.active_period, "An active period is required"

    # if the latest request has been done in the last minute, this is a
    # duplicate and should be ignored
    latest = self.latest_request

    if latest and (sedate.utcnow() - timedelta(seconds=60)) < latest.created:
        return

    session = request.session

    with session.no_autoflush:
        self.propose()

        publication_request = self.create_publication_request(
            request.app.active_period)

        ticket = TicketCollection(session).open_ticket(
            handler_code='FER', handler_id=publication_request.id.hex
        )
        TicketMessage.create(ticket, request, 'opened')

    send_ticket_mail(
        request=request,
        template='mail_ticket_opened.pt',
        subject=_("Your ticket has been opened"),
        receivers=(self.username, ),
        ticket=ticket,
        force=(
            request.is_organiser_only
            or request.current_username != self.username
        )
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
    name='accept',
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
    name='archive',
    request_method='POST')
def archive_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='archive',
        template='mail_activity_archived.pt',
        subject=_("Your activity has been archived")
    )


@FeriennetApp.view(
    model=VacationActivity,
    permission=Personal,
    name='offer-again',
    request_method='POST')
def offer_activity_again(self, request):
    assert self.state in ('archived', 'preview')

    if self.state == 'archived':
        self.state = 'preview'

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(self, 'edit'))


def relevant_ticket(activity, request):
    pr = activity.request_by_period(request.app.active_period) \
        or activity.latest_request

    if pr:
        return TicketCollection(request.session).by_handler_id(pr.id.hex)


def administer_activity(model, request, action, template, subject):
    ticket = relevant_ticket(model, request)

    if not ticket:
        raise RuntimeError(
            f"No ticket found for {model.name}, when performing {action}")

    # execute state change
    getattr(model, action)()

    send_ticket_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=(model.username, ),
        ticket=ticket,
        content={
            'model': model,
            'ticket': ticket
        }
    )

    ActivityMessage.create(ticket, request, action)

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(ticket))

    # do not redirect here, intercooler doesn't deal well with that...
    return
