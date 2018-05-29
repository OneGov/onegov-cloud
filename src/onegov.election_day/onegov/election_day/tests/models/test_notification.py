from datetime import date
from datetime import datetime
from datetime import timezone
from freezegun import freeze_time
from onegov.ballot import BallotResult
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ComplexVote
from onegov.ballot import Election
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListResult
from onegov.ballot import ProporzElection
from onegov.ballot import Vote
from onegov.core.custom import json
from onegov.election_day.models import EmailNotification
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import Notification
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import WebhookNotification
from onegov.election_day.tests.common import DummyRequest
from pytest import raises
from time import sleep
from unittest.mock import Mock
from unittest.mock import patch


def test_notification(session):
    notification = Notification()
    notification.last_modified = datetime(
        2007, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    session.add(notification)
    session.flush()

    notification = session.query(Notification).one()
    assert notification.id
    assert notification.type is None
    assert notification.last_modified == datetime(
        2007, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert notification.election_id is None
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
        assert notification.election_id == election.id
        assert notification.vote_id is None
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
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
        assert notification.election_id is None
        assert notification.vote_id == vote.id
        assert notification.last_modified == datetime(
            2009, 1, 1, 0, 0, tzinfo=timezone.utc
        )

    with raises(NotImplementedError):
        notification.trigger(DummyRequest(), election)
    with raises(NotImplementedError):
        notification.trigger(DummyRequest(), vote)


def test_webhook_notification(session):
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
        notification.trigger(DummyRequest(), election)

        assert notification.type == 'webhooks'
        assert notification.election_id == election.id
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

        notification.trigger(DummyRequest(), vote)

        assert notification.type == 'webhooks'
        assert notification.vote_id == vote.id
        assert notification.last_modified == datetime(
            2008, 1, 1, 0, 0, tzinfo=timezone.utc
        )

        with patch('urllib.request.urlopen') as urlopen:
            request = DummyRequest()
            request.app.principal.webhooks = {'http://abc.com/1': None}

            notification.trigger(request, election)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'completed': False,
                'date': '2011-01-01',
                'domain': 'federation',
                'elected': [],
                'last_modified': '2008-01-01T00:00:00+00:00',
                'progress': {'counted': 0, 'total': 0},
                'title': {'de_CH': 'Election'},
                'type': 'election',
                'url': 'Election/election'
            }

            notification.trigger(request, vote)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

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
                'yeas_percentage': None
            }


