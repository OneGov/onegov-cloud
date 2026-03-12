from __future__ import annotations

from datetime import date
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.forms import ArchiveSearchFormElection
from onegov.election_day.forms import ArchiveSearchFormVote
from tests.onegov.election_day.common import DummyApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_apply_model_archive_search_form_election(session: Session) -> None:
    archive = SearchableArchivedResultCollection(DummyApp(session))  # type: ignore[arg-type]
    archive.term = 'xxx'
    archive.from_date = date(2222, 1, 1)
    archive.to_date = date(2222, 1, 1)
    archive.answers = ['accepted']
    archive.domains = ['region', 'municipality']

    form = ArchiveSearchFormElection()
    form.apply_model(archive)
    assert form.term.data == archive.term
    assert form.from_date.data == archive.from_date
    assert form.to_date.data == archive.to_date
    assert form.domains.data == archive.domains

def test_apply_model_archive_search_form_vote(session: Session) -> None:
    archive = SearchableArchivedResultCollection(DummyApp(session))  # type: ignore[arg-type]
    archive.term = 'xxx'
    archive.from_date = date(2222, 1, 1)
    archive.to_date = date(2222, 1, 1)
    archive.answers = ['accepted']
    archive.domains = ['region', 'municipality']

    form = ArchiveSearchFormVote()
    form.apply_model(archive)
    assert form.term.data == archive.term
    assert form.from_date.data == archive.from_date
    assert form.to_date.data == archive.to_date
    assert form.answers.data == archive.answers
    assert form.domains.data == archive.domains
