from __future__ import annotations

from onegov.agency.models import ExtendedAgency
from onegov.agency.utils import filter_modified_or_created
from onegov.core.collection import GenericCollection, Pagination
from onegov.core.orm.abstract import AdjacencyListCollection
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import undefer


from typing import Literal, Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from datetime import datetime
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import TypedDict
    from typing_extensions import Unpack

    class FilterParams(TypedDict, total=False):
        title: str | None
        updated_gt: datetime | str | None
        updated_ge: datetime | str | None
        updated_eq: datetime | str | None
        updated_le: datetime | str | None
        updated_lt: datetime | str | None


class ExtendedAgencyCollection(AdjacencyListCollection[ExtendedAgency]):

    __listclass__ = ExtendedAgency

    # Used to create link for root pdf based on timestamp
    def __init__(
        self,
        session: Session,
        # FIXME: These really should be float/int, we just need to add
        #        convertes to the path configuration...
        root_pdf_modified: str | None = None,
        browse: str | None = None
    ) -> None:
        super().__init__(session)
        self.root_pdf_modified = root_pdf_modified
        self.browse = browse


class PaginatedAgencyCollection(
    GenericCollection[ExtendedAgency],
    Pagination[ExtendedAgency]
):

    def __init__(
        self,
        session: Session,
        page: int = 0,
        parent: str | Literal[False] | None = None,
        exclude_hidden: bool = True,
        joinedload: Collection[str] | None = None,
        title: str | None = None,
        updated_gt: datetime | str | None = None,
        updated_ge: datetime | str | None = None,
        updated_eq: datetime | str | None = None,
        updated_le: datetime | str | None = None,
        updated_lt: datetime | str | None = None,
        undefer: Collection[str] | None = None
    ) -> None:

        super().__init__(session)
        self.page = page
        # filter keywords
        self.parent = parent
        self.title = title
        self.updated_gt = updated_gt
        self.updated_ge = updated_ge
        self.updated_eq = updated_eq
        self.updated_le = updated_le
        self.updated_lt = updated_lt
        # end filter keywords
        self.exclude_hidden = exclude_hidden
        self.joinedload = joinedload or []
        self.undefer = undefer or []

    @property
    def model_class(self) -> type[ExtendedAgency]:
        return ExtendedAgency

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and other.page == self.page
            and other.parent == self.parent
        )

    def subset(self) -> Query[ExtendedAgency]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            title=self.title,
            updated_gt=self.updated_gt,
            updated_ge=self.updated_ge,
            updated_eq=self.updated_eq,
            updated_le=self.updated_le,
            updated_lt=self.updated_lt,
        )

    def for_filter(self, **kwargs: Unpack[FilterParams]) -> Self:
        return self.__class__(
            session=self.session,
            title=kwargs.get('title', self.title),
            updated_gt=kwargs.get('updated_gt', self.updated_gt),
            updated_ge=kwargs.get('updated_ge', self.updated_ge),
            updated_eq=kwargs.get('updated_eq', self.updated_eq),
            updated_le=kwargs.get('updated_le', self.updated_le),
            updated_lt=kwargs.get('updated_lt', self.updated_lt),
        )

    def query(self) -> Query[ExtendedAgency]:
        query = super().query()

        for attribute in self.undefer:
            query = query.options(
                undefer(getattr(ExtendedAgency, attribute))
            )

        for attribute in self.joinedload:
            query = query.options(
                joinedload(getattr(ExtendedAgency, attribute))
            )

        if self.exclude_hidden:
            query = query.filter(
                or_(
                    ExtendedAgency.meta['access'] == 'public',
                    ExtendedAgency.meta['access'] == None,
                ),
                ExtendedAgency.published.is_(True)
            )

        if self.parent is False:
            query = query.filter(ExtendedAgency.parent_id == None)
        elif self.parent:
            query = query.filter(ExtendedAgency.parent_id == self.parent)

        if self.title:
            # if multiple words in search filter for title we 'or' link
            # them using ilike
            query = query.filter(or_(*(
                func.lower(
                    func.unaccent(ExtendedAgency.title)
                ).ilike(f'%{element}%') for element in self.title.split()
            )))
        if self.updated_gt:
            query = filter_modified_or_created(query, '>', self.updated_gt,
                                               ExtendedAgency)
        if self.updated_ge:
            query = filter_modified_or_created(query, '>=', self.updated_ge,
                                               ExtendedAgency)
        if self.updated_eq:
            query = filter_modified_or_created(query, '==', self.updated_eq,
                                               ExtendedAgency)
        if self.updated_le:
            query = filter_modified_or_created(query, '<=', self.updated_le,
                                               ExtendedAgency)
        if self.updated_lt:
            query = filter_modified_or_created(query, '<', self.updated_lt,
                                               ExtendedAgency)
        return query
