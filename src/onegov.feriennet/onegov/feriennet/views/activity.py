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
from onegov.org.elements import Link, ConfirmLink, DeleteLink
from onegov.org.mail import send_html_mail
from onegov.ticket import TicketCollection
from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from webob import exc


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

    taglinks = []

    if show_activities:
        taglinks = [
            Link(
                text=request.translate(_(tag)),
                active=tag in self.tags,
                url=request.link(self.for_filter(tag=tag))
            ) for tag in self.used_tags
        ]

        taglinks.extend(
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

        taglinks.extend(
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

        if request.is_organiser:
            periods = request.app.periods
        else:
            periods = None

        if periods:
            taglinks.extend(
                Link(
                    text=period.title,
                    active=period.id in self.period_ids,
                    url=request.link(self.for_filter(period_id=period.id))
                ) for period in periods if period
            )

        if request.is_organiser:

            taglinks.append(
                Link(
                    text=request.translate(_("Own")),
                    active=request.current_username in self.owners,
                    url=request.link(
                        self.for_filter(owner=request.current_username))
                )
            )

            taglinks.extend(
                Link(
                    text=request.translate(_(state.capitalize())),
                    active=state in self.states,
                    url=request.link(self.for_filter(state=state))
                ) for state in ACTIVITY_STATES
            )

        taglinks.sort(key=lambda link: link.text)

    def get_period_bound_occasions(activity):
        if not active_period:
            return []

        return [
            o for o in activity.occasions
            if o.period_id == active_period.id
        ]

    def get_ages(a):
        return tuple(o.age for o in get_period_bound_occasions(a))

    def get_occasion_count(a):
        return len(get_period_bound_occasions(a))

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
        'layout': VacationActivityCollectionLayout(self, request),
        'title': _("Activities"),
        'taglinks': taglinks,
        'period': active_period,
        'get_ages': get_ages,
        'get_min_cost': get_min_cost,
        'get_occasion_count': get_occasion_count,
    }


@FeriennetApp.html(
    model=VacationActivity,
    template='activity.pt',
    permission=Public)
def view_activity(self, request):

    session = request.app.session()
    ticket = TicketCollection(session).by_handler_id(self.id.hex)
    layout = VacationActivityLayout(self, request)

    occasion_links = (
        lambda o: Link(text=_("Edit"), url=request.link(o, name='bearbeiten')),
        lambda o: DeleteLink(
            text=_("Delete"), url=layout.csrf_protected_url(request.link(o)),
            confirm=_('Do you really want to delete "${title}"?', mapping={
                'title': layout.format_datetime_range(
                    o.dates[0].localized_start,
                    o.dates[0].localized_end
                ),
            }),
            redirect_after=request.link(self),
            yes_button_text=_("Delete Occasion"),
            classes=('confirm', )
        )
    )

    occasion_ids = {o.id for o in self.occasions}
    occasion_ids_with_bookings = occasion_ids and {
        b.occasion_id for b in session.query(Booking)
        .with_entities(Booking.occasion_id)
        .filter(Booking.occasion_id.in_(occasion_ids))
    } or set()

    def occasion_links(o):
        yield Link(text=_("Edit"), url=request.link(o, name='bearbeiten'))

        title = layout.format_datetime_range(
            o.dates[0].localized_start,
            o.dates[0].localized_end
        )

        if o.cancelled and not o.period.finalized:
            yield ConfirmLink(
                text=_("Reinstate"),
                url=layout.csrf_protected_url(
                    request.link(o, name='reinstate')
                ),
                confirm=_((
                    'Do you really want to reinstate "${title}"?'
                ), mapping={
                    'title': title
                }),
                extra_information=_("Previous attendees need to re-apply"),
                redirect_after=request.link(self),
                yes_button_text=_("Reinstate Occasion"),
                classes=('confirm', )
            )
        elif o.id in occasion_ids_with_bookings and not o.period.finalized:
            yield ConfirmLink(
                text=_("Rescind"),
                url=layout.csrf_protected_url(request.link(o, name='cancel')),
                confirm=_((
                    'Do you really want to rescind "${title}"?'
                ), mapping={
                    'title': title
                }),
                extra_information=_((
                    "${count} already accepted bookings will be cancelled"
                ), mapping={
                    'count': o.attendee_count
                }),
                redirect_after=request.link(self),
                yes_button_text=_("Rescind Occasion"),
                classes=('confirm', )
            )
        elif o.id not in occasion_ids_with_bookings:
            yield DeleteLink(
                text=_("Delete"),
                url=layout.csrf_protected_url(request.link(o)),
                confirm=_('Do you really want to delete "${title}"?', mapping={
                    'title': title
                }),
                extra_information=_((
                    "There are no accepted bookings associated with this "
                    "occasion, though there might be cancelled/blocked "
                    "bookings which will be deleted."
                )),
                redirect_after=request.link(self),
                yes_button_text=_("Delete Occasion"),
                classes=('confirm', )
            )

    def age_bracket(age):
        if 13 <= age.lower:
            return 'teenager'
        elif (age.upper - 1) <= 7:
            return 'young'
        else:
            return 'general'

    def show_enroll(occasion):
        if self.state != 'accepted':
            return False

        if not occasion.active:
            return False

        if occasion.cancelled:
            return False

        if occasion.full:
            return False

        if occasion.period.finalized:
            return False

        if occasion.period.phase not in ('wishlist', 'booking', 'execution'):
            return False

        return True

    return {
        'layout': layout,
        'title': self.title,
        'activity': self,
        'ticket': ticket,
        'show_enroll': show_enroll,
        'occasion_links': occasion_links,
        'occasions_by_period': occasions_by_period(
            session=session,
            activity=self,
            active_only=not request.is_organiser
        ),
        'age_bracket': age_bracket,
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
    name='ablehnen',
    request_method='POST')
def reject_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='deny',
        template='mail_activity_rejected.pt',
        subject=_("Your activity has been rejected")
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
