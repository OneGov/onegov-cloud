from __future__ import annotations

import hashlib

from decimal import Decimal
from onegov.activity.models import Activity, Attendee, Booking, Occasion
from onegov.user import User
from sqlalchemy import func


from typing import Any, Generic, Self, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.activity.matching.interfaces import MatchableBooking
    from sqlalchemy.orm import Session
    BookingT = TypeVar(
        'BookingT',
        bound='Booking | MatchableBooking',
        default=Any
    )
else:
    BookingT = TypeVar('BookingT', bound='Booking | MatchableBooking')


class Scoring(Generic[BookingT]):
    """ Provides scoring based on a number of criteria.

    A criteria is a callable which takes a booking and returns a score.
    The final score is the sum of all criteria scores.

    """

    criteria: list[Callable[[BookingT], float]]

    def __init__(
        self,
        criteria: list[Callable[[BookingT], float]] | None = None
    ) -> None:
        self.criteria = criteria or [PreferMotivated()]

    def __call__(self, booking: BookingT) -> Decimal:
        return Decimal(sum(criterium(booking) for criterium in self.criteria))

    # NOTE: Some of the preference function are not compatible with our
    #       minimal interface, so this only works with real bookings.
    @classmethod
    def from_settings(
        cls,
        settings: dict[str, Any],
        session: Session
    ) -> Self:

        scoring = cls()

        # always prefer groups
        scoring.criteria.append(PreferGroups.from_session(session))  # type: ignore[arg-type]

        if settings.get('prefer_in_age_bracket'):
            scoring.criteria.append(
                PreferInAgeBracket.from_session(session))  # type: ignore[arg-type]

        if settings.get('prefer_organiser'):
            scoring.criteria.append(
                PreferOrganiserChildren.from_session(session))  # type: ignore[arg-type]

        if settings.get('prefer_admins'):
            scoring.criteria.append(
                PreferAdminChildren.from_session(session))  # type: ignore[arg-type]

        return scoring

    @property
    def settings(self) -> dict[str, Any]:
        classes = {c.__class__ for c in self.criteria}
        settings = {}

        if PreferInAgeBracket in classes:
            settings['prefer_in_age_bracket'] = True

        if PreferOrganiserChildren in classes:
            settings['prefer_organiser'] = True

        if PreferAdminChildren in classes:
            settings['prefer_admins'] = True

        return settings


class PreferMotivated:
    """ Scores "motivated" bookings higher. A motivated booking is simply a
    booking with a higher priority (an attendee would favor a booking he's
    excited about.)

    """

    @classmethod
    def from_session(cls, session: Session) -> Self:
        return cls()

    def __call__(self, booking: Booking | MatchableBooking) -> int:
        return booking.priority


class PreferInAgeBracket:
    """ Scores bookings whose attendees fall into the age-bracket of the
    occasion higher.

    If the attendee falls into the age-bracket, the score is 1.0. Each year
    difference results in a penalty of 0.1, until 0.0 is reached.

    """

    def __init__(
        self,
        get_age_range: Callable[[Booking], tuple[int, int]],
        get_attendee_age: Callable[[Booking], int]
    ):
        self.get_age_range = get_age_range
        self.get_attendee_age = get_attendee_age

    @classmethod
    def from_session(cls, session: Session) -> Self:
        attendees = None
        occasions = None

        def get_age_range(booking: Booking) -> tuple[int, int]:
            nonlocal occasions, session

            if occasions is None:
                occasions = {
                    o.id: o.age
                    for o in session.query(Occasion.id, Occasion.age)
                    .filter(Occasion.period_id == booking.period_id)}

            return (
                occasions[booking.occasion_id].lower,
                occasions[booking.occasion_id].upper - 1
            )

        def get_attendee_age(booking: Booking) -> int:
            nonlocal attendees, session

            if attendees is None:
                attendees = {a.id: a.age for a in session.query(
                    Attendee.id, Attendee.age)}

            return attendees[booking.attendee_id]

        return cls(get_age_range, get_attendee_age)

    def __call__(self, booking: Booking) -> float:
        min_age, max_age = self.get_age_range(booking)
        attendee_age = self.get_attendee_age(booking)

        if min_age <= attendee_age and attendee_age <= max_age:
            return 1.0
        else:
            difference = min(
                abs(min_age - attendee_age),
                abs(max_age - attendee_age)
            )
            return 1.0 - min(1.0, float(difference) / 10.0)


