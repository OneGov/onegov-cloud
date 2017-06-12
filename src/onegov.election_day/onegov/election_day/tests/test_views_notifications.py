from datetime import date
from onegov.election_day.tests import login
from onegov.election_day.tests import upload_majorz_election
from onegov.election_day.tests import upload_vote
from webtest import TestApp as Client


def test_view_notifications_votes(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Vote"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Benachrichtigungen auslösen" not in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" not in upload_vote(client, False)

    election_day_app.principal.webhooks = {'http://example.com/1': None}
    del election_day_app.principal.notifications

    assert "Benachrichtigungen auslösen" in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" in upload_vote(client, False)

    assert "erneut auslösen" not in client.get('/vote/vote/trigger')
    client.get('/vote/vote/trigger').form.submit()
    assert "erneut auslösen" in client.get('/vote/vote/trigger')

    upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')


def test_view_notifications_elections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Majorz Election"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Benachrichtigungen auslösen" not in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" not in upload_majorz_election(
        client, False
    )

    election_day_app_gr.principal.webhooks = {'http://example.com/1': None}
    del election_day_app_gr.principal.notifications

    assert "Benachrichtigungen auslösen" in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" in upload_majorz_election(
        client, False
    )

    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )
    client.get('/election/majorz-election/trigger').form.submit()
    assert "erneut auslösen" in client.get('/election/majorz-election/trigger')

    upload_majorz_election(client)
    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )
