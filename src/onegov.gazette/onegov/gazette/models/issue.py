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

    @property
    def first_publication_number(self):
        """ Returns the first publication number of this issue based on the
        last issue of the same year. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        session = object_session(self)

        issues = session.query(Issue.name)
        issues = issues.filter(extract('year', Issue.date) == self.date.year)
        issues = issues.filter(Issue.date < self.date)
        issues = [issue[0] for issue in issues]
        if not issues:
            return 1

        numbers = []
        for issue in issues:
            query = session.query(GazetteNotice._issues[issue])
            query = query.filter(GazetteNotice._issues.has_key(issue))  # noqa
            numbers.extend([int(x[0]) for x in query if x[0]])
        return max(numbers) + 1 if numbers else 1

    def publication_numbers(self, state=None):
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
        """ Publishes the issue.

        This ensures that every accepted notice of this issue is published. It
        then creates the PDF while assigning the publications numbers (it uses
        the highest publication number of the last issue of the same year as a
        starting point.

        """

        for notice in self.notices('accepted'):
            notice.publish(request)

        from onegov.gazette.pdf import Pdf  # circular
        self.pdf = Pdf.from_issue(self, request, self.first_publication_number)
