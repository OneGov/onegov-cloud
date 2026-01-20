from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timezone
from freezegun import freeze_time
from onegov.core.custom import json
from onegov.election_day.models import BallotResult
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import EmailNotification
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import List
from onegov.election_day.models import ListResult
from onegov.election_day.models import Notification
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import Vote
from onegov.election_day.models import WebhookNotification
from pytest import raises
from tests.onegov.election_day.common import DummyRequest
from time import sleep
from unittest.mock import Mock
from unittest.mock import patch
from unittest.mock import PropertyMock
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def test_notification_generic(session: Session) -> None:
    notification = Notification()
    notification.last_modified = datetime(
        2007, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    session.add(notification)
    session.flush()

    notification = session.query(Notification).one()
    assert notification.id
    assert notification.type == 'generic'
    assert notification.last_modified == datetime(
        2007, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert notification.election_id is None
    assert notification.election_compound_id is None
    assert notification.vote_id is None

    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        session.flush()
        election = session.query(Election).one()

        notification = Notification()
        notification.update_from_model(election)
        session.add(notification)
        session.flush()
        assert notification.election_id == election.id
        assert notification.vote_id is None
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )

    with freeze_time("2010-01-01 00:00"):
        session.add(
            ElectionCompound(
                title="Elections",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        session.flush()
        election_compound = session.query(ElectionCompound).one()

        notification = Notification()
        notification.update_from_model(election_compound)
        session.add(notification)
        session.flush()
        assert notification.election_compound_id == election_compound.id
        assert notification.vote_id is None
        assert notification.last_modified == datetime(
            2010, 1, 1, 0, 0, tzinfo=timezone.utc
        )

    with freeze_time("2009-01-01 00:00"):
        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        session.flush()
        vote = session.query(Vote).one()

        notification = Notification()
        notification.update_from_model(vote)
        session.add(notification)
        session.flush()
        assert notification.election_id is None
        assert notification.vote_id == vote.id
        assert notification.last_modified == datetime(
            2009, 1, 1, 0, 0, tzinfo=timezone.utc
        )

    with raises(NotImplementedError):
        notification.trigger(DummyRequest(), election)  # type: ignore[arg-type]
    with raises(NotImplementedError):
        notification.trigger(DummyRequest(), election_compound)  # type: ignore[arg-type]
    with raises(NotImplementedError):
        notification.trigger(DummyRequest(), vote)  # type: ignore[arg-type]

    assert session.query(Notification).count() == 4
    session.query(Vote).delete()
    session.query(Election).delete()
    session.query(ElectionCompound).delete()
    assert session.query(Notification).count() == 1


def test_webhook_notification(session: Session) -> None:
    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        notification = WebhookNotification()
        notification.trigger(DummyRequest(), election)  # type: ignore[arg-type]

        assert notification.type == 'webhooks'
        assert notification.election_id == election.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )

        session.add(
            ElectionCompound(
                title="Elections",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election_compound = session.query(ElectionCompound).one()

        notification = WebhookNotification()
        notification.trigger(DummyRequest(), election_compound)  # type: ignore[arg-type]

        assert notification.type == 'webhooks'
        assert notification.election_compound_id == election_compound.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        notification.trigger(DummyRequest(), vote)  # type: ignore[arg-type]

        assert notification.type == 'webhooks'
        assert notification.vote_id == vote.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )

        with patch('urllib.request.urlopen') as urlopen:
            request: Any = DummyRequest()
            request.app.principal.webhooks = {'https://example.org/1': None}

            notification.trigger(request, election)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == str(len(data))

            assert json.loads(data.decode('utf-8')) == {
                'completed': False,
                'date': '2011-01-01',
                'domain': 'federation',
                'elected': [],
                'last_modified': '2008-01-01T00:00:00+00:00',
                'progress': {'counted': 0, 'total': 0},
                'title': {'de_CH': 'Election'},
                'type': 'election',
                'url': 'Election/election',
                'turnout': 0
            }

            notification.trigger(request, election_compound)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == str(len(data))

            assert json.loads(data.decode('utf-8')) == {
                'completed': False,
                'date': '2011-01-01',
                'domain': 'federation',
                'elected': [],
                'elections': [],
                'last_modified': '2008-01-01T00:00:00+00:00',
                'progress': {'counted': 0, 'total': 0},
                'title': {'de_CH': 'Elections'},
                'type': 'election_compound',
                'url': 'ElectionCompound/elections',
            }

            notification.trigger(request, vote)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == str(len(data))

            assert json.loads(data.decode('utf-8')) == {
                'answer': None,
                'completed': False,
                'date': '2011-01-01',
                'domain': 'federation',
                'last_modified': '2008-01-01T00:00:00+00:00',
                'nays_percentage': None,
                'progress': {'counted': 0.0, 'total': 0.0},
                'title': {'de_CH': 'Vote'},
                'type': 'vote',
                'url': 'Vote/vote',
                'yeas_percentage': None,
                'turnout': 0
            }


def test_email_notification_vote(
    election_day_app_zg: TestApp,
    session: Session
) -> None:

    with freeze_time("2008-01-01 00:00"):
        mock = Mock()
        election_day_app_zg.send_marketing_email_batch = mock  # type: ignore[method-assign]

        principal = election_day_app_zg.principal
        principal.email_notification = True
        election_day_app_zg.cache.set('principal', principal)

        session.add(
            Vote(
                title_translations={
                    'de_CH': "Abstimmung",
                    'fr_CH': "Vote",
                    'it_CH': "Votazione",
                    'rm_CH': "Votaziun"
                },
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        simple_vote = session.query(Vote).one()

        session.add(
            ComplexVote(  # type: ignore[misc]
                title_translations={
                    'de_CH': "Vorlage mit Gegenentwurf",
                    'fr_CH': "Vote avec contre-projet",
                    # 'it_CH' missing
                    'rm_CH': "Project cun cuntraproposta"
                },
                domain='municipality',
                domain_segment='Zug',
                date=date(2011, 1, 1),
            )
        )
        complex_vote = session.query(ComplexVote).one()

        request: Any = DummyRequest(
            app=election_day_app_zg,
            session=session,
            # Otherwise we will hit an assertion in send_mail
            # due to the escaping of the quotes
            avoid_quotes_in_url=True
        )

        for address, domain, domain_segment, locale, active in (
            ('de@examp.le', None, None, 'de_CH', True),
            ('fr@examp.le', None, None, 'fr_CH', True),
            ('it@examp.le', None, None, 'it_CH', True),
            ('rm@examp.le', None, None, 'rm_CH', True),
            ('xx@examp.le', None, None, 'de_CH', False),
            ('yy@examp.le', None, None, 'fr_CH', False),
            ('aa@examp.le', 'canton', None, 'de_CH', True),
            ('bb@examp.le', 'municipality', 'Zug', 'de_CH', True),
            ('cc@examp.le', 'municipality', 'Baar', 'de_CH', True)
        ):
            session.add(
                EmailSubscriber(
                    address=address,
                    domain=domain,
                    domain_segment=domain_segment,
                    locale=locale,
                    active=active
                )
            )

        # No results yet
        # ... simple
        notification = EmailNotification()
        notification.trigger(request, simple_vote)
        assert notification.type == 'email'
        assert notification.vote_id == simple_vote.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )
        assert mock.call_count == 1
        emails = list(mock.call_args.args[0])
        assert sorted(email['Subject'] for email in emails) == [
            'Abstimmung - Neue Zwischenresultate',
            'Abstimmung - Neue Zwischenresultate',
            'Votazione - Nuovi risultati provvisori',
            'Votaziun - Novs resultats intermediars',
            'Vote - Nouveaux résultats intermédiaires'
        ]
        assert sorted(email['To'] for email in emails) == [
            'aa@examp.le',
            'de@examp.le',
            'fr@examp.le',
            'it@examp.le',
            'rm@examp.le'
        ]
        assert {email['ReplyTo'] for email in emails} == {
            'Kanton Govikon <mails@govikon.ch>'
        }
        headers_per_email = [
            {h['Name']: h['Value'] for h in email['Headers']}
            for email in emails
        ]
        assert {
            headers['List-Unsubscribe-Post'] for headers in headers_per_email
        } == {'List-Unsubscribe=One-Click'}
        assert sorted(
            headers['List-Unsubscribe'] for headers in headers_per_email
        ) == [
            "<Principal/unsubscribe-email?opaque={address: aa@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: de@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: fr@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: it@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: rm@examp.le}>"
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

    with freeze_time("2008-01-01 01:00"):
        # ... complex
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, complex_vote)
        assert notification.type == 'email'
        assert notification.vote_id == complex_vote.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )
        assert mock.call_count == 1
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Project cun cuntraproposta - Novs resultats intermediars',
            'Vorlage mit Gegenentwurf - Neue Zwischenresultate',
            'Vorlage mit Gegenentwurf - Neue Zwischenresultate',
            'Vorlage mit Gegenentwurf - Nuovi risultati provvisori',
            'Vote avec contre-projet - Nouveaux résultats intermédiaires'
        ]
        assert sorted([email['To'] for email in emails]) == [
            'bb@examp.le',
            'de@examp.le',
            'fr@examp.le',
            'it@examp.le',
            'rm@examp.le'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

        # Intermediate results
        keys = [
            'entity_id', 'name', 'yeas', 'nays', 'eligible_voters', 'empty',
            'invalid', 'counted'
        ]
        for values in (
            (1711, 'Zug', 3821, 7405, 16516, 80, 1, True),
            (1706, 'Oberägeri', 811, 1298, 3560, 18, 0, True),
            (1709, 'Unterägeri', 1096, 2083, 5245, 18, 1, True),
            (1704, 'Menzingen', 599, 1171, 2917, 17, 0, True),
            (1701, 'Baar', 3049, 5111, 13828, 54, 3, True),
            (1702, 'Cham', 2190, 3347, 9687, 60, 0, True),
            (1703, 'Hünenberg', 1497, 2089, 5842, 15, 1, True),
            (1708, 'Steinhausen', 1211, 2350, 5989, 17, 0, True),
            (1707, 'Risch', 1302, 1779, 6068, 17, 0, True),
            (1710, 'Walchwil', 651, 743, 2016, 8, 0, False),
            (1705, 'Neuheim', 307, 522, 1289, 10, 1, False),
        ):
            kw = {key: values[index] for index, key in enumerate(keys)}
            simple_vote.proposal.results.append(BallotResult(**kw))
            complex_vote.proposal.results.append(BallotResult(**kw))
            complex_vote.counter_proposal.results.append(BallotResult(**kw))
            complex_vote.tie_breaker.results.append(BallotResult(**kw))

    with freeze_time("2008-01-01 02:00"):
        # ... simple
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, simple_vote)
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Abstimmung - Neue Zwischenresultate',
            'Abstimmung - Neue Zwischenresultate',
            'Votazione - Nuovi risultati provvisori',
            'Votaziun - Novs resultats intermediars',
            'Vote - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "9 da 11" in contents
        assert "9 di 11" in contents
        assert "9 de 11" in contents
        assert "9 von 11" in contents
        assert "37.21%" in contents
        assert "62.79%" in contents

        # ... complex
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, complex_vote)
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Project cun cuntraproposta - Novs resultats intermediars',
            'Vorlage mit Gegenentwurf - Neue Zwischenresultate',
            'Vorlage mit Gegenentwurf - Neue Zwischenresultate',
            'Vorlage mit Gegenentwurf - Nuovi risultati provvisori',
            'Vote avec contre-projet - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "9 da 11" in contents
        assert "9 di 11" in contents
        assert "9 de 11" in contents
        assert "9 von 11" in contents
        assert "37.21%" in contents
        assert "62.79%" in contents

        # Final results
        for result in simple_vote.proposal.results:
            result.counted = True
        for result in complex_vote.proposal.results:
            result.counted = True
        for result in complex_vote.counter_proposal.results:
            result.counted = True
        for result in complex_vote.tie_breaker.results:
            result.counted = True

    with freeze_time("2008-01-01 03:00"):
        # ... simple
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, simple_vote)
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Abstimmung - abgelehnt',
            'Abstimmung - abgelehnt',
            'Votazione - Respinto',
            'Votaziun - Refusà',
            'Vote - Refusé'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "37.21%" in contents
        assert "62.79%" in contents
        assert "61.34 %" in contents

    with freeze_time("2008-01-01 04:00"):
        # ... complex
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, complex_vote)
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Project cun cuntraproposta - Refusà',
            'Vorlage mit Gegenentwurf - Respinto',
            'Vorlage mit Gegenentwurf - abgelehnt',
            'Vorlage mit Gegenentwurf - abgelehnt',
            'Vote avec contre-projet - Refusé'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Refusà l'iniziativa e la cuntraproposta" in contents
        assert "Initiative et contre-projet rejetées" in contents
        assert "Iniziativa e controprogetto sono state rifiutate" in contents
        assert "Initative und Gegenentwurf abgelehnt" in contents
        assert "37.21%" in contents
        assert "62.79%" in contents
        assert "61.34 %" in contents


