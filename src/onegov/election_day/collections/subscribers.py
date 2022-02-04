from email.utils import formataddr
from onegov.core.collection import Pagination
from onegov.core.templates import render_template
from onegov.election_day import _
from onegov.election_day.formats.common import load_csv
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import Subscriber
from sqlalchemy import func


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

    def export(self):
        """ Returns all data connected to these subscribers. """

        return [
            {'address': subscriber.address, 'locale': subscriber.locale}
            for subscriber in self.query()
        ]

    def delete(self, file, mimetype):
        """ Removes the subscribers in the given CSV. """

        csv, error = load_csv(file, mimetype, expected_headers=['address'])
        if error:
            return [error], 0

        addresses = [l.address.lower() for l in csv.lines if l.address]
        query = self.session.query(self.model_class)
        query = query.filter(
            func.lower(self.model_class.address).in_(addresses)
        )
        count = query.delete()
        return [], count


class EmailSubscriberCollection(SubscriberCollection):

    @property
    def model_class(self):
        return EmailSubscriber

    def confirm_subscription(self, subscriber, request):
        """ Give the (new) subscriber a confirmation that he successfully
        subscribed. """

        from onegov.election_day.layouts import MailLayout  # circular

        optout = request.link(request.app.principal, 'unsubscribe-email')
        token = request.new_url_safe_token({'address': subscriber.address})
        optout_custom = f'{optout}?opaque={token}'

        # even though this is technically a transactional e-mail we send
        # it as marketing, since the actual subscription is sent as
        # a marketing e-mail as well
        request.app.send_marketing_email(
            subject=request.translate(
                _("Successfully subscribed to the email service")
            ),
            receivers=(subscriber.address, ),
            reply_to=formataddr((
                request.app.principal.name,
                request.app.principal.reply_to
                or request.app.mail['marketing']['sender']
            )),
            content=render_template(
                'mail_subscribed.pt',
                request,
                {
                    'title': request.translate(
                        _("Successfully subscribed to the email service")
                    ),
                    'model': None,
                    'optout': optout_custom,
                    'layout': MailLayout(self, request)
                }
            ),
            headers={
                'List-Unsubscribe': f'<{optout_custom}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
            }
        )


class SmsSubscriberCollection(SubscriberCollection):

    @property
    def model_class(self):
        return SmsSubscriber

    def confirm_subscription(self, subscriber, request):
        """ Give the (new) subscriber a confirmation that he successfully
        subscribed. """

        content = _(
            "Successfully subscribed to the SMS service. You will"
            " receive a SMS every time new results are published."
        )
        content = request.translate(content)
        request.app.send_sms(subscriber.address, content)
