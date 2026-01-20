from __future__ import annotations

import sedate

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.form.models.submission import SurveySubmission
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.sql.elements import quoted_name
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date, datetime
    from onegov.form.models.definition import SurveyDefinition


daterange = Column(  # type:ignore[call-overload]
    quoted_name('DATERANGE("start", "end")', quote=False))


class SurveySubmissionWindow(Base, TimestampMixin):
    """ Defines a submission window during which a form definition
    may be used to create submissions.

    Submissions created thusly are attached to the currently active
    survey window.

    submission windows may not overlap.

    """

    __tablename__ = 'submission_windows'

    #: the public id of the submission window
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of the survey to which this submission window belongs
    name: Column[str] = Column(
        Text,
        ForeignKey('surveys.name'),
        nullable=False
    )

    #: the title of the submission window
    title = Column(Text)

    #: the survey to which this submission window belongs
    survey: relationship[SurveyDefinition] = relationship(
        'SurveyDefinition',
        back_populates='submission_windows'
    )

    #: true if the submission window is enabled
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

    #: submissions linked to this
    submissions: relationship[list[SurveySubmission]] = relationship(
        SurveySubmission,
        back_populates='submission_window'
    )

    __table_args__ = (
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

    @property
    def in_the_future(self) -> bool:
        return sedate.utcnow() <= self.localized_start

    @property
    def in_the_past(self) -> bool:
        return self.localized_end <= sedate.utcnow()

    @property
    def in_the_present(self) -> bool:
        return self.localized_start <= sedate.utcnow() <= self.localized_end

    def accepts_submissions(self) -> bool:

        if not self.enabled:
            return False

        if not self.in_the_present:
            return False

        return True
