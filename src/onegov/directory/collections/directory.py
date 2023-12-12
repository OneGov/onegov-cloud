from onegov.core.collection import GenericCollection
from onegov.core.utils import normalize_for_url, increment_name
from onegov.directory.models import Directory
from onegov.directory.types import DirectoryConfiguration


from typing import overload, Any, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session


DirectoryT = TypeVar('DirectoryT', bound=Directory)


class DirectoryCollection(GenericCollection[DirectoryT]):

    @overload
    def __init__(
        self: 'DirectoryCollection[Directory]',
        session: 'Session',
        type: Literal['*', 'generic'] = '*'
    ) -> None: ...

    @overload
    def __init__(self, session: 'Session', type: str) -> None: ...

    def __init__(self, session: 'Session', type: str = '*') -> None:
        super().__init__(session)
        self.type = type

    @property
    def model_class(self) -> type[DirectoryT]:
        return Directory.get_polymorphic_class(  # type:ignore[return-value]
            self.type,
            Directory  # type:ignore[arg-type]
        )

    def query(self) -> 'Query[DirectoryT]':
        return super().query().order_by(self.model_class.order)

    def add(self, **kwargs: Any) -> DirectoryT:
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

    def unique_name(self, title: str) -> str:
        names = {n for n, in self.session.query(self.model_class.name)}
        name = normalize_for_url(title)

        # add an upper limit to how many times increment_name can fail
        # to find a suitable name
        for _ in range(0, 100):
            if name not in names:
                return name

            name = increment_name(name)

        raise RuntimeError("Increment name failed to find a candidate")

    def by_name(self, name: str) -> DirectoryT | None:
        return self.query().filter_by(name=name).first()
