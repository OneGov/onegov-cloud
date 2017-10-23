import yaml

from more_itertools import collapse
from onegov.core import custom_json as json
from onegov.core.utils import normalize_for_url, safe_format
from onegov.form.utils import label_to_field_id
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy_utils.types.scalar_coercible import ScalarCoercible


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
        return cls(**yaml.load(text))


class DirectoryConfiguration(Mutable, StoredConfiguration):

    fields = ('title', 'lead', 'order', 'keywords', 'searchable', 'display')

    def __init__(self, title=None, lead=None, order=None, keywords=None,
                 searchable=None, display=None):
        self.title = title
        self.lead = lead
        self.order = order
        self.keywords = keywords
        self.searchable = searchable
        self.display = display

    def __setattr__(self, name, value):
        self.changed()
        return super().__setattr__(name, value)

    def rename_field(self, old_name, new_name):
        for field in self.fields:
            lst = getattr(self, field)

            for ix, name in enumerate(lst):
                lst[ix] = new_name if name == old_name else name

            setattr(self, field, lst)

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, Mutable):
            raise TypeError()
        else:
            return value

    def join(self, data, attribute, separator=' '):
        return separator.join((s and str(s).strip() or '') for s in (
            data[key] for key in getattr(self, attribute)
        ))

    def extract_title(self, data):
        return safe_format(self.title, data, adapt=label_to_field_id)

    def extract_lead(self, data):
        if self.lead:
            return safe_format(self.lead, data, adapt=label_to_field_id)

    def extract_order(self, data):
        # by default we use the title as order
        attribute = (
            (self.order and 'order') or
            (self.title and 'title')
        )
        return normalize_for_url(self.join(data, attribute))

    def extract_searchable(self, data):
        if self.searchable:
            return self.join(data, 'searchable')

    def extract_keywords(self, data):
        if self.keywords:
            keywords = set()

            for key in self.keywords:
                for value in collapse(data[key]):
                    if isinstance(value, str):
                        value = value.strip()

                    if value:
                        keywords.add(':'.join((key, value)))

            return keywords


DirectoryConfiguration.associate_with(DirectoryConfigurationStorage)
