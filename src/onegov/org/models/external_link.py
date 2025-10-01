from __future__ import annotations

from uuid import uuid4

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    ContentMixin, TimestampMixin, dict_property, meta_property)
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection
from onegov.reservation import ResourceCollection
from onegov.org.models import AccessExtension
from onegov.org.observer import observes
from onegov.search import SearchableContent
from sqlalchemy import Column, Text


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import Query, Session
    from typing import Self


class ExternalLink(Base, ContentMixin, TimestampMixin, AccessExtension,
                   SearchableContent):
    """
    An Object appearing in some other collection
    that features a lead and text but points to some external url.
    """

    __tablename__ = 'external_links'

    es_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'},
    }

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    title: Column[str] = Column(Text, nullable=False)
    url: Column[str] = Column(Text, nullable=False)
    page_image: dict_property[str | None] = meta_property()

    # The collection name this model should appear in
    member_of: Column[str | None] = Column(Text, nullable=True)
    # TODO: Stop passing title (and maybe even to) as url parameters.
    # Figure out a way to use the member_of attribute instead.
    group: Column[str | None] = Column(Text, nullable=True)

    #: The normalized title for sorting
    order: Column[str] = Column(Text, nullable=False, index=True)

    es_type_name = 'external_links'
    es_id = 'title'

    lead: dict_property[str | None] = meta_property()

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)


class ExternalLinkCollection(GenericCollection[ExternalLink]):

    supported_collections = {
        'form': FormCollection,
        'resource': ResourceCollection
    }

    def __init__(
        self,
        session: Session,
        member_of: str | None = None,
        group: str | None = None,
        type: str | None = None
    ):
        super().__init__(session)
        self.member_of = member_of
        self.group = group
        self.type = type

    @staticmethod
    def translatable_name(model_class: type[object]) -> str:
        """ Most collections have a base model whose name can be guessed
        from the collection name. """
        name = model_class.__name__.lower()
        name = name.replace('collection', '').rstrip('s')
        return f'{name.capitalize()}s'

    def form_choices(self) -> tuple[tuple[str, str], ...]:
        if self.type in self.supported_collections:
            collection = self.supported_collections[self.type]
            return (
                (collection.__name__, self.translatable_name(collection)),
            )
        else:
            return tuple(
                (m.__name__, self.translatable_name(m))
                for m in self.supported_collections.values()
            )

    @classmethod
    def collection_by_name(cls) -> dict[str, type[GenericCollection[Any]]]:
        return {m.__name__: m for m in cls.supported_collections.values()}

    @property
    def model_class(self) -> type[ExternalLink]:
        return ExternalLink

    @classmethod
    def target(
        cls,
        external_link: ExternalLink
    ) -> type[GenericCollection[Any]]:
        assert external_link.member_of is not None
        return cls.collection_by_name()[external_link.member_of]

    def query(self) -> Query[ExternalLink]:
        query = super().query()
        if self.member_of:
            query = query.filter_by(member_of=self.member_of)
        if self.group:
            query = query.filter_by(group=self.group)
        return query

    @classmethod
    def for_model(
        cls,
        session: Session,
        model_class: type[FormCollection | ResourceCollection],
        **kwargs: Any
    ) -> Self:
        """ It would be better to use the tablename, but the collections do
        not always implement the property model_class. """

        assert model_class in cls.supported_collections.values()
        return cls(session, member_of=model_class.__name__, **kwargs)
