from onegov.election_day.models import Subscriber


class SubscriberCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Subscriber)

    def subscribe(self, phone_number):
        """ Subscribe with the given phone number. """

        if self.query().filter_by(phone_number=phone_number).first():
            return

        subscriber = Subscriber(phone_number=phone_number)

        self.session.add(subscriber)
        self.session.flush()

        return subscriber

    def unsubscribe(self, phone_number):
        """ Unsubscribe with the given phone number. """

        for subscriber in self.query().filter_by(phone_number=phone_number):
            self.session.delete(subscriber)

        self.session.flush()