class PreferOrganiserChildren:
    """ Scores bookings of children higher if their parents are organisers.

    This is basically an incentive to become an organiser. A child whose parent
    is an organiser gets a score of 1.0, if the parent is not an organiser
    a score 0.0 is returned.

    """

    def __init__(self, get_is_organiser_child: Callable[[Booking], bool]):
        self.get_is_organiser_child = get_is_organiser_child

    @classmethod
    def from_session(cls, session: Session) -> Self:
        organisers = None

        def get_is_organiser_child(booking: Booking) -> bool:
            nonlocal organisers

            if organisers is None:
                organisers = {
                    username
                    for username, in session.query(Activity.username)
                    .filter(Activity.id.in_(
                        session.query(Occasion.activity_id)
                        .filter(Occasion.period_id == booking.period_id)
                        .subquery()
                    ))
                }

            return booking.username in organisers

        return cls(get_is_organiser_child)

    def __call__(self, booking: Booking) -> float:
        return 1.5 if self.get_is_organiser_child(booking) else 0.0


class PreferAdminChildren:
    """ Scores bookings of children higher if their parents are admins. """

    def __init__(self, get_is_association_child: Callable[[Booking], bool]):
        self.get_is_association_child = get_is_association_child

    @classmethod
    def from_session(cls, session: Session) -> Self:
        members = None

        def get_is_association_child(booking: Booking) -> bool:
            nonlocal members

            if members is None:
                members = {
                    u.username for u in session.query(User)
                    .filter(User.role == 'admin')
                    .filter(User.active == True)
                }

            return booking.username in members

        return cls(get_is_association_child)

    def __call__(self, booking: Booking) -> float:
        return self.get_is_association_child(booking) and 1.5 or 0.0


class PreferGroups:
    """ Scores group bookings higher than other bookings. Groups get a boost
    by size:

    - 2 people: 0.7
    - 3 people: 0.6
    - more people: 0.5

    This preference gives an extra boost to unprioritised bookings, to somewhat
    level out bookings in groups that used no star (otherwise a group
    might be split up because someone didn't star the booking).

    Additionally a unique boost between 0.010000000 to 0.099999999 is given to
    each group depending on the group name. This should ensure that competing
    groups generally do not have the same score. So an occasion will generally
    prefer the members of one group over members of another group.

    """

    def __init__(self, get_group_score: Callable[[Booking], float]):
        self.get_group_score = get_group_score

    @classmethod
    def from_session(cls, session: Session) -> Self:
        group_scores = None

        def unique_score_modifier(group_code: str) -> float:
            digest = hashlib.new(
                'sha1',
                group_code.encode('utf-8'),
                usedforsecurity=False
            ).hexdigest()[:8]
            number = int(digest, 16)

            return float('0.0' + str(number)[:8])

        def get_group_score(booking: Booking) -> float:
            nonlocal group_scores

            if group_scores is None:
                query = session.query(Booking).with_entities(
                    Booking.group_code,
                    func.count(Booking.group_code).label('count')
                ).filter(
                    Booking.group_code != None,
                    Booking.period_id == booking.period_id
                ).group_by(
                    Booking.group_code
                ).having(
                    func.count(Booking.group_code) > 1
                )

                group_scores = {
                    r.group_code:
                    max(.5, .7 - 0.1 * (r.count - 2))
                    + unique_score_modifier(r.group_code)

                    for r in query
                }

            return group_scores.get(booking.group_code, 0)

        return cls(get_group_score)

    def __call__(self, booking: Booking) -> float:
        return self.get_group_score(booking)
