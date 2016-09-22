from onegov.ballot.models import Election, Vote
from onegov.election_day.models import Notification


class NotificationCollection(object):

    def __init__(self, session):
        self.session = session

    def add(self, url, last_change, election_or_vote):
        """ Adds a new notification. """

        notification = Notification()
        notification.url = url
        notification.last_change = last_change
        if isinstance(election_or_vote, Election):
            notification.election_id = election_or_vote.id
        if isinstance(election_or_vote, Vote):
            notification.vote_id = election_or_vote.id

        self.session.add(notification)
        self.session.flush()

        return notification

    def query(self):
        return self.session.query(Notification)

    def by_election(self, election, url, last_change):
        """ Returns the notification specified by given parameters. """
        return self.query().filter(
            Notification.election_id == election.id,
            Notification.url == url,
            Notification.last_change == last_change
        ).first()

    def by_vote(self, vote, url, last_change):
        """ Returns the notification specified by given parameters. """

        return self.query().filter(
            Notification.vote_id == vote.id,
            Notification.url == url,
            Notification.last_change == last_change
        ).first()
