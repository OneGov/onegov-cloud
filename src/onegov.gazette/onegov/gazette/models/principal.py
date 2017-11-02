from collections import namedtuple
from collections import OrderedDict
from dateutil.parser import parse
from yaml import load


# todo: remove these in a future version, once it is migrated
class _IssueDates(namedtuple('IssueDates', ['issue_date', 'deadline'])):
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

        # todo: remove these in a future version, once it is migrated
        self._organizations = OrderedDict(
            [next(enumerate(org.items()))[1] for org in (organizations or {})]
        )
        self._categories = OrderedDict(
            [next(enumerate(org.items()))[1] for org in (categories or {})]
        )
        issues = issues or {}
        self._issues = OrderedDict()
        for year, numbers in sorted(issues.items(), key=lambda year: year[0]):
            self._issues[year] = OrderedDict([
                (key, _IssueDates.from_string(numbers[key]))
                for key in sorted(numbers.keys())
            ])

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))
