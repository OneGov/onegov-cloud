from datetime import date
from onegov.election_day.layouts import MailLayout
from onegov.election_day.models import Election
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest


def test_mail_layout_model_title(session):
    layout = MailLayout(None, DummyRequest())
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

    layout = MailLayout(None, DummyRequest(locale='fr_CH'))
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


def test_mail_layout_optout(session):
    layout = MailLayout(None, DummyRequest())
    assert layout.optout_link == 'DummyPrincipal/unsubscribe-email'


def test_mail_layout_subject(session):
    # Note: the dummy setup does not translate the strings

    vote = Vote(
        title_translations={'de_CH': 'DE', 'fr_CH': 'FR'},
        date=date(2020, 1, 1),
        domain='federation'
    )
    session.add(vote)
    session.flush()

    layout = MailLayout(None, DummyRequest(locale='de_CH'))
    assert layout.subject(vote) == 'DE - New intermediate results'

    layout = MailLayout(None, DummyRequest(locale='fr_CH'))
    assert layout.subject(vote) == 'FR - New intermediate results'

    vote.status = 'final'
    assert layout.subject(vote) == 'FR - Final results'