def test_email_notification_election(
    election_day_app_zg: TestApp,
    session: Session
) -> None:

    with freeze_time("2008-01-01 00:00"):
        mock = Mock()
        election_day_app_zg.send_marketing_email_batch = mock  # type: ignore[method-assign]

        principal = election_day_app_zg.principal
        principal.email_notification = True
        principal.reply_to = 'reply-to@example.org'
        election_day_app_zg.cache.set('principal', principal)

        session.add(
            Election(
                title_translations={
                    'de_CH': "Majorzwahl",
                    'fr_CH': "Election selon le système majoritaire",
                    'it_CH': "Elezione secondo il sistema maggioritario",
                    'rm_CH': "Elecziun da maiorz"
                },
                domain='federation',
                date=date(2011, 1, 1),
                number_of_mandates=1
            )
        )
        majorz = session.query(Election).one()

        session.add(
            ProporzElection(  # type: ignore[misc]
                title_translations={
                    'de_CH': "Proporzwahl",
                    'fr_CH': "Election selon le système proportionnel",
                    # 'it_CH' missing
                    'rm_CH': "Elecziun da proporz"
                },
                domain='municipality',
                domain_segment='Zug',
                date=date(2011, 1, 1),
                number_of_mandates=1
            )
        )
        proporz = session.query(ProporzElection).one()

        request: Any = DummyRequest(
            app=election_day_app_zg,
            session=session,
            # Otherwise we will hit an assertion in send_mail
            # due to the escaping of the quotes
            avoid_quotes_in_url=True
        )

        for address, domain, domain_segment, locale, active in (
            ('de@examp.le', None, None, 'de_CH', True),
            ('fr@examp.le', None, None, 'fr_CH', True),
            ('it@examp.le', None, None, 'it_CH', True),
            ('rm@examp.le', None, None, 'rm_CH', True),
            ('xx@examp.le', None, None, 'de_CH', False),
            ('yy@examp.le', None, None, 'fr_CH', False),
            ('aa@examp.le', 'canton', None, 'de_CH', True),
            ('bb@examp.le', 'municipality', 'Zug', 'de_CH', True),
            ('cc@examp.le', 'municipality', 'Baar', 'de_CH', True)
        ):
            session.add(
                EmailSubscriber(
                    address=address,
                    domain=domain,
                    domain_segment=domain_segment,
                    locale=locale,
                    active=active
                )
            )

        # No results yet
        # ... majorz
        notification = EmailNotification()
        notification.trigger(request, majorz)
        assert notification.type == 'email'
        assert notification.election_id == majorz.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )
        assert mock.call_count == 1
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            (
                'Election selon le système majoritaire - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da maiorz - Novs resultats intermediars',
            (
                'Elezione secondo il sistema maggioritario - '
                'Nuovi risultati provvisori'
            ),
            'Majorzwahl - Neue Zwischenresultate',
            'Majorzwahl - Neue Zwischenresultate',
        ]
        assert sorted([email['To'] for email in emails]) == [
            'aa@examp.le',
            'de@examp.le',
            'fr@examp.le',
            'it@examp.le',
            'rm@examp.le'
        ]
        assert set(email['ReplyTo'] for email in emails) == {
            'Kanton Govikon <reply-to@example.org>'
        }
        headers_per_email = [
            {h['Name']: h['Value'] for h in email['Headers']}
            for email in emails
        ]
        assert set(
            headers['List-Unsubscribe-Post'] for headers in headers_per_email
        ) == {'List-Unsubscribe=One-Click'}
        assert sorted([
            headers['List-Unsubscribe'] for headers in headers_per_email
        ]) == [
            "<Principal/unsubscribe-email?opaque={address: aa@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: de@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: fr@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: it@examp.le}>",
            "<Principal/unsubscribe-email?opaque={address: rm@examp.le}>"
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

    with freeze_time("2008-01-01 01:00"):
        # ... proporz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, proporz)
        assert notification.type == 'email'
        assert notification.election_id == proporz.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )
        assert mock.call_count == 1
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            (
                'Election selon le système proportionnel - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da proporz - Novs resultats intermediars',
            'Proporzwahl - Neue Zwischenresultate',
            'Proporzwahl - Neue Zwischenresultate',
            'Proporzwahl - Nuovi risultati provvisori'
        ]
        assert sorted([email['To'] for email in emails]) == [
            'bb@examp.le',
            'de@examp.le',
            'fr@examp.le',
            'it@examp.le',
            'rm@examp.le'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

        # Intermediate results
        lids = {'1': uuid4(), '2': uuid4()}
        proporz.lists.append(List(id=lids['1'], list_id='1', name='FDP'))
        proporz.lists.append(List(id=lids['2'], list_id='2', name='SP'))

        mcids = {'1': uuid4(), '2': uuid4()}
        pcids = {'1': uuid4(), '2': uuid4()}
        keys = ['candidate_id', 'first_name', 'family_name', 'elected']
        for values in (
            ('1', 'Peter', 'Maier', False),
            ('2', 'Hans', 'Müller', False),
        ):
            kw: dict[str, Any] = {
                key: values[index]
                for index, key in enumerate(keys)
            }

            kw['id'] = mcids[kw['candidate_id']]
            majorz.candidates.append(Candidate(**kw))

            kw['id'] = pcids[kw['candidate_id']]
            kw['list_id'] = lids[kw['candidate_id']]
            proporz.candidates.append(Candidate(**kw))

        keys = [
            'entity_id', 'name', 'counted', 'eligible_voters',
            'received_ballots', 'blank_ballots', 'invalid_ballots',
            'blank_votes', 'invalid_votes'
        ]
        for vals in (
            (1711, 'Zug', False, 16516, 8516, 80, 1, 0, 0),
            (1706, 'Oberägeri', True, 3560, 1560, 18, 0, 0, 0),
            (1709, 'Unterägeri', True, 5245, 2245, 18, 1, 0, 0),
            (1704, 'Menzingen', True, 2917, 1917, 17, 0, 0, 0),
            (1701, 'Baar', True, 13828, 6828, 54, 3, 0, 0),
            (1702, 'Cham', True, 9687, 4687, 60, 0, 0, 0),
            (1703, 'Hünenberg', True, 5842, 2842, 15, 1, 0, 0),
            (1708, 'Steinhausen', True, 5989, 2989, 17, 0, 0, 0),
            (1707, 'Risch', True, 6068, 3068, 17, 0, 0, 0),
            (1710, 'Walchwil', True, 2016, 1016, 8, 0, 0, 0),
            (1705, 'Neuheim', True, 1289, 689, 10, 1, 0, 0),
        ):
            kw = {key: vals[index] for index, key in enumerate(keys)}
            result = ElectionResult(**kw)
            result.candidate_results.append(
                CandidateResult(candidate_id=mcids['1'], votes=500)
            )
            result.candidate_results.append(
                CandidateResult(candidate_id=mcids['2'], votes=200)
            )
            majorz.results.append(result)

            result = ElectionResult(**kw)
            result.candidate_results.append(
                CandidateResult(candidate_id=pcids['1'], votes=500)
            )
            result.candidate_results.append(
                CandidateResult(candidate_id=pcids['2'], votes=200)
            )
            result.list_results.append(
                ListResult(list_id=lids['1'], votes=700)
            )
            result.list_results.append(
                ListResult(list_id=lids['2'], votes=600)
            )
            proporz.results.append(result)

    with freeze_time("2008-01-01 02:00"):
        # ... majorz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, majorz)
        emails = list(mock.call_args.args[0])
        assert sorted(email['Subject'] for email in emails) == [
            (
                'Election selon le système majoritaire - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da maiorz - Novs resultats intermediars',
            (
                'Elezione secondo il sistema maggioritario - '
                'Nuovi risultati provvisori'
            ),
            'Majorzwahl - Neue Zwischenresultate',
            'Majorzwahl - Neue Zwischenresultate'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "10 da 11" in contents
        assert "10 di 11" in contents
        assert "10 de 11" in contents
        assert "10 von 11" in contents
        assert "Maier Peter" in contents
        assert "5’500" in contents
        assert "5 500" in contents
        assert "Müller Hans" in contents
        assert "2’200" in contents
        assert "2 200" in contents

    with freeze_time("2008-01-01 03:00"):
        # ... proporz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, proporz)
        emails = list(mock.call_args.args[0])
        assert sorted(email['Subject'] for email in emails) == [
            (
                'Election selon le système proportionnel - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da proporz - Novs resultats intermediars',
            'Proporzwahl - Neue Zwischenresultate',
            'Proporzwahl - Neue Zwischenresultate',
            'Proporzwahl - Nuovi risultati provvisori'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "10 da 11" in contents
        assert "10 di 11" in contents
        assert "10 de 11" in contents
        assert "10 von 11" in contents
        assert "FDP" in contents
        assert "7’700" in contents

        # note the spaces here are *NOT* actual spaces, they are usually some
        # kind of non-breaking space to keep the numbers together, so don't
        # be fooled by that!
        assert "7 700" in contents
        assert "SP" in contents
        assert "6’600" in contents
        assert "6 600" in contents

        # Final results
        for result in majorz.results:
            result.counted = True
        for result in proporz.results:
            result.counted = True
        for candidate in session.query(Candidate).filter_by(candidate_id='1'):
            candidate.elected = True
        for list_ in session.query(List).filter_by(list_id='1'):
            list_.number_of_mandates = 1

    with freeze_time("2008-01-01 04:00"):
        # ... majorz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, majorz)
        emails = list(mock.call_args.args[0])
        assert sorted(email['Subject'] for email in emails) == [
            'Election selon le système majoritaire - Résultats finaux',
            'Elecziun da maiorz - Resultats finals',
            'Elezione secondo il sistema maggioritario - Risultati finali',
            'Majorzwahl - Schlussresultate',
            'Majorzwahl - Schlussresultate'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Maier Peter" in contents
        assert "Müller Hans" not in contents
        assert "49.83 %" in contents

        # ... proporz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, proporz)
        emails = list(mock.call_args.args[0])
        assert sorted(email['Subject'] for email in emails) == [
            'Election selon le système proportionnel - Résultats finaux',
            'Elecziun da proporz - Resultats finals',
            'Proporzwahl - Risultati finali',
            'Proporzwahl - Schlussresultate',
            'Proporzwahl - Schlussresultate'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "FDP" in contents
        assert "<span>1</span>" in contents
        assert "Maier Peter" in contents
        assert "Müller Hans" not in contents
        assert "49.83 %" in contents


def test_email_notification_election_compound(
    election_day_app_zg: TestApp,
    session: Session
) -> None:

    with freeze_time("2008-01-01 00:00"):
        mock = Mock()
        election_day_app_zg.send_marketing_email_batch = mock  # type: ignore[method-assign]

        principal = election_day_app_zg.principal
        principal.email_notification = True
        principal.reply_to = 'reply-to@example.org'
        election_day_app_zg.cache.set('principal', principal)

        session.add(
            ProporzElection(
                title_translations={
                    'de_CH': "Proporzwahl",
                },
                domain='federation',
                date=date(2011, 1, 1),
                number_of_mandates=1
            )
        )
        election = session.query(ProporzElection).one()

        session.add(
            ElectionCompound(
                title_translations={
                    'de_CH': "Kantonsratswahl",
                    'fr_CH': "Élection du Grand Conseil",
                    'it_CH': "Elezione del Consiglio Cantonale",
                    # 'rm_CH': missing
                },
                domain='canton',
                date=date(2011, 1, 1)
            )
        )
        compound = session.query(ElectionCompound).one()
        compound.elections = [election]

        request: Any = DummyRequest(
            app=election_day_app_zg,
            session=session,
            # Otherwise we will hit an assertion in send_mail
            # due to the escaping of the quotes
            avoid_quotes_in_url=True
        )

        for address, domain, domain_segment, locale, active in (
            ('de@examp.le', None, None, 'de_CH', True),
            ('fr@examp.le', None, None, 'fr_CH', True),
            ('it@examp.le', None, None, 'it_CH', True),
            ('rm@examp.le', None, None, 'rm_CH', True),
            ('xx@examp.le', None, None, 'de_CH', False),
            ('yy@examp.le', None, None, 'fr_CH', False),
            ('aa@examp.le', 'canton', None, 'de_CH', True),
            ('bb@examp.le', 'municipality', 'Zug', 'de_CH', True),
            ('cc@examp.le', 'municipality', 'Baar', 'de_CH', True)
        ):
            session.add(
                EmailSubscriber(
                    address=address,
                    domain=domain,
                    domain_segment=domain_segment,
                    locale=locale,
                    active=active
                )
            )

    with freeze_time("2008-01-01 01:00"):
        # No results yet
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, compound)
        assert notification.type == 'email'
        assert notification.election_compound_id == compound.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )
        assert mock.call_count == 1
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Elezione del Consiglio Cantonale - Nuovi risultati provvisori',
            'Kantonsratswahl - Neue Zwischenresultate',
            'Kantonsratswahl - Neue Zwischenresultate',
            'Kantonsratswahl - Novs resultats intermediars',
            'Élection du Grand Conseil - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

        # Intermediate results
        lids = {'1': uuid4(), '2': uuid4()}
        election.lists.append(List(id=lids['1'], list_id='1', name='FDP'))
        election.lists.append(List(id=lids['2'], list_id='2', name='SP'))

        pcids = {'1': uuid4(), '2': uuid4()}
        keys = ['candidate_id', 'first_name', 'family_name', 'elected']
        for values in (
            ('1', 'Peter', 'Maier', False),
            ('2', 'Hans', 'Müller', False),
        ):
            kw: dict[str, Any] = {
                key: values[index]
                for index, key in enumerate(keys)
            }
            kw['list_id'] = lids[kw['candidate_id']]
            kw['id'] = pcids[kw['candidate_id']]
            election.candidates.append(Candidate(**kw))

        keys = [
            'entity_id', 'name', 'counted', 'eligible_voters',
            'received_ballots', 'blank_ballots', 'invalid_ballots',
            'blank_votes', 'invalid_votes'
        ]
        for vals in (
            (1711, 'Zug', False, 16516, 8516, 80, 1, 0, 0),
            (1706, 'Oberägeri', True, 3560, 1560, 18, 0, 0, 0),
            (1709, 'Unterägeri', True, 5245, 2245, 18, 1, 0, 0),
            (1704, 'Menzingen', True, 2917, 1917, 17, 0, 0, 0),
            (1701, 'Baar', True, 13828, 6828, 54, 3, 0, 0),
            (1702, 'Cham', True, 9687, 4687, 60, 0, 0, 0),
            (1703, 'Hünenberg', True, 5842, 2842, 15, 1, 0, 0),
            (1708, 'Steinhausen', True, 5989, 2989, 17, 0, 0, 0),
            (1707, 'Risch', True, 6068, 3068, 17, 0, 0, 0),
            (1710, 'Walchwil', True, 2016, 1016, 8, 0, 0, 0),
            (1705, 'Neuheim', True, 1289, 689, 10, 1, 0, 0),
        ):
            kw = {key: vals[index] for index, key in enumerate(keys)}
            result = ElectionResult(**kw)
            result.candidate_results.append(
                CandidateResult(candidate_id=pcids['1'], votes=500)
            )
            result.candidate_results.append(
                CandidateResult(candidate_id=pcids['2'], votes=200)
            )
            result.list_results.append(
                ListResult(list_id=lids['1'], votes=700)
            )
            result.list_results.append(
                ListResult(list_id=lids['2'], votes=600)
            )
            election.results.append(result)

    with freeze_time("2008-01-01 03:00"):
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, compound)
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Elezione del Consiglio Cantonale - Nuovi risultati provvisori',
            'Kantonsratswahl - Neue Zwischenresultate',
            'Kantonsratswahl - Neue Zwischenresultate',
            'Kantonsratswahl - Novs resultats intermediars',
            'Élection du Grand Conseil - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "0 da 1" in contents
        assert "0 di 1" in contents
        assert "0 de 1" in contents
        assert "0 von 1" in contents

        # Final results
        for result in election.results:
            result.counted = True
        for candidate in session.query(Candidate).filter_by(candidate_id='1'):
            candidate.elected = True
        for list_ in session.query(List).filter_by(list_id='1'):
            list_.number_of_mandates = 1

    with freeze_time("2008-01-01 04:00"):
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, compound)
        emails = list(mock.call_args.args[0])
        assert sorted([email['Subject'] for email in emails]) == [
            'Elezione del Consiglio Cantonale - Risultati finali',
            'Kantonsratswahl - Resultats finals',
            'Kantonsratswahl - Schlussresultate',
            'Kantonsratswahl - Schlussresultate',
            'Élection du Grand Conseil - Résultats finaux'
        ]

        contents = ''.join(email['HtmlBody'] for email in emails)
        assert "Maier Peter" in contents


def test_email_notification_send_segmented(
    election_day_app_zg: TestApp,
    session: Session
) -> None:

    mock = Mock()
    election_day_app_zg.send_marketing_email_batch = mock  # type: ignore[method-assign]

    principal = election_day_app_zg.principal
    principal.email_notification = True
    principal.reply_to = 'reply-to@example.org'
    election_day_app_zg.cache.set('principal', principal)

    elections = [
        Election(
            title="WahlE",
            domain='federation',
            date=date(2011, 1, 1)
        )
    ]
    compounds = [
        ElectionCompound(
            title="WahlK",
            domain='canton',
            date=date(2011, 1, 1)
        )
    ]
    votes = [
        Vote(  # type: ignore[misc]
            title="AbstimmungZ",
            domain='municipality',
            domain_segment='Zug',
            date=date(2011, 1, 1),
        ),
        Vote(  # type: ignore[misc]
            title="AbstimmungB",
            domain='municipality',
            domain_segment='Baar',
            date=date(2011, 1, 1),
        )
    ]

    for address, domain, domain_segment, locale, active in (
        ('a@example.org', None, None, 'de_CH', True),
        ('a@example.org', None, None, 'de_CH', True),
        ('a@example.org', None, None, 'en', True),
        ('b@example.org', None, None, 'en', True),
        ('c@example.org', None, None, 'fr_CH', False),
        ('d@example.org', None, None, 'it_CH', False),
        ('e@example.org', 'canton', None, 'de_CH', True),
        ('e@example.org', 'canton', None, 'fr_CH', True),
        ('e@example.org', 'municipality', 'Zug', 'fr_CH', True),
        ('f@example.org', 'municipality', 'Baar', 'it_CH', True),
    ):
        session.add(
            EmailSubscriber(
                address=address,
                domain=domain,
                domain_segment=domain_segment,
                locale=locale,
                active=active
            )
        )

    request: Any = DummyRequest(
        app=election_day_app_zg,
        session=session,
        # Otherwise we will hit an assertion in send_mail
        # due to the escaping of the quotes
        avoid_quotes_in_url=True
    )
    notification = EmailNotification()
    notification.send_emails(request, elections, compounds, votes)
    emails = list(mock.call_args.args[0])
    assert sorted([
        (
            email['To'],
            email['Subject'],
            'WahlE' in email['HtmlBody'],
            'WahlK' in email['HtmlBody'],
            'AbstimmungZ' in email['HtmlBody'],
            'AbstimmungB' in email['HtmlBody'],
        )
        for email in emails
    ]) == [
        ('a@example.org', 'WahlK - Neue Zwischenresultate',
         True, True, True, True),
        ('e@example.org', 'AbstimmungZ - Nouveaux résultats intermédiaires',
         False, False, True, False),
        ('e@example.org', 'WahlK - Neue Zwischenresultate',
         True, True, False, False),
        ('e@example.org', 'WahlK - Nouveaux résultats intermédiaires',
         True, True, False, False),
        ('f@example.org', 'AbstimmungB - Nuovi risultati provvisori',
         False, False, False, True)
    ]


def test_sms_notification(
    election_day_app_zg: TestApp,
    session: Session
) -> None:

    with freeze_time("2008-01-01 00:00"):
        election_day_app_zg.send_sms = Mock()  # type: ignore[method-assign]

        def sms_queue() -> tuple[tuple[set[str], str], ...]:
            return tuple(
                (set(call[0][0]), call[0][1])
                for call in election_day_app_zg.send_sms.call_args_list  # type: ignore[attr-defined]
            )

        principal = election_day_app_zg.principal
        principal.sms_notification = 'https://wab.ch.ch'
        # use the default reply_to
        election_day_app_zg.cache.set('principal', principal)

        session.add(
            Election(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        session.add(
            ElectionCompound(
                title="Elections",
                domain='canton',
                date=date(2011, 1, 1)
            )
        )
        election_compound = session.query(ElectionCompound).one()

        session.add(
            Vote(  # type: ignore[misc]
                title="Vote",
                domain='municipality',
                domain_segment='Zug',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        session.add(
            Vote(  # type: ignore[misc]
                title="Vote",
                domain='municipality',
                domain_segment='Baar',
                date=date(2011, 1, 1),
            )
        )

        request: Any = DummyRequest(app=election_day_app_zg, session=session)
        freezed = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)

        notification = SmsNotification()
        notification.trigger(request, election)
        assert notification.type == 'sms'
        assert notification.election_id == election.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 0

        notification = SmsNotification()
        notification.trigger(request, election_compound)
        assert notification.type == 'sms'
        assert notification.election_compound_id == election_compound.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 0

        notification = SmsNotification()
        notification.trigger(request, vote)
        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 0

        for address, domain, domain_segment, locale, active in (
            ('+41791112233', None, None, 'de_CH', True),
            ('+41791112233', None, None, 'de_CH', True),
            ('+41791112233', None, None, 'en', True),
            ('+41791112244', None, None, 'en', True),
            ('+41791112255', None, None, 'fr_CH', False),
            ('+41791112266', None, None, 'it_CH', False),
            ('+41791112277', 'canton', None, 'de_CH', True),
            ('+41791112277', 'canton', None, 'fr_CH', True),
            ('+41791112277', 'municipality', 'Zug', 'de_CH', True),
            ('+41791112288', 'municipality', 'Baar', 'de_CH', True),
        ):
            session.add(
                SmsSubscriber(
                    address=address,
                    domain=domain,
                    domain_segment=domain_segment,
                    locale=locale,
                    active=active
                )
            )

        # Intermediate election results
        notification = SmsNotification()
        notification.trigger(request, election)

        assert notification.type == 'sms'
        assert notification.election_id == election.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 3
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf Election/election'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on Election/election'
            ),
            (
                {'+41791112277'},
                'Les nouveaux résultats sont disponibles sur Election/election'
            )
        )

        # Intermediate election compound results
        election_day_app_zg.send_sms.reset_mock()
        notification = SmsNotification()
        notification.trigger(request, election_compound)

        assert notification.type == 'sms'
        assert notification.election_compound_id == election_compound.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 3
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf ElectionCompound/elections'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on ElectionCompound/elections'
            ),
            (
                {'+41791112277'},
                'Les nouveaux résultats sont disponibles sur '
                'ElectionCompound/elections'
            )
        )

        # Intermediate vote results
        election_day_app_zg.send_sms.reset_mock()
        notification = SmsNotification()
        notification.trigger(request, vote)

        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 2
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf Vote/vote'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on Vote/vote'
            )
        )

        # Final election results
        election_day_app_zg.send_sms.reset_mock()
        election.status = 'final'
        notification = SmsNotification()
        notification.trigger(request, election)

        assert notification.type == 'sms'
        assert notification.election_id == election.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 3
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf Election/election'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on Election/election'
            ),
            (
                {'+41791112277'},
                'Les nouveaux résultats sont disponibles sur Election/election'
            )
        )

        # Final election compound results
        election_day_app_zg.send_sms.reset_mock()
        with patch.object(ElectionCompound, 'completed',
                          new_callable=PropertyMock) as mock:
            mock.return_value = True
            notification = SmsNotification()
            notification.trigger(request, election_compound)

        assert notification.type == 'sms'
        assert notification.election_compound_id == election_compound.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 3
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf ElectionCompound/elections'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on ElectionCompound/elections'
            ),
            (
                {'+41791112277'},
                'Les nouveaux résultats sont disponibles sur '
                'ElectionCompound/elections'
            )
        )

        # Final vote results
        election_day_app_zg.send_sms.reset_mock()
        vote.status = 'final'
        notification = SmsNotification()
        notification.trigger(request, vote)

        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 2
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf Vote/vote'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on Vote/vote'
            )
        )


        # Really long urls get replaced by a generic one
        election_day_app_zg.send_sms.reset_mock()
        vote.id = 'really-'*16 + 'long'
        notification = SmsNotification()
        notification.trigger(request, vote)

        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app_zg.send_sms.call_count == 2
        assert sms_queue() == (
            (
                {'+41791112233', '+41791112277'},
                'Neue Resultate verfügbar auf https://wab.ch.ch'
            ),
            (
                {'+41791112233', '+41791112244'},
                'New results are available on https://wab.ch.ch'
            )
        )