def test_email_notification_vote(election_day_app, session):
    with freeze_time("2008-01-01 00:00"):
        mock = Mock()
        election_day_app.send_email = mock

        principal = election_day_app.principal
        principal.email_notification = True
        election_day_app.cache.set('principal', principal)

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
            ComplexVote(
                title_translations={
                    'de_CH': "Vorlage mit Gegenentwurf",
                    'fr_CH': "Vote avec contre-projet",
                    # 'it_CH' missing
                    'rm_CH': "Project cun cuntraproposta"
                },
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        complex_vote = session.query(ComplexVote).one()

        request = DummyRequest(app=election_day_app, session=session)
        freezed = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)

        session.add(EmailSubscriber(address='de@examp.le', locale='de_CH'))
        session.add(EmailSubscriber(address='fr@examp.le', locale='fr_CH'))
        session.add(EmailSubscriber(address='it@examp.le', locale='it_CH'))
        session.add(EmailSubscriber(address='rm@examp.le', locale='rm_CH'))

        # No results yet
        # ... simple
        notification = EmailNotification()
        notification.trigger(request, simple_vote)
        assert notification.type == 'email'
        assert notification.vote_id == simple_vote.id
        assert notification.last_modified == freezed
        assert mock.call_count == 4
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Abstimmung - Neue Zwischenresultate',
            'Votazione - Nuovi risultati provvisori',
            'Votaziun - Novs resultats intermediars',
            'Vote - Nouveaux résultats intermédiaires'
        ]
        assert sorted([call[2]['receivers'] for call in mock.mock_calls]) == [
            ('de@examp.le',),
            ('fr@examp.le',),
            ('it@examp.le',),
            ('rm@examp.le',)
        ]
        assert set([call[2]['reply_to'] for call in mock.mock_calls]) == {
            'Kanton Govikon <mails@govikon.ch>'
        }
        assert set([
            call[2]['headers']['List-Unsubscribe-Post']
            for call in mock.mock_calls
        ]) == {'List-Unsubscribe=One-Click'}
        assert sorted([
            call[2]['headers']['List-Unsubscribe'] for call in mock.mock_calls
        ]) == [
            "<Principal/unsubscribe-email?opaque={'address': 'de@examp.le'}>",
            "<Principal/unsubscribe-email?opaque={'address': 'fr@examp.le'}>",
            "<Principal/unsubscribe-email?opaque={'address': 'it@examp.le'}>",
            "<Principal/unsubscribe-email?opaque={'address': 'rm@examp.le'}>"
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

        # ... complex
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, complex_vote)
        assert notification.type == 'email'
        assert notification.vote_id == complex_vote.id
        assert notification.last_modified == freezed
        assert mock.call_count == 4
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Project cun cuntraproposta - Novs resultats intermediars',
            'Vorlage mit Gegenentwurf - Neue Zwischenresultate',
            'Vorlage mit Gegenentwurf - Nuovi risultati provvisori',
            'Vote avec contre-projet - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
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

        # ... simple
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, simple_vote)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Abstimmung - Neue Zwischenresultate',
            'Votazione - Nuovi risultati provvisori',
            'Votaziun - Novs resultats intermediars',
            'Vote - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
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
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Project cun cuntraproposta - Novs resultats intermediars',
            'Vorlage mit Gegenentwurf - Neue Zwischenresultate',
            'Vorlage mit Gegenentwurf - Nuovi risultati provvisori',
            'Vote avec contre-projet - Nouveaux résultats intermédiaires'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
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

        # ... simple
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, simple_vote)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Abstimmung - Abgelehnt',
            'Votazione - Respinto',
            'Votaziun - Refusà',
            'Vote - Refusé'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "37.21%" in contents
        assert "62.79%" in contents
        assert "61.34 %" in contents

        # ... complex
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, complex_vote)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Project cun cuntraproposta - Refusà',
            'Vorlage mit Gegenentwurf - Abgelehnt',
            'Vorlage mit Gegenentwurf - Respinto',
            'Vote avec contre-projet - Refusé'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "Refusà l'iniziativa e la cuntraproposta" in contents
        assert "Initiative et contre-projet rejetées" in contents
        assert "Iniziativa e controprogetto sono state rifiutate" in contents
        assert "Initative und Gegenentwurf abgelehnt" in contents
        assert "37.21%" in contents
        assert "62.79%" in contents
        assert "61.34 %" in contents


