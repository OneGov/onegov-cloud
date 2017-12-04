from onegov.core.collection import Pagination
from onegov.election_day import _
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import Subscriber


class SubscriberCollectionPagination(Pagination):

    def __init__(self, session, page=0, term=None):
        self.session = session
        self.page = page
        self.term = term

    def __eq__(self, other):
        return (self.page == other.page) and (self.term == other.term)

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index)


class SubscriberCollection(SubscriberCollectionPagination):

    @property
    def model_class(self):
        return Subscriber

    def query(self):
        query = self.session.query(self.model_class)
        if self.term:
            query = query.filter(self.model_class.address.contains(self.term))
            self.batch_size = query.count()
        query = query.order_by(self.model_class.address)
        return query

    def by_id(self, id):
        """ Returns the subscriber by its id. """

        return self.query().filter(self.model_class.id == id).first()

    def subscribe(self, address, request, confirm=True):
        """ Subscribe with the given address and locale.

        Existing subscriptions with the given address will be updated according
        to the new locale.
        """

        locale = request.locale

        subscriber = None
        for existing in self.query().filter_by(address=address):
            if not subscriber:
                subscriber = existing
                if subscriber.locale != locale:
                    subscriber.locale = locale
            else:
                self.session.delete(existing)

        if not subscriber:
            subscriber = self.model_class(
                address=address,
                locale=locale
            )
            self.session.add(subscriber)

            if confirm:
                self.confirm_subscription(subscriber, request)

        self.session.flush()

        return subscriber

    def confirm_subscription(self, subscriber, request):
        """ Give the (new) subscriber a confirmation that he successfully
        subscribed. """

        pass

    def unsubscribe(self, address):
        """ Unsubscribe with the given address. """

        query = self.query().filter(self.model_class.address == address)
        for subscriber in query:
            self.session.delete(subscriber)

        self.session.flush()


class SmsSubscriberCollection(SubscriberCollection):

    @property
    def model_class(self):
        return SmsSubscriber

    def confirm_subscription(self, subscriber, request):
        """ Give the (new) subscriber a confirmation that he successfully
        subscribed. """

        content = _(
            "Successfully subscribed to the SMS services. You will"
            " receive an SMS every time new results are published."
        )
        content = request.translate(content)
        request.app.send_sms(subscriber.address, content)


class EmailSubscriberCollection(SubscriberCollection):

    @property
    def model_class(self):
        return EmailSubscriber

    def confirm_subscription(self, subscriber, request):
        """ Give the (new) subscriber a confirmation that he successfully
        subscribed. """

        # todo:
        pass
