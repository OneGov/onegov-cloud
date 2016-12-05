from onegov.activity.models import Activity, Attendee, Occasion
from onegov.user import User


class Scoring(object):
    """ Provides scoring based on a number of criteria.

    A criteria is a callable which takes a booking and returns a score.
    The final score is the sum of all criteria scores.

    """

    def __init__(self, criteria=None):
        self.criteria = criteria or [PreferMotivated()]

    def __call__(self, booking):
        return sum(criterium(booking) for criterium in self.criteria)

    @classmethod
    def from_settings(cls, settings, session):
        scoring = cls()

        if settings.get('prefer_in_age_bracket'):
            scoring.criteria.append(
                PreferInAgeBracket.from_session(session))

        if settings.get('prefer_organiser'):
            scoring.criteria.append(
                PreferOrganiserChildren.from_session(session))

        if settings.get('prefer_admins'):
            scoring.criteria.append(
                PreferAdminChildren.from_session(session))

        return scoring

    @property
    def settings(self):
        classes = {c.__class__ for c in self.criteria}
        settings = {}

        if PreferInAgeBracket in classes:
            settings['prefer_in_age_bracket'] = True

        if PreferOrganiserChildren in classes:
            settings['prefer_organiser'] = True

        if PreferAdminChildren in classes:
            settings['prefer_admins'] = True

        return settings


class PreferMotivated(object):
    """ Scores "motivated" bookings higher. A motivated booking is simply a
    booking with a higher priority (an attendee would favor a booking he's
    excited about.)

    """

    @classmethod
    def from_session(cls, session):
        return cls()

    def __call__(self, booking):
        return booking.priority


class PreferInAgeBracket(object):
    """ Scores bookings whose attendees fall into the age-bracket of the
    occasion higher.

    If the attendee falls into the age-bracket, the score is 1.0. Each year
    difference results in a penalty of 0.1, until 0.0 is reached.

    """

    def __init__(self, get_age_range, get_attendee_age):
        self.get_age_range = get_age_range
        self.get_attendee_age = get_attendee_age

    @classmethod
    def from_session(cls, session):
        attendees = None
        occasions = None

        def get_age_range(booking):
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

        def get_attendee_age(booking):
            nonlocal attendees, session

            if attendees is None:
                attendees = {a.id: a.age for a in session.query(
                    Attendee.id, Attendee.age)}

            return attendees[booking.attendee_id]

        return cls(get_age_range, get_attendee_age)

    def __call__(self, booking):
        min_age, max_age = self.get_age_range(booking)
        attendee_age = self.get_attendee_age(booking)

        if min_age <= attendee_age and attendee_age <= max_age:
            return 1.0
        else:
            difference = min(
                abs(min_age - attendee_age),
                abs(max_age - attendee_age)
            )
            return 1.0 - min(1.0, difference / 10.0)


class PreferOrganiserChildren(object):
    """ Scores bookings of children higher if their parents are organisers.

    This is basically an incentive to become an organiser. A child whose parent
    is an organiser gets a score of 1.0, if the parent is not an organiser
    a score 0.0 is returned.

    """

    def __init__(self, get_is_organiser_child):
        self.get_is_organiser_child = get_is_organiser_child

    @classmethod
    def from_session(cls, session):
        organisers = None

        def get_is_organiser_child(booking):
            nonlocal organisers

            if organisers is None:
                organisers = {
                    a.username
                    for a in session.query(Activity.username)
                    .filter(Activity.id.in_(
                        session.query(Occasion.activity_id)
                        .filter(Occasion.period_id == booking.period_id)
                        .subquery()
                    ))
                }

            return booking.username in organisers

        return cls(get_is_organiser_child)

    def __call__(self, booking):
        return self.get_is_organiser_child(booking) and 1.0 or 0.0


class PreferAdminChildren(object):
    """ Scores bookings of children higher if their parents are admins. """

    def __init__(self, get_is_association_child):
        self.get_is_association_child = get_is_association_child

    @classmethod
    def from_session(cls, session):
        members = None

        def get_is_association_child(booking):
            nonlocal members

            if members is None:
                members = {
                    u.username for u in session.query(User)
                    .filter(User.role == 'admin')
                    .filter(User.active == True)
                }

            return booking.username in members

        return cls(get_is_association_child)

    def __call__(self, booking):
        return self.get_is_association_child(booking) and 1.0 or 0.0
