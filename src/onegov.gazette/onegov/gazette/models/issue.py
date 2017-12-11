from collections import namedtuple
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.file.utils import as_fileintent
from sedate import as_datetime
from sedate import standardize_date
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import extract
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.orm import object_session


class IssueName(namedtuple('IssueName', ['year', 'number'])):
    """ An issue, which consists of a year and a number.

    The issue might be converted from to a string in the form of 'year-number'
    for usage in forms and databases.

    """

    def __repr__(self):
        return '{}-{}'.format(self.year, self.number)

    @classmethod
    def from_string(cls, value):
        return cls(*[int(part) for part in value.split('-')])


class IssuePdfFile(File):
    __mapper_args__ = {'polymorphic_identity': 'gazette_issue'}


class Issue(Base, TimestampMixin, AssociatedFiles):
    """ Defines an issue. """

    __tablename__ = 'gazette_issues'

    #: the id of the db record (only relevant internally)
    id = Column(Integer, primary_key=True)

    #: The name of the issue.
    name = Column(Text, nullable=False)

    #: The number of the issue.
    number = Column(Integer, nullable=True)

    # The issue date.
    date = Column(Date, nullable=True)

    # The deadline of this issue.
    deadline = Column(UTCDateTime, nullable=True)

    @property
    def pdf(self):
        return self.files[0] if self.files else None

    @pdf.setter
    def pdf(self, value):
        filename = '{}.pdf'.format(self.name)

        pdf = self.pdf or IssuePdfFile(id=random_token())
        pdf.name = filename
        pdf.reference = as_fileintent(value, filename)

        if not self.pdf:
            self.files.append(pdf)

    def notices(self, state=None):
        """ Returns a query to get all notices related to this issue. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = object_session(self).query(GazetteNotice)
        notices = notices.filter(
            GazetteNotice._issues.has_key(self.name)  # noqa
        )
        if state:
            notices = notices.filter(GazetteNotice.state == state)

        return notices

    @staticmethod
    def publication_numbers(session):
        """ Returns the current publication numbers by year. """

        from onegov.gazette.models.notice import GazetteNotice  # circular
        from onegov.gazette.collections.issues import IssueCollection  # circ.

        result = {}

        for year in IssueCollection(session).years:
            numbers = []

            issues = session.query(Issue.name)
            issues = issues.filter(extract('year', Issue.date) == year)
            for issue in issues:
                numbers.extend([
                    x[0] for x in session.query(GazetteNotice._issues[issue])
                    if x[0]
                ])
            numbers = [int(number) for number in numbers]

            result[year] = max(numbers) if numbers else 0

        return result

    @property
    def in_use(self):
        """ True, if the issued is used by any notice. """

        if self.notices().first():
            return True

        return False

    @observes('date')
    def date_observer(self, date_):
        """ Changes the issue date of the notices when updating the date
        of the issue.

        At this moment, the transaction is not yet commited: Querying the
        current issue returns the old date.

        """

        issues = object_session(self).query(Issue.name, Issue.date)
        issues = dict(issues.order_by(Issue.date))
        issues[self.name] = date_
        issues = {
            key: standardize_date(as_datetime(value), 'UTC')
            for key, value in issues.items()
        }

        for notice in self.notices():
            dates = [issues.get(issue, None) for issue in notice._issues]
            dates = [date for date in dates if date]
            notice.first_issue = min(dates)

    def publish(self, request):
        """ Ensures that every accepted notice of this issue has been
        published.

        """

        publication_numbers = None
        for notice in self.notices('accepted'):
            publication_numbers = notice.publish(request, publication_numbers)
