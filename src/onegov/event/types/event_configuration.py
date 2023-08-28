from onegov.directory.types.directory_configuration import \
    DirectoryConfiguration
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy_utils.types.scalar_coercible import ScalarCoercible


class EventConfigurationStorage(TypeDecorator, ScalarCoercible):

    impl = TEXT

    @property
    def python_type(self):
        return EventConfiguration

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.to_json()

    def process_result_value(self, value, dialect):
        if value is not None:
            return EventConfiguration.from_json(value)


class EventConfiguration(DirectoryConfiguration):

    fields = (
        'title',
        'order',
        'keywords',
    )

    def __init__(self, title=None, order=None, keywords=None, **kwargs):

        self.title = title
        self.order = order
        self.keywords = keywords


EventConfiguration.associate_with(EventConfigurationStorage)
