from __future__ import annotations

from onegov.form import FormCollection
from onegov.org.models.document_form import (
    FormDocument,
    FormDocumentCollection,
)
from onegov.reservation import ResourceCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_translatable_name() -> None:
    assert FormDocumentCollection.translatable_name(FormCollection) == 'Forms'
    assert FormDocumentCollection.translatable_name(
        ResourceCollection) == 'Resources'


def test_collection_by_name() -> None:
    mapping = FormDocumentCollection.collection_by_name()
    assert mapping == {
        'FormCollection': FormCollection,
        'ResourceCollection': ResourceCollection,
    }


def test_form_choices(session: Session) -> None:
    # a specific type yields only that collection
    specific = FormDocumentCollection(session, type='form')
    assert specific.form_choices() == (('FormCollection', 'Forms'),)

    # no type yields all supported collections
    everything = FormDocumentCollection(session)
    assert set(everything.form_choices()) == {
        ('FormCollection', 'Forms'),
        ('ResourceCollection', 'Resources'),
    }


def test_target() -> None:
    document = FormDocument(title='x', member_of='FormCollection')
    assert FormDocumentCollection.target(document).__name__ == 'FormCollection'
