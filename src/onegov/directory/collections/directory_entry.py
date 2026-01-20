from __future__ import annotations

from itertools import groupby
from onegov.core.collection import GenericCollection, Pagination
from onegov.core.utils import toggle
from onegov.directory.models import DirectoryEntry
from onegov.form import as_internal_id
from sqlalchemy import and_, desc
from sqlalchemy.orm import object_session
from sqlalchemy.dialects.postgresql import array


from typing import overload, Any, Literal, Protocol, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Iterable, Mapping
    from markupsafe import Markup
    from onegov.directory.models import Directory
    from sqlalchemy.orm import Query
    from typing import Self


T = TypeVar('T')
DirectoryEntryT = TypeVar('DirectoryEntryT', bound=DirectoryEntry)


class DirectorySearchWidget(Protocol[DirectoryEntryT]):
    @property
    def name(self) -> str: ...
    @property
    def search_query(self) -> Query[DirectoryEntryT]: ...

    def adapt(
        self,
        query: Query[DirectoryEntryT]
    ) -> Query[DirectoryEntryT]: ...

    def html(self, layout: Any) -> Markup: ...


class DirectoryEntryCollection(
    GenericCollection[DirectoryEntryT],
    Pagination[DirectoryEntryT]
):
    """ Provides a view on a directory's entries.

    The directory itself might be a natural place for lots of these methods
    to reside, but ultimately we want to avoid mixing the concerns of the
    directory model and this view-supporting collection.

    """

    @overload
    def __init__(
        self: DirectoryEntryCollection[DirectoryEntry],
        directory: Directory,
        type: Literal['*', 'generic'] = '*',
        keywords: Mapping[str, list[str]] | None = None,
        page: int = 0,
        search_widget: DirectorySearchWidget[DirectoryEntryT] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        directory: Directory,
        type: str,
        keywords: Mapping[str, list[str]] | None = None,
        page: int = 0,
        search_widget: DirectorySearchWidget[DirectoryEntryT] | None = None,
    ) -> None: ...

    def __init__(
        self,
        directory: Directory,
        type: str = '*',
        keywords: Mapping[str, list[str]] | None = None,
        page: int = 0,
        search_widget: DirectorySearchWidget[DirectoryEntryT] | None = None,
    ) -> None:

        super().__init__(object_session(directory))
        self.type = type
        self.directory = directory
        self.keywords = keywords or {}
        self.page = page
        self.search_widget = search_widget

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.type == other.type
            and self.page == other.page
        )

    def subset(self) -> Query[DirectoryEntryT]:
        return self.query()

    @property
    def search(self) -> str | None:
        if self.search_widget is None:
            return None

        return self.search_widget.name

    @property
    def search_query(self) -> Query[DirectoryEntryT] | None:
        if self.search_widget is None:
            return None

        return self.search_widget.search_query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.directory,
            self.type,
            self.keywords,
            page=index,
        )

    def by_name(self, name: str) -> DirectoryEntryT | None:
        return self.query().filter_by(name=name).first()

    def query(self) -> Query[DirectoryEntryT]:
        cls = self.model_class

        query = super().query().filter_by(directory_id=self.directory.id)
        keywords = self.valid_keywords(self.keywords)

        def keyword_group(value: str) -> str:
            return value.split(':')[0]

        values = [
            f'{keyword}:{value}'
            for keyword in keywords
            for value in keywords[keyword]
        ]
        values.sort(key=keyword_group)

        values = [
            cls._keywords.has_any(array(group_values))  # type:ignore
            for group, group_values in groupby(values, key=keyword_group)
        ]
        if values:
            query = query.filter(and_(*values))

        if self.directory.configuration.direction == 'desc':
            query = query.order_by(desc(cls.order))
        else:
            query = query.order_by(cls.order)

        if self.search_widget is not None:
            query = self.search_widget.adapt(query)

        return query

    def valid_keywords(
        self,
        parameters: Mapping[str, T]
    ) -> dict[str, T]:

        valid_keywords = {
            as_internal_id(kw)
            for kw in self.directory.configuration.keywords or ()
        }
        return {
            k_id: v
            for k, v in parameters.items()
            if (k_id := as_internal_id(k)) in valid_keywords
        }

    @property
    def directory_name(self) -> str:
        return self.directory.name

    @property
    def model_class(self) -> type[DirectoryEntryT]:
        return DirectoryEntry.get_polymorphic_class(  # type:ignore
            self.type,
            DirectoryEntry  # type:ignore[arg-type]
        )

    def available_filters(
        self,
        sort_choices: bool = False,
        sortfunc: Callable[[str], SupportsRichComparison] | None = None
    ) -> Iterable[tuple[str, str, list[str]]]:
        """ Retrieve the filters with their choices.

        By default the choices are returned in the same order as defined in the
        structrue. To filter alphabetically, set `sort_choices=True`.
        """

        keywords = tuple(
            as_internal_id(k)
            for k in self.directory.configuration.keywords or ()
        )
        fields = {
            f.id: f
            for f in self.directory.fields
            if f.id in keywords and (
                f.type == 'radio'
                or f.type == 'checkbox'
            )
        }

        def maybe_sorted(values: Iterable[str]) -> list[str]:
            if not sort_choices:
                return list(values)
            return sorted(values, key=sortfunc)

        return (
            (k, f.label, maybe_sorted(c.label for c in f.choices))
            for k in keywords if hasattr((f := fields[k]), 'choices')
        )

    def for_keywords(
        self,
        singular: bool = False,
        **keywords: list[str]
    ) -> Self:

        if not self.directory.configuration.keywords:
            return self

        return self.__class__(
            directory=self.directory,
            type=self.type,
            search_widget=self.search_widget,
            keywords=keywords,
        )

    def for_toggled_keyword_value(
        self,
        keyword: str,
        value: str,
        singular: bool = False,
    ) -> Self:

        if not self.directory.configuration.keywords:
            return self

        parameters = dict(self.keywords)

        collection = set(parameters.get(keyword, []))

        if singular:
            collection = set() if value in collection else {value}
        else:
            collection = toggle(collection, value)

        if collection:
            parameters[keyword] = list(collection)
        elif keyword in parameters:
            del parameters[keyword]

        return self.__class__(
            directory=self.directory,
            type=self.type,
            search_widget=self.search_widget,
            keywords=parameters,
        )

    def without_keywords(self) -> Self:
        return self.__class__(
            directory=self.directory,
            type=self.type,
            page=self.page,
            search_widget=self.search_widget,
        )
