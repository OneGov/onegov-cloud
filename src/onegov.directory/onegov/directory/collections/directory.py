from onegov.core.collection import GenericCollection
from onegov.directory.models import Directory
from onegov.directory.types import DirectoryConfiguration


class DirectoryCollection(GenericCollection):

    def __init__(self, session, type='*'):
        super().__init__(session)
        self.type = type

    @property
    def model_class(self):
        return Directory.get_polymorphic_class(self.type, Directory)

    def add(self, **kwargs):
        if self.type != '*':
            kwargs.setdefault('type', self.type)

        if 'configuration' not in kwargs:
            kwargs['configuration'] = DirectoryConfiguration()

        elif isinstance(kwargs['configuration'], str):
            kwargs['configuration'] = DirectoryConfiguration.from_yaml(
                kwargs['configuration']
            )

        return super().add(**kwargs)

    def by_name(self, name):
        return self.query().filter_by(name=name).first()
