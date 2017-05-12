from functools import lru_cache
from onegov.activity import Attendee
from onegov.activity import Booking, BookingCollection, Occasion
from onegov.activity.matching import deferred_acceptance_from_database
from onegov.core.security import Secret
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.forms import MatchForm
from onegov.feriennet.layout import MatchCollectionLayout
from onegov.org.new_elements import Block
from onegov.org.new_elements import Confirm
from onegov.org.new_elements import Intercooler
from onegov.org.new_elements import Link
from onegov.user import User, UserCollection


@FeriennetApp.form(
    model=MatchCollection,
    form=MatchForm,
    template='matches.pt',
    permission=Secret)
def handle_matches(self, request, form):

    layout = MatchCollectionLayout(self, request)

    users = UserCollection(request.app.session()).query()
    users = users.with_entities(User.username, User.id)
    users = {u.username: u.id.hex for u in users}

    if form.submitted(request):
        assert self.period.active and not self.period.confirmed

        deferred_acceptance_from_database(
            session=request.app.session(),
            period_id=self.period_id,
            score_function=form.scoring(request.app.session()))

        self.period.scoring = form.scoring(request.app.session())

        if form.confirm_period:
            self.period.confirm()
            request.success(_("The matching was confirmed successfully"))
        else:
            request.success(_("The matching run executed successfully"))

    elif not request.POST:
        form.process_scoring(self.period.scoring)

    def activity_link(oid):
        return request.class_link(Occasion, {'id': oid})

    def occasion_links(oid):
        if self.period.finalized:
            yield Link(
                text=_("Signup Attendee"),
                traits=(
                    Block(_(
                        "The period has already been finalized. No new "
                        "attendees may be added."
                    ))
                )
            )
        else:
            yield Link(
                text=_("Signup Attendee"),
                url=request.return_here(
                    request.class_link(Occasion, {'id': oid}, 'anmelden')
                )
            )

    wishlist_phase = self.period.wishlist_phase
    booking_phase = self.period.booking_phase

    phase_title = wishlist_phase and _("Wishlist") or _("Bookings")

    @lru_cache(maxsize=128)
    def bookings_link(username):
        return request.class_link(
            BookingCollection, {
                'period_id': self.period.id,
                'username': username
            }
        )

    @lru_cache(maxsize=128)
    def user_link(username):
        return request.return_here(
            request.class_link(
                User, {'id': users[username]}
            )
        )

    @lru_cache(maxsize=128)
    def attendee_link(attendee_id):
        return request.return_here(
            request.class_link(
                Attendee, {'id': attendee_id}
            )
        )

    def record_links(record):
        yield Link(_("User"), user_link(record.attendee_username))
        yield Link(_("Attendee"), attendee_link(record.attendee_id))
        yield Link(phase_title, bookings_link(record.attendee_username))

        if wishlist_phase:
            yield Link(
                text=_("Remove Wish"),
                url=layout.csrf_protected_url(
                    request.class_link(Booking, {'id': record.booking_id})
                ),
                traits=(
                    Confirm(_(
                        "Do you really want to remove ${attendee}'s wish?",
                        mapping={
                            'attendee': record.attendee_name
                        }
                    ), yes=_("Remove Wish")),
                    Intercooler(
                        request_method='DELETE',
                        target='#{}'.format(record.booking_id)
                    )
                )
            )

        elif booking_phase and record.booking_state != 'accepted':
            yield Link(
                text=_("Remove Booking"),
                url=layout.csrf_protected_url(
                    request.class_link(Booking, {'id': record.booking_id})
                ),
                traits=(
                    Confirm(_(
                        "Do you really want to delete ${attendee}'s booking?",
                        mapping={
                            'attendee': record.attendee_name
                        }
                    ), yes=_("Remove Booking")),
                    Intercooler(
                        request_method='DELETE',
                        target='#{}'.format(record.booking_id)
                    )
                )
            )
        elif booking_phase and record.booking_state == 'accepted':
            yield Link(
                text=_("Cancel Booking"),
                url=layout.csrf_protected_url(
                    request.class_link(
                        Booking, {'id': record.booking_id}, 'absagen'
                    )
                ),
                traits=(
                    Confirm(_(
                        "Do you really want to cancel ${attendee}'s booking?",
                        mapping={
                            'attendee': record.attendee_name
                        }
                    ), _("This cannot be undone."), yes=_("Cancel Booking")),
                    Intercooler(
                        request_method='POST',
                    )
                )
            )

    filters = {}
    filters['states'] = tuple(
        Link(
            text=request.translate(text),
            active=state in self.states,
            url=request.link(self.for_filter(state=state))
        ) for text, state in (
            (_("Too many attendees"), 'overfull'),
            (_("Fully occupied"), 'full'),
            (_("Enough attendees"), 'operable'),
            (_("Not enough attendees"), 'unoperable'),
            (_("No attendees"), 'empty'),
            (_("Rescinded"), 'cancelled')
        )
    )

    return {
        'layout': layout,
        'title': _("Matches for ${title}", mapping={
            'title': self.period.title
        }),
        'occasions': self.occasions,
        'activity_link': activity_link,
        'happiness': '{}%'.format(round(self.happiness * 100)),
        'operability': '{}%'.format(round(self.operability * 100)),
        'period': self.period,
        'periods': request.app.periods,
        'form': form,
        'button_text': _("Run Matching"),
        'model': self,
        'filters': filters,
        'record_links': record_links,
        'occasion_links': occasion_links,
        'booking_link': lambda record, name=None: request.class_link(
            Booking, {'id': record.booking_id}, name
        )
    }


@FeriennetApp.view(
    model=MatchCollection,
    name='zuruecksetzen',
    permission=Secret,
    request_method="POST")
def reset_matching(self, request):
    assert self.period.active and not self.period.confirmed

    bookings = BookingCollection(request.app.session(), self.period_id)

    for booking in bookings.query().filter(Booking.state != 'cancelled'):
        booking.state = 'open'

    request.success(_("The period was successfully reset"))
