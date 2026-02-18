from __future__ import annotations

import pytest
import transaction

from datetime import date, timedelta
from onegov.form import Form
from onegov.form import FormCollection
from onegov.form import FormExtension
from onegov.form import FormRegistrationWindow
from onegov.form import FormSubmission
from sqlalchemy.exc import IntegrityError
from webob.multidict import MultiDict
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form.types import RegistrationState
    from sqlalchemy.orm import Session


def days(d: int) -> timedelta:
    return timedelta(days=d)


def test_has_submissions(session: Session) -> None:
    collection = FormCollection(session)
    form = collection.definitions.add('Newsletter', definition="E-Mail = @@@")

    assert not form.has_submissions()

    data = MultiDict([
        ('e_mail', 'test@example.org'),
    ])

    collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    assert not form.has_submissions(with_state='pending')
    assert form.has_submissions(with_state='complete')
    assert form.has_submissions()


def test_form_extensions(session: Session) -> None:
    collection = FormCollection(session)

    members = collection.definitions.add('Members', definition="E-Mail = @@@")

    class CorporateOnly:

        def validate_e_mail(self, value: Any) -> None:
            # note, you probably don't want to do this in a real world
            # project as the name of the e-mail field might change and
            # the validation would not be triggered!
            if not value.data.endswith('seantis.ch'):
                raise ValidationError("Only seantis.ch e-mails are allowed")

    class CorporateOnlyExtension(
        FormExtension[Form],
        name='corporate-emails-only'
    ):

        def create(self) -> type[Form]:
            class ExtendedForm(self.form_class, CorporateOnly):  # type: ignore[misc, name-defined]
                pass

            return ExtendedForm

    members.meta['extensions'] = ['corporate-emails-only']
    assert issubclass(members.form_class, CorporateOnly)

    session.flush()

    # the validation should fail here
    data = MultiDict([
        ('e_mail', 'test@example.org'),
    ])

    form = members.form_class(data)
    form.validate()
    assert form.errors

    with pytest.raises(AssertionError) as e:
        collection.submissions.add('newsletter', form, state='complete')

    assert "the given form doesn't validate" in str(e.value)

    # now it should work
    data = MultiDict([
        ('e_mail', 'test@seantis.ch'),
    ])

    form = members.form_class(data)
    form.validate()
    assert not form.errors

    # the extensions are carried over to the submission
    submission = collection.submissions.add(
        'members', form, state='complete')
    assert issubclass(submission.form_class, CorporateOnly)


def test_registration_window_adjacent(session: Session) -> None:
    forms = FormCollection(session)

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    winter = forms.definitions.add('Witnercamp', definition="E-Mail = @@@")

    summer.add_registration_window(date(2018, 4, 1), date(2018, 6, 30))
    summer.add_registration_window(date(2017, 4, 1), date(2017, 6, 30))

    assert len(summer.registration_windows) == 2

    # Test ordering ascending has not worked using order_by in the relationship
    # of the model, should be 2017
    assert summer.registration_windows[0].start.year == 2018

    winter.add_registration_window(date(2017, 4, 1), date(2017, 6, 30))
    winter.add_registration_window(date(2018, 4, 1), date(2018, 6, 30))

    assert len(winter.registration_windows) == 2

    # no overlap -> different forms
    session.flush()

    # adjacent, fails
    summer.add_registration_window(date(2017, 1, 1), date(2017, 4, 1))

    with pytest.raises(IntegrityError) as e:
        session.flush()

    assert 'no_adjacent_registration_windows' in str(e.value)


def test_registration_window_overlaps(session: Session) -> None:
    forms = FormCollection(session)

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    summer.add_registration_window(date(2017, 4, 1), date(2017, 6, 30))

    assert len(summer.registration_windows) == 1

    # no overlap -> different forms
    session.flush()

    # overlapping, fails
    summer.add_registration_window(date(2017, 1, 1), date(2017, 4, 2))

    with pytest.raises(IntegrityError) as e:
        session.flush()

    assert 'no_overlapping_registration_windows' in str(e.value)


def test_registration_window_end_before_start(session: Session) -> None:
    camp = FormCollection(session).definitions.add(
        'Camp', definition="E-Mail = @@@")

    camp.add_registration_window(date(2018, 1, 1), date(2017, 1, 1))

    with pytest.raises(IntegrityError) as e:
        session.flush()

    assert 'start_smaller_than_end' in str(e.value)


