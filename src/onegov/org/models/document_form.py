from __future__ import annotations

from uuid import uuid4

from onegov.chat.models.message import associated
from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    ContentMixin, TimestampMixin, dict_property, content_property,
    meta_property)
from onegov.core.orm.mixins.content import dict_markup_property
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.file import File, MultiAssociatedFiles
from onegov.form import FormCollection
from onegov.org.i18n import _
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.observer import observes
from onegov.reservation import ResourceCollection
from onegov.org.models import (AccessExtension, ContactExtension,
                               CoordinatesExtension, GeneralFileLinkExtension,
                               HoneyPotExtension)
from onegov.search import SearchableContent
from sqlalchemy import Column, Text


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import Query, Session


class DocumentFormFile(File):

    __mapper_args__ = {'polymorphic_identity': 'document_form_file'}


class FormDocument(Base, ContentMixin, TimestampMixin, AccessExtension,
                   SearchableContent, MultiAssociatedFiles,
                   ContactExtension, PersonLinkExtension,
                   HoneyPotExtension, CoordinatesExtension,
                   GeneralFileLinkExtension):

    __tablename__ = 'form_documents'

    fts_type_title = _('Forms')
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'},
        'pdf_extract': {'type': 'localized', 'weight': 'C'},
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

    pdf_extract: dict_property[str | None] = content_property()

    @observes('pdf')
    def pdf_observer(self, pdf: DocumentFormFile | None) -> None:
        self.pdf_extract = pdf.extract if pdf is not None else None

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)


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
