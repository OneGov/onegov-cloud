from onegov.election_day.models import Notification
from onegov.election_day.models import WebhookNotification
from onegov.election_day.models import SmsNotification


class NotificationCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Notification)

    def by_election(self, election):
        """ Returns the notification for the given election and its
        modification times.

        """

        return self.query().filter(
            Notification.election_id == election.id,
            Notification.last_change == election.last_result_change
        ).all()

    def by_vote(self, vote):
        """ Returns the notification for the given vote and its modification
        time.

        """

        return self.query().filter(
            Notification.vote_id == vote.id,
            Notification.last_change == vote.last_result_change
        ).all()

    def trigger(self, request, model):
        """ Triggers and adds all notifications. """

        if request.app.principal.sms_notification:
            notification = SmsNotification()
            notification.trigger(request, model)
            self.session.add(notification)

        if request.app.principal.webhooks:
            notification = WebhookNotification()
            notification.trigger(request, model)
            self.session.add(notification)

        self.session.flush()
