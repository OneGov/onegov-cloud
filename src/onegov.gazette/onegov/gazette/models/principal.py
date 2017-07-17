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


class CategoryDict(OrderedDict):
    """ An ordered dict which supports inheritance. """

    def __init__(self, parent=None, parent_key=None):
        super(CategoryDict, self).__init__()
        self.parent = parent
        self.parent_key = parent_key
        self.children = {}

    def new_child(self, key):
        return self.children.setdefault(
            key, CategoryDict(parent=self, parent_key=key)
        )


class Principal(object):
    """ The principal is the political entity running the gazette app. """

    def __init__(
        self,
        name='',
        logo='',
        color='',
        categories=None,
        issues=None,
        publish_to=''
    ):
        categories = categories or []
        issues = issues or {}

        self.name = name
        self.logo = logo
        self.color = color
        self.publish_to = publish_to

        # We want the categories nested, accessible by the id and in the order
        # defined in the configuration
        def add_categories(values, target):
            for category in values:
                key = [key for key in category.keys() if key != 'children'][0]
                target[key] = category[key]

                children = category.get('children')
                if children:
                    add_categories(children, target.new_child(key))

        self.categories = CategoryDict()
        add_categories(categories, self.categories)

        # But we want the categories also accessible in a flat array with
        # breadcrumbs.
        def add_flat_categories(values, target):
            if not values:
                return

            path = []
            cursor = values
            while cursor.parent:
                path.insert(0, cursor.parent[cursor.parent_key])
                cursor = cursor.parent

            target.update({
                key: path + [value] for key, value in values.items()
            })

            for child in values.children.values():
                add_flat_categories(child, target)

        self.categories_flat = {}
        add_flat_categories(self.categories, self.categories_flat)

        # We want the issues accessible and ordered by year and issue number
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
