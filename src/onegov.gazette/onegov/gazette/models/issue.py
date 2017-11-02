from collections import namedtuple
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from sedate import as_datetime
from sedate import standardize_date
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import or_
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


class Issue(Base, TimestampMixin):
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

    def in_use(self, session):
        """ True, if the issued is used by any notice. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        query = session.query(GazetteNotice._issues)
        query = query.filter(GazetteNotice._issues.has_key(self.name))  # noqa
        if query.first():
            return True

        return False

    @observes('date')
    def date_observer(self, date_):
        """ Changes the issue date of the notices when updating the date
        of the issue.

        """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        date_time = standardize_date(as_datetime(date_), 'UTC')
        query = object_session(self).query(GazetteNotice)
        query = query.filter(
            GazetteNotice._issues.has_key(self.name),  # noqa
            or_(
                GazetteNotice.first_issue.is_(None),
                GazetteNotice.first_issue != date_time
            )
        )
        for notice in query:
            notice.first_issue = date_time
