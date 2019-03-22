import re
import yaml

from collections import defaultdict
from datetime import date, datetime, time
from more_itertools import collapse
from onegov.core.custom import json
from onegov.core.utils import normalize_for_url, safe_format, safe_format_keys
from onegov.form import parse_formcode, flatten_fieldsets, as_internal_id
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy_utils.types.scalar_coercible import ScalarCoercible
from urllib.parse import quote_plus

# XXX i18n
SAFE_FORMAT_TRANSLATORS = {
    date: lambda d: d.strftime('%d.%m.%Y'),
    datetime: lambda d: d.strftime('%d.%m.%Y %H:%M'),
    time: lambda t: t.strftime('%H:%M')
}


number_chunks = re.compile(r'([0-9]+)')


def pad_numbers_in_chunks(text, padding=8):
    """ Alphanumeric sorting by padding all numbers.

    For example:
        foobar-1-to-10 becomes foobar-0000000001-to-0000000010)

    See:
        https://nedbatchelder.com/blog/200712/human_sorting.html

    """
    return ''.join((
        part.rjust(padding, '0') if part.isdigit() else part
        for part in number_chunks.split(text)
    ))


class DirectoryConfigurationStorage(TypeDecorator, ScalarCoercible):

    impl = TEXT

    @property
    def python_type(self):
        return DirectoryConfiguration

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.to_json()

    def process_result_value(self, value, dialect):
        if value is not None:
            return DirectoryConfiguration.from_json(value)


class StoredConfiguration(object):

    fields = None

    def to_dict(self):
        return {
            name: getattr(self, name)
            for name in self.fields
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_yaml(self):
        text = yaml.dump(self.to_dict(), default_flow_style=False)
        return text.replace('\n- ', '\n  - ')

    @classmethod
    def from_json(cls, text):
        return cls(**json.loads(text))

    @classmethod
    def from_yaml(cls, text):
        return cls(**yaml.safe_load(text))


class DirectoryConfiguration(Mutable, StoredConfiguration):

    fields = (
        'title',
        'lead',
        'order',
        'keywords',
        'searchable',
        'display',
        'direction',
        'link_pattern',
        'link_title',
        'link_visible',
        'thumbnail'
    )

    def __init__(self, title=None, lead=None, order=None, keywords=None,
                 searchable=None, display=None, direction=None,
                 link_pattern=None, link_title=None, link_visible=None,
                 thumbnail=None):

        self.title = title
        self.lead = lead
        self.order = order
        self.keywords = keywords
        self.searchable = searchable
        self.display = display
        self.direction = direction
        self.link_pattern = link_pattern
        self.link_title = link_title
        self.link_visible = link_visible
        self.thumbnail = thumbnail

    def __setattr__(self, name, value):
        self.changed()
        return super().__setattr__(name, value)

    def missing_fields(self, formcode):
        """ Takes the given formcode and returns a dictionary with missing
        fields per configuration field. If the return-value is falsy, the
        configuration is valid.

        For example::

            >>> cfg = DirectoryConfiguration(title='[Name]')
            >>> cfg.missing_fields('Title = ___')

            {'title': ['Name']}

        """
        formfields = tuple(flatten_fieldsets(parse_formcode(formcode)))
        known = {field.human_id for field in formfields}

        errors = defaultdict(list)

        for name in self.fields:
            if not getattr(self, name):
                continue

            # booleans
            if name == 'link_visible':
                continue

            if name in ('title', 'lead'):
                found = safe_format_keys(getattr(self, name))
            else:
                found = getattr(self, name)

            for id in found:
                if id not in known:
                    errors[name].append(id)

        return errors

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, Mutable):
            raise TypeError()
        else:
            return value

    def join(self, data, attribute, separator='\n'):
        def render(value):
            if isinstance(value, (list, tuple)):
                return '\n'.join(v.strip() for v in value)

            if isinstance(value, str):
                return value.strip()

            return value and str(value) or ''

        return separator.join(render(s) for s in (
            data[as_internal_id(key)] for key in getattr(self, attribute)
        ))

    def safe_format(self, fmt, data):
        return safe_format(
            fmt, self.for_safe_format(data), adapt=as_internal_id)

    def for_safe_format(self, data):
        return {
            k: SAFE_FORMAT_TRANSLATORS.get(type(v), str)(v)
            for k, v in data.items()
            if (
                type(v) in (str, int, float)
                or type(v) in SAFE_FORMAT_TRANSLATORS
            )
        }

    def extract_name(self, data):
        return normalize_for_url(self.extract_title(data))

    def extract_title(self, data):
        return self.safe_format(self.title, data)

    def extract_lead(self, data):
        return self.lead and self.safe_format(self.lead, data)

    def extract_link(self, data):
        return self.link_pattern and self.safe_format(self.link_pattern, {
            k: quote_plus(v) for k, v in self.for_safe_format(data).items()
        })

    def extract_order(self, data):
        # by default we use the title as order
        attribute = (
            (self.order and 'order')
            or (self.title and 'title')
        )
        order = normalize_for_url(self.join(data, attribute))
        order = pad_numbers_in_chunks(order)

        return order

    def extract_searchable(self, data):
        if self.searchable:
            return self.join(data, 'searchable')

    def extract_keywords(self, data):
        if self.keywords:
            keywords = set()

            for key in self.keywords:
                key = as_internal_id(key)

                for value in collapse(data[key]):
                    if isinstance(value, str):
                        value = value.strip()

                    if value:
                        keywords.add(':'.join((key, value)))

            return keywords


DirectoryConfiguration.associate_with(DirectoryConfigurationStorage)
