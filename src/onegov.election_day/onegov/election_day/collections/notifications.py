from onegov.election_day import _
from onegov.election_day.models import EmailNotification
from onegov.election_day.models import Notification
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import WebhookNotification


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
            Notification.last_modified == election.last_modified
        ).all()

    def by_vote(self, vote):
        """ Returns the notification for the given vote and its modification
        time.

        """

        return self.query().filter(
            Notification.vote_id == vote.id,
            Notification.last_modified == vote.last_modified
        ).all()

    def trigger(self, request, model, options):
        """ Triggers and adds the selected notifications. """

        if 'email' in options and request.app.principal.email_notification:
            notification = EmailNotification()
            notification.trigger(request, model)
            self.session.add(notification)

        if 'sms' in options and request.app.principal.sms_notification:
            notification = SmsNotification()
            notification.trigger(request, model)
            self.session.add(notification)

        if 'webhooks' in options and request.app.principal.webhooks:
            notification = WebhookNotification()
            notification.trigger(request, model)
            self.session.add(notification)

        self.session.flush()

    def trigger_summarized(self, request, elections, votes, options):
        """ Triggers and adds a single notification for all given votes and
        elections.

        """

        if not (elections or votes) or not options:
            return

        if 'email' in options and request.app.principal.email_notification:
            completed = True
            for election in elections:
                completed &= election.completed
                notification = EmailNotification()
                notification.update_from_model(election)
                self.session.add(notification)
            for vote in votes:
                completed &= vote.completed
                notification = EmailNotification()
                notification.update_from_model(vote)
                self.session.add(notification)

            notification = EmailNotification()
            notification.send_emails(
                request,
                elections,
                votes,
                _("The final results are available") if completed else
                _("New results are available")
            )

        if 'sms' in options and request.app.principal.sms_notification:
            for election in elections:
                notification = SmsNotification()
                notification.update_from_model(election)
                self.session.add(notification)
            for vote in votes:
                notification = SmsNotification()
                notification.update_from_model(vote)
                self.session.add(notification)

            notification = SmsNotification()
            notification.send_sms(
                request,
                _(
                    "New results are available on ${url}",
                    mapping={'url': request.app.principal.sms_notification}
                )
            )

        if 'webhooks' in options and request.app.principal.webhooks:
            for election in elections:
                notification = WebhookNotification()
                notification.trigger(request, election)
                self.session.add(notification)
            for vote in votes:
                notification = WebhookNotification()
                notification.trigger(request, vote)
                self.session.add(notification)

        self.session.flush()
