from more_itertools import collapse
from onegov.core import custom_json as json
from onegov.core.utils import normalize_for_url
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, TEXT


class DirectoryConfigurationStorage(TypeDecorator):

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = value.to_json()

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = DirectoryConfiguration.from_json(value)

        return value


class JSONConfiguration(object):

    fields = None

    def to_json(self):
        return json.dumps({
            name: getattr(self, name)
            for name in self.fields
        })

    @classmethod
    def from_json(cls, text):
        return cls(**json.loads(text))


class DirectoryConfiguration(Mutable, JSONConfiguration):

    fields = ('title', 'order')

    def __init__(self, title=None, order=None, keywords=None, searchable=None):
        self.title = title
        self.order = order
        self.keywords = keywords
        self.searchable = searchable

    def __setattr__(self, name, value):
        self.changed()
        return super().__setattr__(name, value)

    def join(self, data, attribute, separator=' '):
        return separator.join(s.strip() for s in (
            data[key] for key in getattr(self, attribute)
        ))

    def extract_title(self, data):
        assert self.title
        return self.join(data, 'title')

    def extract_order(self, data):
        assert self.order
        return normalize_for_url(self.join(data, 'order'))

    def extract_keywords(self, data):
        if self.keywords:
            keywords = set()

            for key in self.keywords:
                for value in collapse(data[key]):
                    if isinstance(value, str):
                        value = value.strip()

                    if value:
                        keywords.add(value)

            return keywords

    def extract_searchable_text(self, data):
        if self.searchable:
            return self.join(data, 'searchable')


DirectoryConfiguration.associate_with(DirectoryConfigurationStorage)
