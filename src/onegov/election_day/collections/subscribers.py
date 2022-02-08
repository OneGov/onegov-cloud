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

    def __init__(self, session, page=0, term=None, active_only=True):
        self.session = session
        self.page = page
        self.term = term
        self.active_only = active_only

    def __eq__(self, other):
        return (
            (self.page == other.page)
            and (self.term == other.term)
            and (self.active_only == other.active_only)
        )

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index)

    def for_active_only(self, active_only):
        return self.__class__(self.session, 0, self.term, active_only)


class SubscriberCollection(SubscriberCollectionPagination):

    @property
    def model_class(self):
        return Subscriber

    def add(self, address, locale, active):
        subscriber = self.model_class(
            address=address,
            locale=locale,
            active=active
        )
        self.session.add(subscriber)
        self.session.flush()
        return subscriber

    def query(self, active_only=None):
        query = self.session.query(self.model_class)

        active_only = self.active_only if active_only is None else active_only
        if active_only:
            query = query.filter(self.model_class.active.is_(True))

        if self.term:
            query = query.filter(self.model_class.address.contains(self.term))
            self.batch_size = query.count()

        query = query.order_by(self.model_class.address)

        return query

    def by_id(self, id):
        """ Returns the subscriber by its id. """

        query = self.query(active_only=False)
        query = query.filter(self.model_class.id == id)
        return query.first()

    def by_address(self, address):
        """ Returns the (first) subscriber by its address. """

        query = self.query(active_only=False)
        query = query.filter(self.model_class.address == address)
        return query.first()

    def initiate_subscription(self, address, request):
        """ Initiate the subscription process.

        Might be used to change the locale by re-subscribing.

        """

        subscriber = self.by_address(address)
        if not subscriber:
            subscriber = self.add(address, request.locale, False)

        self.handle_subscription(subscriber, request)

        return subscriber

    def handle_subscription(self, subscriber, request):
        """ Send the subscriber a request to confirm the subscription. """

        raise NotImplementedError()

    def initiate_unsubscription(self, address, request):
        """ Initiate the unsubscription process. """

        subscriber = self.by_address(address)
        if subscriber:
            self.handle_unsubscription(subscriber, request)

    def handle_unsubscription(self, subscriber, request):
        """ Send the subscriber a request to confirm the unsubscription.
        """

        raise NotImplementedError()

    def export(self):
        """ Returns all data connected to these subscribers. """

        return [
            {
                'address': subscriber.address,
                'locale': subscriber.locale,
                'active': subscriber.active
            }
            for subscriber in self.query()
        ]

    def cleanup(self, file, mimetype, delete):
        """ Disables or deletes the subscribers in the given CSV. """

        csv, error = load_csv(file, mimetype, expected_headers=['address'])
        if error:
            return [error], 0

        addresses = [l.address.lower() for l in csv.lines if l.address]
        query = self.session.query(self.model_class)
        query = query.filter(
            func.lower(self.model_class.address).in_(addresses)
        )
        if delete:
            count = query.delete()
        else:
            query = query.filter(self.model_class.active.is_(True))
            count = query.count()
            for subscriber in query:
                subscriber.active = False

        return [], count


class EmailSubscriberCollection(SubscriberCollection):

    @property
    def model_class(self):
        return EmailSubscriber

    def handle_subscription(self, subscriber, request):
        """ Send the (new) subscriber a request to confirm the subscription.

        """

        from onegov.election_day.layouts import MailLayout  # circular

        token = request.new_url_safe_token({
            'address': subscriber.address,
            'locale': request.locale
        })
        optin = request.link(request.app.principal, 'optin-email')
        optin = f'{optin}?opaque={token}'
        optout = request.link(request.app.principal, 'optout-email')
        optout = f'{optout}?opaque={token}'

        # even though this is technically a transactional e-mail we send
        # it as marketing, since the actual subscription is sent as
        # a marketing e-mail as well
        title = request.translate(_("Please confirm your email"))
        request.app.send_marketing_email(
            subject=title,
            receivers=(subscriber.address, ),
            reply_to=formataddr((
                request.app.principal.name,
                request.app.principal.reply_to
                or request.app.mail['marketing']['sender']
            )),
            content=render_template(
                'mail_confirm_subscription.pt',
                request,
                {
                    'title': title,
                    'model': None,
                    'optin': optin,
                    'optout': optout,
                    'layout': MailLayout(self, request),
                }
            ),
            headers={
                'List-Unsubscribe': f'<{optout}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
            }
        )

    def confirm_subscription(self, address, locale):
        """ Confirm the subscription. """

        subscriber = self.by_address(address)
        if subscriber:
            subscriber.active = True
            subscriber.locale = locale
            return True
        return False

    def handle_unsubscription(self, subscriber, request):
        """ Send the subscriber a request to confirm the unsubscription.
        """

        from onegov.election_day.layouts import MailLayout  # circular

        token = request.new_url_safe_token({'address': subscriber.address})
        optout = request.link(request.app.principal, 'optout-email')
        optout = f'{optout}?opaque={token}'

        # even though this is technically a transactional e-mail we send
        # it as marketing, since the actual subscription is sent as
        # a marketing e-mail as well
        title = request.translate(_("Please confirm your unsubscription"))
        request.app.send_marketing_email(
            subject=title,
            receivers=(subscriber.address, ),
            reply_to=formataddr((
                request.app.principal.name,
                request.app.principal.reply_to
                or request.app.mail['marketing']['sender']
            )),
            content=render_template(
                'mail_confirm_unsubscription.pt',
                request,
                {
                    'title': title,
                    'model': None,
                    'optout': optout,
                    'layout': MailLayout(self, request),
                }
            ),
            headers={
                'List-Unsubscribe': f'<{optout}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
            }
        )

    def confirm_unsubscription(self, address):
        """ Confirm the unsubscription. """

        subscriber = self.by_address(address)
        if subscriber:
            subscriber.active = False
            return True
        return False


class SmsSubscriberCollection(SubscriberCollection):

    @property
    def model_class(self):
        return SmsSubscriber

    def handle_subscription(self, subscriber, request):
        """ Confirm the subscription by sending an SMS (if not already
        subscribed). There is no double-opt-in for SMS subscribers.

        """

        if not subscriber.active or subscriber.locale != request.locale:
            subscriber.locale = request.locale
            subscriber.active = True
            content = _(
                "Successfully subscribed to the SMS service. You will"
                " receive a SMS every time new results are published."
            )
            content = request.translate(content)
            request.app.send_sms(subscriber.address, content)

    def handle_unsubscription(self, subscriber, request):
        """ Deactivate the subscriber. There is no double-opt-out for SMS
        subscribers.

        """
        subscriber.active = False