def test_email_notification_election(election_day_app, session):
    with freeze_time("2008-01-01 00:00"):
        mock = Mock()
        election_day_app.send_email = mock

        principal = election_day_app.principal
        principal.email_notification = True
        election_day_app.cache.set('principal', principal)

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
            ProporzElection(
                title_translations={
                    'de_CH': "Proporzwahl",
                    'fr_CH': "Election selon le système proportionnel",
                    # 'it_CH' missing
                    'rm_CH': "Elecziun da proporz"
                },
                domain='federation',
                date=date(2011, 1, 1),
                number_of_mandates=1
            )
        )
        proporz = session.query(ProporzElection).one()

        request = DummyRequest(app=election_day_app, session=session)
        freezed = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)

        session.add(EmailSubscriber(address='de@examp.le', locale='de_CH'))
        session.add(EmailSubscriber(address='fr@examp.le', locale='fr_CH'))
        session.add(EmailSubscriber(address='it@examp.le', locale='it_CH'))
        session.add(EmailSubscriber(address='rm@examp.le', locale='rm_CH'))

        # No results yet
        # ... majorz
        notification = EmailNotification()
        notification.trigger(request, majorz)
        assert notification.type == 'email'
        assert notification.election_id == majorz.id
        assert notification.last_modified == freezed
        assert mock.call_count == 4
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            (
                'Election selon le système majoritaire - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da maiorz - Novs resultats intermediars',
            (
                'Elezione secondo il sistema maggioritario - '
                'Nuovi risultati provvisori'
            ),
            'Majorzwahl - Neue Zwischenresultate'
        ]
        assert sorted([call[2]['receivers'] for call in mock.mock_calls]) == [
            ('de@examp.le',),
            ('fr@examp.le',),
            ('it@examp.le',),
            ('rm@examp.le',)
        ]
        assert set([call[2]['reply_to'] for call in mock.mock_calls]) == {
            'Kanton Govikon <mails@govikon.ch>'
        }
        assert set([
            call[2]['headers']['List-Unsubscribe-Post']
            for call in mock.mock_calls
        ]) == {'List-Unsubscribe=One-Click'}
        assert sorted([
            call[2]['headers']['List-Unsubscribe'] for call in mock.mock_calls
        ]) == [
            "<Principal/unsubscribe-email?opaque={'address': 'de@examp.le'}>",
            "<Principal/unsubscribe-email?opaque={'address': 'fr@examp.le'}>",
            "<Principal/unsubscribe-email?opaque={'address': 'it@examp.le'}>",
            "<Principal/unsubscribe-email?opaque={'address': 'rm@examp.le'}>"
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

        # ... proporz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, proporz)
        assert notification.type == 'email'
        assert notification.election_id == proporz.id
        assert notification.last_modified == freezed
        assert mock.call_count == 4
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            (
                'Election selon le système proportionnel - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da proporz - Novs resultats intermediars',
            'Proporzwahl - Neue Zwischenresultate',
            'Proporzwahl - Nuovi risultati provvisori'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "Noch keine Resultate" in contents
        assert "Pas de résultats à l'heure actuelle" in contents
        assert "Ancora nessun risultato" in contents
        assert "Anc nagins resultats avant maun" in contents

        # Intermediate results
        proporz.lists.append(List(list_id='1', name='FDP'))
        proporz.lists.append(List(list_id='2', name='SP'))
        lids = {
            '1': session.query(List).filter_by(list_id='1').one().id,
            '2': session.query(List).filter_by(list_id='2').one().id
        }

        keys = ['candidate_id', 'first_name', 'family_name', 'elected']
        for values in (
            ('1', 'Peter', 'Maier', False),
            ('2', 'Hans', 'Müller', False),
        ):
            kw = {key: values[index] for index, key in enumerate(keys)}
            majorz.candidates.append(Candidate(**kw))
            kw['list_id'] = lids[kw['candidate_id']]
            proporz.candidates.append(Candidate(**kw))
        mcids = {
            '1': majorz.candidates.filter_by(candidate_id='1').one().id,
            '2': majorz.candidates.filter_by(candidate_id='2').one().id,
        }
        pcids = {
            '1': proporz.candidates.filter_by(candidate_id='1').one().id,
            '2': proporz.candidates.filter_by(candidate_id='2').one().id,
        }

        keys = [
            'entity_id', 'name', 'counted', 'eligible_voters',
            'received_ballots', 'blank_ballots', 'invalid_ballots',
            'blank_votes', 'invalid_votes'
        ]
        for values in (
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
            kw = {key: values[index] for index, key in enumerate(keys)}
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

        # ... majorz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, majorz)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            (
                'Election selon le système majoritaire - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da maiorz - Novs resultats intermediars',
            (
                'Elezione secondo il sistema maggioritario - '
                'Nuovi risultati provvisori'
            ),
            'Majorzwahl - Neue Zwischenresultate'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "10 da 11" in contents
        assert "10 di 11" in contents
        assert "10 de 11" in contents
        assert "10 von 11" in contents
        assert "Maier Peter" in contents
        assert "5’500" in contents
        assert "5 500" in contents
        assert "Müller Hans" in contents
        assert "2’200" in contents
        assert "2 200" in contents

        # ... proporz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, proporz)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            (
                'Election selon le système proportionnel - '
                'Nouveaux résultats intermédiaires'
            ),
            'Elecziun da proporz - Novs resultats intermediars',
            'Proporzwahl - Neue Zwischenresultate',
            'Proporzwahl - Nuovi risultati provvisori'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "10 da 11" in contents
        assert "10 di 11" in contents
        assert "10 de 11" in contents
        assert "10 von 11" in contents
        assert "FDP" in contents
        assert "7’700" in contents
        assert "7 700" in contents
        assert "SP" in contents
        assert "6’600" in contents
        assert "6 600" in contents

        # Final results
        for result in majorz.results:
            result.counted = True
        for result in proporz.results:
            result.counted = True
        for candidate in session.query(Candidate).filter_by(candidate_id='1'):
            candidate.elected = True
        for list_ in session.query(List).filter_by(list_id='1'):
            list_.number_of_mandates = 1

        # ... majorz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, majorz)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Election selon le système majoritaire - Résultats finaux',
            'Elecziun da maiorz - Resultats finals',
            'Elezione secondo il sistema maggioritario - Risultati finali',
            'Majorzwahl - Schlussresultate'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "Maier Peter" in contents
        assert "Müller Hans" not in contents
        assert "49.83 %" in contents

        # ... proporz
        mock.reset_mock()
        notification = EmailNotification()
        notification.trigger(request, proporz)
        assert sorted([call[2]['subject'] for call in mock.mock_calls]) == [
            'Election selon le système proportionnel - Résultats finaux',
            'Elecziun da proporz - Resultats finals',
            'Proporzwahl - Risultati finali',
            'Proporzwahl - Schlussresultate'
        ]
        contents = ''.join(call[2]['content'] for call in mock.mock_calls)
        assert "FDP" in contents
        assert "<span>1</span>" in contents
        assert "Maier Peter" in contents
        assert "Müller Hans" not in contents
        assert "49.83 %" in contents


def test_sms_notification(request, election_day_app, session):
    with freeze_time("2008-01-01 00:00"):
        election_day_app.send_sms = Mock()

        principal = election_day_app.principal
        principal.sms_notification = 'https://wab.ch.ch'
        election_day_app.cache.set('principal', principal)

        session.add(
            Election(
                title="Election",
                domain='federation',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        request = DummyRequest(app=election_day_app, session=session)
        freezed = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)

        notification = SmsNotification()
        notification.trigger(request, election)
        assert notification.type == 'sms'
        assert notification.election_id == election.id
        assert notification.last_modified == freezed
        assert election_day_app.send_sms.call_count == 0

        notification = SmsNotification()
        notification.trigger(request, vote)
        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app.send_sms.call_count == 0

        session.add(SmsSubscriber(address='+41791112233', locale='en'))
        session.add(SmsSubscriber(address='+41791112233', locale='de_CH'))
        session.add(EmailSubscriber(address='t@rg.et', locale='fr_CH'))

        # Intermediate election results
        notification = SmsNotification()
        notification.trigger(request, election)

        assert notification.type == 'sms'
        assert notification.election_id == election.id
        assert notification.last_modified == freezed
        assert election_day_app.send_sms.call_count == 2
        assert election_day_app.send_sms.call_args_list[0][0] == (
            '+41791112233',
            'New intermediate results are available on https://wab.ch.ch'
        )
        assert election_day_app.send_sms.call_args_list[1][0] == (
            '+41791112233',
            'Neue Zwischenresultate verfügbar auf https://wab.ch.ch'
        )

        # Intermediate vote results
        notification = SmsNotification()
        notification.trigger(request, vote)

        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app.send_sms.call_count == 4
        assert election_day_app.send_sms.call_args_list[2][0] == (
            '+41791112233',
            'New intermediate results are available on https://wab.ch.ch'
        )
        assert election_day_app.send_sms.call_args_list[3][0] == (
            '+41791112233',
            'Neue Zwischenresultate verfügbar auf https://wab.ch.ch'
        )

        # Final election results
        election.status = 'final'
        notification = SmsNotification()
        notification.trigger(request, election)

        assert notification.type == 'sms'
        assert notification.election_id == election.id
        assert notification.last_modified == freezed
        assert election_day_app.send_sms.call_count == 6
        assert election_day_app.send_sms.call_args_list[4][0] == (
            '+41791112233',
            'Final results are available on https://wab.ch.ch'
        )
        assert election_day_app.send_sms.call_args_list[5][0] == (
            '+41791112233',
            'Schlussresultate verfügbar auf https://wab.ch.ch'
        )

        # Final vote results
        vote.status = 'final'
        notification = SmsNotification()
        notification.trigger(request, vote)

        assert notification.type == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_modified == freezed
        assert election_day_app.send_sms.call_count == 8
        assert election_day_app.send_sms.call_args_list[6][0] == (
            '+41791112233',
            'Final results are available on https://wab.ch.ch'
        )
        assert election_day_app.send_sms.call_args_list[7][0] == (
            '+41791112233',
            'Schlussresultate verfügbar auf https://wab.ch.ch'
        )