def test_current_registration_window_bound_to_form(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    winter = forms.definitions.add('Witnercamp', definition="E-Mail = @@@")
    winter.add_registration_window(today - days(1), today + days(1))

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    summer.add_registration_window(today - days(100), today - days(10))

    assert winter.current_registration_window is not None
    assert winter.current_registration_window.start == today - days(1)
    assert summer.current_registration_window is not None
    assert summer.current_registration_window.start == today - days(100)


def test_current_registration_window_end_date(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")

    # the first window is closer, though the start is further away
    summer.add_registration_window(today - days(10), today - days(1))
    summer.add_registration_window(today + days(5), today + days(10))

    assert summer.current_registration_window is not None
    assert summer.current_registration_window.start == today - days(10)


@pytest.mark.skip_night_hours
def test_registration_window_spots(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    window = summer.add_registration_window(today - days(5), today + days(5))

    session.flush()

    window.enabled = False
    assert not window.accepts_submissions()

    window.enabled = True
    window.end = today - days(1)
    assert not window.accepts_submissions()

    window.start = today + days(1)
    window.end = today + days(5)
    assert not window.accepts_submissions()

    window.start = today - days(5)
    window.overflow = True
    assert window.accepts_submissions()

    window.overflow = False
    window.limit = None
    assert window.accepts_submissions()
    assert window.claimed_spots == 0
    assert window.requested_spots == 0

    window.limit = 2
    assert window.accepts_submissions()
    assert window.claimed_spots == 0
    assert window.requested_spots == 0

    s1 = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=1
    )

    assert window.accepts_submissions()
    assert window.claimed_spots == 0
    assert window.requested_spots == 1

    s2 = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=1
    )

    assert not window.accepts_submissions()
    assert window.claimed_spots == 0
    assert window.requested_spots == 2

    window.overflow = True
    assert window.accepts_submissions()

    s1.claim(1)
    session.flush()

    assert window.accepts_submissions()
    assert window.claimed_spots == 1
    assert window.requested_spots == 1

    window.overflow = False
    assert not window.accepts_submissions()

    s2.claim(1)
    session.flush()

    assert not window.accepts_submissions()
    assert window.claimed_spots == 2
    assert window.requested_spots == 0

    window.overflow = True
    assert window.accepts_submissions()


def test_registration_claims_with_no_limit(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")

    window = summer.add_registration_window(today - days(5), today + days(5))
    window.limit = None

    session.flush()

    submission = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=100
    )

    submission.claim()
    session.flush()

    assert submission.claimed == 100
    assert submission.spots == 100
    assert window.claimed_spots == 100
    assert window.requested_spots == 0

    submission.disclaim()
    session.flush()

    assert submission.claimed == 0
    assert submission.spots == 100
    assert window.claimed_spots == 0
    assert window.requested_spots == 0

    submission.claim(50)
    session.flush()

    assert submission.claimed == 50
    assert submission.spots == 100
    assert window.claimed_spots == 50
    assert window.requested_spots == 50

    submission.claim(25)
    session.flush()

    assert submission.claimed == 75
    assert submission.spots == 100
    assert window.claimed_spots == 75
    assert window.requested_spots == 25

    submission.claim(25)
    session.flush()

    assert submission.claimed == 100
    assert submission.spots == 100
    assert window.claimed_spots == 100
    assert window.requested_spots == 0

    submission.disclaim(25)
    session.flush()

    assert submission.claimed == 75
    assert submission.spots == 100
    assert window.claimed_spots == 75
    assert window.requested_spots == 25

    submission.disclaim()
    session.flush()

    assert submission.claimed == 0
    assert submission.spots == 100
    assert window.claimed_spots == 0
    assert window.requested_spots == 0


def test_registration_claims_with_a_limit(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")

    window = summer.add_registration_window(today - days(5), today + days(5))
    window.limit = 10
    window.overflow = True

    session.flush()

    submission = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=100
    )

    assert not submission.claim()

    assert not submission.claim(11)

    assert submission.claim(spots=10)
    session.flush()

    assert window.claimed_spots == 10
    assert window.requested_spots == 90
    assert window.available_spots == 0

    submission.disclaim()
    session.flush()

    assert window.claimed_spots == 0
    assert window.requested_spots == 0
    assert window.available_spots == 10


def test_register_more_than_allowed(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")

    window = summer.add_registration_window(today - days(5), today + days(5))
    window.limit = 1
    window.overflow = False

    session.flush()

    with pytest.raises(AssertionError):
        forms.submissions.add(
            name='summercamp',
            form=summer.form_class(data={'e_mail': 'info@example.org'}),
            state='complete',
            spots=2
        )

    window.overflow = True
    session.flush()

    forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=2
    )

    window.overflow = False
    session.flush()


def test_undo_registration(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")

    window = summer.add_registration_window(today - days(5), today + days(5))
    window.limit = 1
    window.overflow = False

    session.flush()

    assert window.available_spots == 1

    submission = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=1
    )
    session.flush()

    assert window.available_spots == 0

    submission.claim()
    session.flush()

    assert window.available_spots == 0

    submission.disclaim()
    session.flush()

    assert window.available_spots == 1


def test_registration_window_queue(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    window = summer.add_registration_window(today - days(5), today + days(5))

    session.flush()

    first = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=10
    )
    session.flush()

    assert window.next_submission is first

    second = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=10
    )
    session.flush()

    assert window.next_submission is first

    first.claim()
    session.flush()

    assert window.next_submission is second

    second.claim(5)
    session.flush()

    assert window.next_submission is second

    second.claim(5)
    session.flush()

    assert window.next_submission is None


