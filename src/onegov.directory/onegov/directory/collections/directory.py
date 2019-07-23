from onegov.core.collection import GenericCollection
from onegov.core.utils import normalize_for_url, increment_name
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

        kwargs['name'] = self.unique_name(kwargs['title'])

        if 'configuration' not in kwargs:
            kwargs['configuration'] = DirectoryConfiguration()

        elif isinstance(kwargs['configuration'], str):
            kwargs['configuration'] = DirectoryConfiguration.from_yaml(
                kwargs['configuration']
            )

        return super().add(**kwargs)

    def unique_name(self, title):
        names = {n.name for n in self.session.query(self.model_class.name)}
        name = normalize_for_url(title)

        # add an upper limit to how many times increment_name can fail
        # to find a suitable name
        for _ in range(0, 100):
            if name not in names:
                return name

            name = increment_name(name)

        raise RuntimeError("Increment name failed to find a candidate")

    def by_name(self, name):
        return self.query().filter_by(name=name).first()
