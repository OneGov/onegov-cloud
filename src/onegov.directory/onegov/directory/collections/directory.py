from onegov.core.collection import GenericCollection
from onegov.directory.models import Directory


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
        return super().add(**kwargs)
