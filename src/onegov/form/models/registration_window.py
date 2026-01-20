from __future__ import annotations

import sedate

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.form.models.submission import FormSubmission
from sqlalchemy import and_
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy import Text
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import object_session, relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.sql.elements import quoted_name
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date, datetime
    from onegov.form.models.definition import FormDefinition


daterange = Column(  # type:ignore[call-overload]
    quoted_name('DATERANGE("start", "end")', quote=False))


class FormRegistrationWindow(Base, TimestampMixin):
    """ Defines a registration window during which a form definition
    may be used to create submissions.

    Submissions created thusly are attached to the currently active
    registration window.

    Registration windows may not overlap.

    """

    __tablename__ = 'registration_windows'

    #: the public id of the registraiton window
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of the form to which this registration window belongs
    name: Column[str] = Column(
        Text,
        ForeignKey('forms.name'),
        nullable=False
    )

    #: the form to which this registration window belongs
    form: relationship[FormDefinition] = relationship(
        'FormDefinition',
        back_populates='registration_windows'
    )

    #: true if the registration window is enabled
    enabled: Column[bool] = Column(Boolean, nullable=False, default=True)

    #: the start date of the window
    start: Column[date] = Column(Date, nullable=False)

    #: the end date of the window
    end: Column[date] = Column(Date, nullable=False)

    #: the timezone of the window
    timezone: Column[str] = Column(
        Text,
        nullable=False,
        default='Europe/Zurich'
    )

    #: the number of spots (None => unlimited)
    limit: Column[int | None] = Column(Integer, nullable=True)

    #: enable an overflow of submissions
    overflow: Column[bool] = Column(Boolean, nullable=False, default=True)

    #: submissions linked to this registration window
    submissions: relationship[list[FormSubmission]] = relationship(
        FormSubmission,
        back_populates='registration_window'
    )

    __table_args__ = (

        # ensures that there are no overlapping date ranges within one form
        ExcludeConstraint(
            (name, '='), (daterange, '&&'),
            name='no_overlapping_registration_windows',
            using='gist'
        ),

        # ensures that there are no adjacent date ranges
        # (end on the same day as next start)
        ExcludeConstraint(
            (name, '='), (daterange, '-|-'),
            name='no_adjacent_registration_windows',
            using='gist'
        ),

        # ensures that start <= end
        CheckConstraint(
            '"start" <= "end"',
            name='start_smaller_than_end'
        ),
    )

    @property
    def localized_start(self) -> datetime:
        return sedate.align_date_to_day(
            sedate.standardize_date(
                sedate.as_datetime(self.start), self.timezone
            ), self.timezone, 'down'
        )

    @property
    def localized_end(self) -> datetime:
        return sedate.align_date_to_day(
            sedate.standardize_date(
                sedate.as_datetime(self.end), self.timezone
            ), self.timezone, 'up'
        )

    def disassociate(self) -> None:
        """ Disassociates all records linked to this window. """

        for submission in self.submissions:
            submission.disclaim()
            submission.registration_window_id = None

    @property
    def in_the_future(self) -> bool:
        return sedate.utcnow() <= self.localized_start

    @property
    def in_the_past(self) -> bool:
        return self.localized_end <= sedate.utcnow()

    @property
    def in_the_present(self) -> bool:
        return self.localized_start <= sedate.utcnow() <= self.localized_end

    def accepts_submissions(self, required_spots: int = 1) -> bool:
        assert required_spots > 0

        if not self.enabled:
            return False

        if not self.in_the_present:
            return False

        if self.overflow:
            return True

        if self.limit is None:
            return True

        return self.available_spots >= required_spots

    @property
    def next_submission(self) -> FormSubmission | None:
        """ Returns the submission next in line. In other words, the next
        submission in order of first come, first serve.

        """

        q = object_session(self).query(FormSubmission)
        q = q.filter(FormSubmission.registration_window_id == self.id)
        q = q.filter(FormSubmission.state == 'complete')
        q = q.filter(or_(
            FormSubmission.claimed == None,
            and_(
                FormSubmission.claimed > 0,
                FormSubmission.claimed < FormSubmission.spots,
            )
        ))
        q = q.order_by(FormSubmission.created)

        return q.first()

    @property
    def available_spots(self) -> int:
        assert self.limit is not None
        return max(self.limit - self.claimed_spots - self.requested_spots, 0)

    @property
    def claimed_spots(self) -> int:
        """ Returns the number of actually claimed spots. """

        return object_session(self).execute(text("""
            SELECT SUM(COALESCE(claimed, 0))
            FROM submissions
            WHERE registration_window_id = :id
            AND submissions.state = 'complete'
        """), {'id': self.id}).scalar() or 0

    @property
    def requested_spots(self) -> int:
        """ Returns the number of requested spots.

        When the claim has not been made yet, `spots` are counted as
        requested. When the claim has been partially made, the difference is
        counted as requested. If the claim has been fully made, the result is
        0. If the claim has been relinquished, the result is 0.

        """
        return object_session(self).execute(text("""
            SELECT GREATEST(
                SUM(
                    CASE WHEN claimed IS NULL THEN spots
                         WHEN claimed = 0 THEN 0
                         ELSE spots - claimed
                    END
                ), 0
            )
            FROM submissions
            WHERE registration_window_id = :id
            AND submissions.state = 'complete'
        """), {'id': self.id}).scalar() or 0
