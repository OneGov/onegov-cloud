from __future__ import annotations

from uuid import uuid4

from onegov.chat.models.message import associated
from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    ContentMixin, TimestampMixin, content_property, dict_property)
from onegov.core.orm.mixins.content import dict_markup_property
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.file import AssociatedFiles, File, SearchableFile
from onegov.form import FormCollection
from onegov.org.observer import observes
from onegov.reservation import ResourceCollection
from onegov.org.models import AccessExtension
from onegov.search import SearchableContent
from sqlalchemy import Column, Text


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import Query, Session


class DocumentFormFile(File, SearchableFile):

    __mapper_args__ = {'polymorphic_identity': 'document_form_file'}

    es_type_name = 'document_form_file'

    @property
    def es_public(self) -> bool:
        return True


class FormDocument(Base, ContentMixin, TimestampMixin, AccessExtension,
                   SearchableContent, AssociatedFiles):

    __tablename__ = 'form_documents'

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
    }

    #: An internal id for references (not public)
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: A nice id for the url, readable by humans
    name: Column[str] = Column(Text, nullable=False, unique=True)

    title: Column[str] = Column(Text, nullable=False)

    #: Describes the document briefly
    lead: dict_property[str | None] = meta_property()

    #: Describes the document in detail
    text = dict_markup_property('content')

    pdf = associated(
        DocumentFormFile, 'pdf', 'one-to-one', uselist=False,
        backref_suffix='pdf')

    # The collection name this model should appear in
    member_of: Column[str | None] = Column(Text, nullable=True)

    group: Column[str | None] = Column(Text, nullable=True)

    #: The normalized title for sorting
    order: Column[str] = Column(Text, nullable=False, index=True)

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)

    es_type_name = 'document_pages'
    es_id = 'title'


class FormDocumentCollection(GenericCollection[FormDocument]):

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

    def by_name(self, name: str) -> FormDocument | None:
        """ Returns the given form by name or None. """
        return self.query().filter(FormDocument.name == name).first()

    @classmethod
    def collection_by_name(cls) -> dict[str, type[GenericCollection[Any]]]:
        return {m.__name__: m for m in cls.supported_collections.values()}

    @property
    def model_class(self) -> type[FormDocument]:
        return FormDocument

    @classmethod
    def target(
        cls,
        external_link: FormDocument
    ) -> type[GenericCollection[Any]]:
        assert external_link.member_of is not None
        return cls.collection_by_name()[external_link.member_of]

    def query(self) -> Query[FormDocument]:
        return self.session.query(FormDocument)
