from __future__ import annotations

from datetime import date
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_import_ech_vote_gr(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # The datasets contain empty and intermediate results from the 3.3.2024
    # two federal and 4 communal votes, one of these 4 is a complex vote.

    results = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='votes-invalid-year'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert errors
    assert errors[0].error == 'Cannot import votes. Year 2084 does not exist.'

    results = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='votes-empty'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 6
    assert not deleted

    # ... test complex communal
    vote = next(u for u in updated if getattr(u, 'type', '') == 'complex')
    assert isinstance(vote, ComplexVote)
    assert vote.domain == 'municipality'
    assert vote.id == 'ipq52'
    assert vote.external_id == 'IPQ52'
    assert vote.date == date(2024, 3, 3)
    assert vote.progress == (0, 1)
    assert vote.has_results is False
    assert vote.title_translations['de_CH'] == (
        'Variante a) zur Totalrevison der Gemeindeverfassung: alle '
        'Angestellten der Gemeinde können nicht Mitglied des Gemeinderates '
        'sein'
    )
    assert vote.counter_proposal.title_translations is not None
    assert vote.counter_proposal.title_translations['de_CH'] == (
        'Variante b) zur Totalrevision der Gemeindeverfassung: nur leitende '
        'Angestellte können nicht Mitglied des Gemeinderates sein'
    )
    assert vote.tie_breaker.title_translations is not None
    assert vote.tie_breaker.title_translations['de_CH'] == (
        'Falls Variante a) und Variante b) angenommen werden, welche Regelung '
        'soll in Kraft treten.'
    )

    # ... test simple federal
    vote = next(u for u in updated if u.id == 'ipq50')
    assert isinstance(vote, Vote)
    assert vote.domain == 'federation'
    assert vote.id == 'ipq50'
    assert vote.external_id == 'IPQ50'
    assert vote.date == date(2024, 3, 3)
    assert vote.progress == (0, 101)
    assert vote.has_results is False
    assert vote.title_translations == {
        'de_CH': (
            'Volksinitiative «Für ein besseres Leben im Alter (Initiative '
            'für eine 13. AHV-Rente)»'
        ),
        'fr_CH': (
            'Initiative populaire «Mieux vivre à la retraite (initiative '
            'pour une 13e rente AVS)»'
        ),
        'it_CH': (
            'Iniziativa popolare «Vivere meglio la pensione (Iniziativa '
            'per una 13esima mensilità AVS)»'
        ),
        'rm_CH': (
            'Iniziativa dal pievel «Viver meglier en la pensiun (Iniziativa '
            'per ina 13avla renta da la AVS)»'
        )
    }
    assert vote.short_title_translations == {
        'de_CH': 'Initiative für eine 13. AHV-Rente',
        'fr_CH': 'Initiative pour une 13e rente AVS',
        'it_CH': 'Iniziativa per una 13esima mensilità AVS',
        'rm_CH': 'Iniziativa per ina 13avla renta da la AVS'
    }

    # re-import
    results = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='votes-empty'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 6
    assert not deleted

    # import of results
    results = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='votes-intermediate'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 6
    assert not deleted

    # ... test complex communal
    vote = next(u for u in updated if getattr(u, 'type', '') == 'complex')
    assert isinstance(vote, ComplexVote)
    assert vote.progress == (1, 1)
    assert vote.counted is True
    assert vote.answer == 'counter-proposal'
    assert vote.counter_proposal.eligible_voters == 5082
    assert vote.counter_proposal.cast_ballots == 1319
    assert vote.counter_proposal.yeas == 660

    # ... test simple federal
    vote = next(u for u in updated if u.id == 'ipq50')
    assert isinstance(vote, Vote)
    assert vote.progress == (7, 101)
    assert vote.counted is False
    assert vote.answer is None
    assert vote.eligible_voters == 19188
    assert vote.cast_ballots == 11855
    assert vote.yeas == 8457

    # re-import of results
    results = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='votes-intermediate'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 6
    assert not deleted

    # test removing items and clearing results
    session.add(
        Vote(
            date=date(2024, 3, 3),
            id='remove',
            domain='canton',
            title_translations={'de_CH': 'remove'}
        )
    )
    session.add(
        Vote(
            date=date(2024, 1, 1),
            id='keep',
            domain='canton',
            title_translations={'de_CH': 'keep'}
        )
    )
    session.flush()

    # ... vote on the same day marked for deletion
    results = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='votes-empty'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 6
    assert len(deleted) == 1
    assert list(deleted)[0].id == 'remove'

    # ... test complex communal
    vote = next(u for u in updated if getattr(u, 'type', '') == 'complex')
    assert isinstance(vote, ComplexVote)
    assert vote.progress == (0, 1)
    assert vote.counted is False
    assert vote.answer is None
    assert vote.counter_proposal.eligible_voters == 0
    assert vote.counter_proposal.cast_ballots == 0
    assert vote.counter_proposal.yeas == 0

    # ... test simple federal
    vote = next(u for u in updated if u.id == 'ipq50')
    assert isinstance(vote, Vote)
    assert vote.progress == (0, 101)
    assert vote.counted is False
    assert vote.answer is None
    assert vote.eligible_voters == 0
    assert vote.cast_ballots == 0
    assert vote.yeas == 0