def test_require_spots_if_registration_window(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    summer.add_registration_window(today - days(5), today + days(5))

    session.flush()

    with pytest.raises(AssertionError):
        forms.submissions.add(
            name='summercamp',
            form=summer.form_class(data={'e_mail': 'info@example.org'}),
            state='complete',
            spots=0
        )

    with pytest.raises(AssertionError):
        forms.submissions.add(
            name='summercamp',
            form=summer.form_class(data={'e_mail': 'info@example.org'}),
            state='complete',
            spots=None
        )


def test_registration_submission_state(session: Session) -> None:
    forms = FormCollection(session)
    today = date.today()

    summer = forms.definitions.add('Summercamp', definition="E-Mail = @@@")
    session.flush()

    submission = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
    )

    def query_registration_state() -> RegistrationState | None:
        q = forms.submissions.query()
        q = q.with_entities(FormSubmission.registration_state)
        q = q.order_by(FormSubmission.created.desc())

        return q.scalar()

    assert submission.registration_state is None
    assert query_registration_state() is None

    summer = forms.definitions.by_name('summercamp')  # type: ignore[assignment]
    summer.add_registration_window(today - days(5), today + days(5), limit=10)

    session.flush()

    # required here for some reason, otherwise there's no current window
    transaction.commit()

    summer = forms.definitions.by_name('summercamp')  # type: ignore[assignment]
    submission = forms.submissions.add(
        name='summercamp',
        form=summer.form_class(data={'e_mail': 'info@example.org'}),
        state='complete',
        spots=2
    )
    session.flush()

    assert submission.registration_state == 'open'
    assert query_registration_state() == 'open'

    submission.claim(1)

    # undo mypy narrowing of registration_state
    submission2 = submission
    assert submission2.registration_state == 'partial'
    assert query_registration_state() == 'partial'

    submission.claim(1)
    # undo mypy narrowing of registration_state
    submission2 = submission
    assert submission2.registration_state == 'confirmed'
    assert query_registration_state() == 'confirmed'

    submission.disclaim()
    # undo mypy narrowing of registration_state
    submission2 = submission
    assert submission2.registration_state == 'cancelled'
    assert query_registration_state() == 'cancelled'

    # test deletion cascading to registration windows
    assert session.query(FormRegistrationWindow).first()

    forms = FormCollection(session)
    assert session.query(FormSubmission).first()

    with pytest.raises(IntegrityError):
        forms.definitions.delete(
            summer.name,
            with_submissions=False,
            with_registration_windows=True)

    transaction.begin()

    forms.definitions.delete(
        summer.name,
        with_submissions=True,
        with_registration_windows=True)

    assert not session.query(FormRegistrationWindow).first()
    assert not session.query(FormSubmission).first()
