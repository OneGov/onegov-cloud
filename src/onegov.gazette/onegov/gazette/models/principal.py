from collections import namedtuple
from collections import OrderedDict
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
        publish_to=''
    ):
        self.name = name
        self.logo = logo
        self.color = color
        self.publish_to = publish_to

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
            self.issues[year] = OrderedDict(
                sorted(numbers.items(), key=lambda issue: issue[0])
            )

        # And we want them also accessible by date
        self.issues_by_date = OrderedDict()
        for year, numbers in self.issues.items():
            for number, date in numbers.items():
                self.issues_by_date[date] = Issue(year, number)

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))
