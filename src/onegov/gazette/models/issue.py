from __future__ import annotations

from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.gazette.observer import observes
from sedate import as_datetime
from sedate import standardize_date
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import extract
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session


from typing import IO
from typing import NamedTuple
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date as date_t
    from datetime import datetime
    from onegov.gazette.models import GazetteNotice
    from onegov.gazette.request import GazetteRequest
    from onegov.notice.models import NoticeState
    from sqlalchemy.orm import Query
    from typing import Self


class IssueName(NamedTuple):
    """ An issue, which consists of a year and a number.

    The issue might be converted from to a string in the form of 'year-number'
    for usage in forms and databases.

    """
    year: int
    number: int

    def __repr__(self) -> str:
        return f'{self.year}-{self.number}'

    @classmethod
    def from_string(cls, value: str) -> Self:
        year, number = value.split('-', maxsplit=1)
        return cls(int(year), int(number))


class IssuePdfFile(File):
    __mapper_args__ = {'polymorphic_identity': 'gazette_issue'}


class Issue(Base, TimestampMixin, AssociatedFiles):
    """ Defines an issue. """

    __tablename__ = 'gazette_issues'

    #: the id of the db record (only relevant internally)
    id: Column[int] = Column(Integer, primary_key=True)

    #: The name of the issue.
    name: Column[str] = Column(Text, nullable=False)

    #: The number of the issue.
    number: Column[int | None] = Column(Integer, nullable=True)

    # The issue date.
    # FIXME: This clearly is meant to not be nullable, the observer
    #        only works if all dates are set
    date: Column[date_t] = Column(Date, nullable=True)  # type:ignore

    # The deadline of this issue.
    deadline: Column[datetime | None] = Column(UTCDateTime, nullable=True)

    @property
    def pdf(self) -> File | None:
        return self.files[0] if self.files else None

    # FIXME: asymmetric properties don't work, need a custom descriptor
    @pdf.setter
    def pdf(self, value: bytes | IO[bytes]) -> None:
        filename = f'{self.name}.pdf'

        pdf = self.pdf or IssuePdfFile(id=random_token())
        pdf.name = filename
        pdf.reference = as_fileintent(value, filename)

        if not self.pdf:
            self.files.append(pdf)

    def notices(
        self,
        state: NoticeState | None = None
    ) -> Query[GazetteNotice]:
        """ Returns a query to get all notices related to this issue. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = object_session(self).query(GazetteNotice)
        notices = notices.filter(
            GazetteNotice._issues.has_key(self.name)  # type:ignore
        )
        if state:
            notices = notices.filter(GazetteNotice.state == state)

        return notices

    @property
    def first_publication_number(self) -> int:
        """ Returns the first publication number of this issue based on the
        last issue of the same year. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        session = object_session(self)

        issues = session.query(Issue.name)
        issues = issues.filter(extract('year', Issue.date) == self.date.year)
        issues = issues.filter(Issue.date < self.date)
        issues = [issue_name for issue_name, in issues]
        if not issues:
            return 1

        # FIXME: This seems slow, just outer join the two queries
        numbers: list[int] = []
        for issue in issues:
            query = session.query(GazetteNotice._issues[issue])
            query = query.filter(
                GazetteNotice._issues.has_key(issue)  # type:ignore
            )
            numbers.extend(int(value) for value, in query if value)
        return max(numbers) + 1 if numbers else 1

    def publication_numbers(
        self,
        state: NoticeState | None = None
    ) -> dict[int, str | None]:
        """ Returns a dictionary containing all publication numbers (by notice)
        of this issue.

        """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        query = self.notices(state).with_entities(
            GazetteNotice.id,
            GazetteNotice._issues[self.name]
        )
        return dict(query)

    @property
    def in_use(self) -> bool:
        """ True, if the issue is used by any notice. """

        session = object_session(self)
        return session.query(self.notices().exists()).scalar()

    @observes('date')
    def date_observer(self, date_: date_t) -> None:
        """ Changes the issue date of the notices when updating the date
        of the issue.

        At this moment, the transaction is not yet commited: Querying the
        current issue returns the old date.

        """

        query: Query[tuple[str, date_t]]
        query = object_session(self).query(Issue.name, Issue.date)
        issue_dates = dict(query.order_by(Issue.date))
        issue_dates[self.name] = date_
        issues = {
            key: standardize_date(as_datetime(value), 'UTC')
            for key, value in issue_dates.items()
        }

        for notice in self.notices():
            notice.first_issue = min(
                date
                for issue in notice._issues
                if (date := issues.get(issue, None))
            )

    def publish(self, request: GazetteRequest) -> None:
        """ Publishes the issue.

        This ensures that every accepted notice of this issue is published. It
        then creates the PDF while assigning the publications numbers (it uses
        the highest publication number of the last issue of the same year as a
        starting point.

        """

        for notice in self.notices('accepted'):
            notice.publish(request)

        from onegov.gazette.pdf import IssuePdf  # circular
        self.pdf = IssuePdf.from_issue(
            issue=self,
            request=request,
            first_publication_number=self.first_publication_number,
            links=request.app.principal.links
        )
