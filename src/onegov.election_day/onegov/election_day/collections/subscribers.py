from onegov.core.collection import Pagination
from onegov.election_day.models import Subscriber


class SubscriberCollectionPagination(Pagination):

    def __init__(self, session, page=0):
        self.session = session
        self.page = page

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query().order_by(Subscriber.phone_number)

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index)


class SubscriberCollection(SubscriberCollectionPagination):

    def query(self):
        return self.session.query(Subscriber)

    def by_id(self, id):
        """ Returns the subscriber by id. """

        return self.query().filter(Subscriber.id == id).first()

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
