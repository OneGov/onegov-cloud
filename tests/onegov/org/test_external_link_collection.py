from __future__ import annotations

from onegov.org.models.external_link import (
    ExternalLink,
    ExternalLinkCollection,
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_form_choices(session: Session) -> None:
    specific = ExternalLinkCollection(session, type='form')
    assert specific.form_choices() == (('FormCollection', 'Forms'),)

    everything = ExternalLinkCollection(session)
    assert set(everything.form_choices()) == {
        ('FormCollection', 'Forms'),
        ('ResourceCollection', 'Resources'),
    }


def test_query_group_filter(session: Session) -> None:
    grouped = ExternalLinkCollection(session, group='A')
    # exercises the group filter branch (empty db)
    assert grouped.query().count() == 0


def test_model_class_polymorphic(session: Session) -> None:
    assert ExternalLinkCollection(session).model_class is ExternalLink
    # a member_of selects the matching polymorphic subclass
    subclass = ExternalLinkCollection(session, member_of='form').model_class
    assert issubclass(subclass, ExternalLink)
