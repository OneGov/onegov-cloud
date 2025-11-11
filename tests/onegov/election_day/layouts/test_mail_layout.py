from __future__ import annotations

from datetime import date
from onegov.election_day.layouts import MailLayout
from onegov.election_day.models import Election
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_mail_layout_model_title(session: Session) -> None:
    layout = MailLayout(None, DummyRequest())  # type: ignore[arg-type]
    assert layout.model_title(Vote()) is None
    assert layout.model_title(Vote(title='Test')) == 'Test'
    assert layout.model_title(
        Vote(title_translations={'de_CH': 'DE', 'rm_CH': 'RM'})
    ) == 'DE'
    assert layout.model_title(
        Vote(title_translations={'fr_CH': 'FR', 'rm_CH': 'RM'})
    ) is None
    assert layout.model_title(Election()) is None
    assert layout.model_title(Election(title='Test')) == 'Test'
    assert layout.model_title(
        Election(title_translations={'de_CH': 'DE', 'rm_CH': 'RM'})
    ) == 'DE'
    assert layout.model_title(
        Election(title_translations={'fr_CH': 'FR', 'rm_CH': 'RM'})
    ) is None

    layout = MailLayout(None, DummyRequest(locale='fr_CH'))  # type: ignore[arg-type]
    assert layout.model_title(
        Vote(title_translations={'fr_CH': 'FR', 'de_CH': 'DE'})
    ) == 'FR'
    assert layout.model_title(
        Vote(title_translations={'it_CH': 'FR', 'de_CH': 'DE'})
    ) == 'DE'
    assert layout.model_title(
        Election(title_translations={'fr_CH': 'FR', 'de_CH': 'DE'})
    ) == 'FR'
    assert layout.model_title(
        Election(title_translations={'it_CH': 'FR', 'de_CH': 'DE'})
    ) == 'DE'


def test_mail_layout_optout(session: Session) -> None:
    layout = MailLayout(None, DummyRequest())  # type: ignore[arg-type]
    assert layout.optout_link == 'DummyPrincipal/unsubscribe-email'


def test_mail_layout_subject(session: Session) -> None:
    # Note: the dummy setup does not translate the strings

    vote = Vote(
        title_translations={'de_CH': 'DE', 'fr_CH': 'FR'},
        date=date(2020, 1, 1),
        domain='federation'
    )
    session.add(vote)
    session.flush()

    layout = MailLayout(None, DummyRequest(locale='de_CH'))  # type: ignore[arg-type]
    assert layout.subject(vote) == 'DE - New intermediate results'

    layout = MailLayout(None, DummyRequest(locale='fr_CH'))  # type: ignore[arg-type]
    assert layout.subject(vote) == 'FR - New intermediate results'

    vote.status = 'final'
    assert layout.subject(vote) == 'FR - Final results'
