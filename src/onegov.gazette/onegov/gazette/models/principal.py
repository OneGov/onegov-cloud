from collections import namedtuple
from collections import OrderedDict
from datetime import datetime
from dateutil.parser import parse
from yaml import load


class Issue(namedtuple('Issue', ['year', 'number'])):
    """ An issue, which consists of a year and a number.

    The issue might be converte from to a string in the form of 'year-number'
    for usage in forms and databases.

    """

    def __repr__(self):
        return '{}-{}'.format(self.year, self.number)

    @classmethod
    def from_string(cls, value):
        return cls(*[int(part) for part in value.split('-')])


class IssueDates(namedtuple('IssueDates', ['issue_date', 'deadline'])):
    """ An issue, which consists of a year and a number.

    The issue might be converte from to a string in the form of 'year-number'
    for usage in forms and databases.

    """

    def __repr__(self):
        return '{} / {}'.format(
            self.issue_date.isoformat(),
            self.deadline.isoformat()
        )

    @classmethod
    def from_string(cls, value):
        arguments = [parse(part) for part in value.split(' / ')]
        arguments[0] = arguments[0].date()
        return cls(*arguments)


class Principal(object):
    """ The principal is the political entity running the gazette app. """

    def __init__(
        self,
        name='',
        logo='',
        color='',
        organizations=None,
        categories=None,
        issues=None,
        publish_to='',
        publish_from='',
        time_zone='Europe/Zurich',
        help_link=''
    ):
        self.name = name
        self.logo = logo
        self.color = color
        self.publish_to = publish_to
        self.publish_from = publish_from
        self.time_zone = time_zone
        self.help_link = help_link

        # We want the organizations and categories in the order defined in the
        # YAML file and accessible by key
        self.organizations = OrderedDict(
            [next(enumerate(org.items()))[1] for org in (organizations or {})]
        )
        self.categories = OrderedDict(
            [next(enumerate(org.items()))[1] for org in (categories or {})]
        )

        # We want the issues accessible and ordered by year and issue number
        issues = issues or {}
        self.issues = OrderedDict()
        for year, numbers in sorted(issues.items(), key=lambda year: year[0]):
            self.issues[year] = OrderedDict([
                (key, IssueDates.from_string(numbers[key]))
                for key in sorted(numbers.keys())
            ])

        # ... and also accessible by date
        self.issues_by_date = OrderedDict()
        for year, numbers in self.issues.items():
            for number, dates in numbers.items():
                self.issues_by_date[dates.issue_date] = Issue(year, number)

        # ... and also accessible by deadline
        self.issues_by_deadline = OrderedDict()
        for year, numbers in self.issues.items():
            for number, dates in numbers.items():
                self.issues_by_deadline[dates.deadline] = Issue(year, number)

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))

    def issue(self, issue):
        """ Returns the issue dates of the given issue number. """

        if not isinstance(issue, Issue):
            issue = Issue.from_string(str(issue))

        return self.issues.get(issue.year, {}).get(issue.number, None)

    @property
    def current_issue(self):
        """ Returns the next issue with the nearest deadline. """

        now = datetime.utcnow()
        issues = [
            issue for deadline, issue in self.issues_by_deadline.items()
            if deadline > now
        ]
        return issues[0] if issues else None
