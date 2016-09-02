from onegov.election_day.models import Webhook


class WebhookCollection(object):

    def __init__(self, session):
        self.session = session

    def add(self, url, last_change, election=None, vote=None):
        webhook = Webhook()
        webhook.url = url
        webhook.last_change = last_change
        if election:
            webhook.election_id = election.id
        if vote:
            webhook.vote_id = vote.id

        self.session.add(webhook)
        self.session.flush()

        return webhook

    def query(self):
        return self.session.query(Webhook)

    def by_election(self, election, url, last_change):
        return self.query().filter(
            Webhook.election_id == election.id,
            Webhook.url == url,
            Webhook.last_change == last_change
        ).first()

    def by_vote(self, vote, url, last_change):
        return self.query().filter(
            Webhook.vote_id == vote.id,
            Webhook.url == url,
            Webhook.last_change == last_change
        ).first()
