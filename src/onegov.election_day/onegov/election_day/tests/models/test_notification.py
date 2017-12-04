from datetime import date
from datetime import datetime
from datetime import timezone
from freezegun import freeze_time
from json import loads
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import Notification
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import WebhookNotification
from onegov.election_day.tests import DummyRequest
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
    assert notification.type == None
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
        assert notification.vote_id == None
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
        assert notification.election_id == None
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

            assert loads(data.decode('utf-8')) == {
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

            assert loads(data.decode('utf-8')) == {
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
