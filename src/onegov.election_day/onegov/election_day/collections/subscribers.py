from onegov.election_day.models import Subscriber


class SubscriberCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Subscriber)

    def subscribe(self, phone_number, locale):
        """ Subscribe with the given phone number and locale.

        Existing subscriptions with the given number will be updated according
        to the new locale.
        """

        subscriber = None
        for existing in self.query().filter_by(phone_number=phone_number):
            if not subscriber:
                subscriber = existing
                if subscriber.locale != locale:
                    subscriber.locale = locale
            else:
                self.session.delete(existing)

        if not subscriber:
            subscriber = Subscriber(
                phone_number=phone_number,
                locale=locale
            )
            self.session.add(subscriber)

        self.session.flush()

        return subscriber

    def unsubscribe(self, phone_number):
        """ Unsubscribe with the given phone number. """

        for subscriber in self.query().filter_by(phone_number=phone_number):
            self.session.delete(subscriber)

        self.session.flush()
