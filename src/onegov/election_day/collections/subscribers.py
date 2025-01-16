from __future__ import annotations

from email.headerregistry import Address
from onegov.core.collection import Pagination
from onegov.core.templates import render_template
from onegov.election_day import _
from onegov.election_day.formats.imports.common import load_csv
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import Subscriber
from sedate import utcnow
from sqlalchemy import func


from typing import Any
from typing import IO
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.formats.imports.common import FileImportError
    from onegov.election_day.request import ElectionDayRequest
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self
    from uuid import UUID


_S = TypeVar('_S', bound=Subscriber)


class SubscriberCollection(Pagination[_S]):

    page: int

    def __init__(
        self: SubscriberCollection[Subscriber],
        session: Session,
        page: int = 0,
        term: str | None = None,
        active_only: bool | None = True
    ):
        super().__init__(page)
        self.session = session
        self.term = term
        self.active_only = active_only

    @property
    def model_class(self) -> type[_S]:
        return Subscriber  # type:ignore[return-value]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.term == other.term
            and self.active_only == other.active_only
        )

    def subset(self) -> Query[_S]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index)

    def for_active_only(self, active_only: bool) -> Self:
        return self.__class__(self.session, 0, self.term, active_only)

    def add(
        self,
        address: str,
        domain: str | None,
        domain_segment: str | None,
        locale: str,
        active: bool
    ) -> _S:
        subscriber = self.model_class(
            address=address,
            domain=domain,
            domain_segment=domain_segment,
            locale=locale,
            active=active
        )
        self.session.add(subscriber)
        self.session.flush()
        return subscriber

    def query(self, active_only: bool | None = None) -> Query[_S]:
        query = self.session.query(self.model_class)

        active_only = self.active_only if active_only is None else active_only
        if active_only:
            query = query.filter(self.model_class.active.is_(True))

        if self.term:
            query = query.filter(self.model_class.address.contains(self.term))
            self.batch_size = query.count()

        query = query.order_by(self.model_class.address)

        return query

    def by_id(self, id: UUID) -> _S | None:
        """ Returns the subscriber by its id. """

        query = self.query(active_only=False)
        query = query.filter(self.model_class.id == id)
        return query.first()

    def by_address(
        self,
        address: str,
        domain: str | None,
        domain_segment: str | None,
    ) -> _S | None:
        """ Returns the (first) subscriber by its address. """

        query = self.query(active_only=False)
        query = query.filter(
            self.model_class.address == address,
            self.model_class.domain == domain,
            self.model_class.domain_segment == domain_segment,
        )
        return query.first()

    def initiate_subscription(
        self,
        address: str,
        domain: str | None,
        domain_segment: str | None,
        request: ElectionDayRequest
    ) -> _S:
        """ Initiate the subscription process.

        Might be used to change the locale by re-subscribing.

        """

        subscriber = self.by_address(address, domain, domain_segment)
        if not subscriber:
            locale = request.locale
            assert locale is not None
            subscriber = self.add(
                address, domain, domain_segment, locale, False
            )

        self.handle_subscription(subscriber, domain, domain_segment, request)

        return subscriber

    def handle_subscription(
        self,
        subscriber: _S,
        domain: str | None,
        domain_segment: str | None,
        request: ElectionDayRequest
    ) -> None:
        """ Send the subscriber a request to confirm the subscription. """

        raise NotImplementedError()

    def initiate_unsubscription(
        self,
        address: str,
        domain: str | None,
        domain_segment: str | None,
        request: ElectionDayRequest
    ) -> None:
        """ Initiate the unsubscription process. """

        subscriber = self.by_address(address, domain, domain_segment)
        if subscriber:
            self.handle_unsubscription(subscriber, request)

    def handle_unsubscription(
        self,
        subscriber: _S,
        request: ElectionDayRequest
    ) -> None:
        """ Send the subscriber a request to confirm the unsubscription. """

        raise NotImplementedError()

    def export(self) -> list[dict[str, Any]]:
        """ Returns all data connected to these subscribers. """

        return [
            {
                'address': subscriber.address,
                'domain': subscriber.domain,
                'domain_segment': subscriber.domain_segment,
                'locale': subscriber.locale,
                'active_since': subscriber.active_since,
                'inactive_since': subscriber.inactive_since,
                'active': subscriber.active,
            }
            for subscriber in self.query()
        ]

    def cleanup(
        self,
        file: IO[bytes],
        mimetype: str,
        delete: bool
    ) -> tuple[list[FileImportError], int]:
        """ Disables or deletes the subscribers in the given CSV.

        Ignores domain and domain segment, as this is inteded to cleanup
        bounced addresses.
        """

        csv, error = load_csv(file, mimetype, expected_headers=['address'])
        if error:
            return [error], 0

        assert csv is not None
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


class EmailSubscriberCollection(SubscriberCollection[EmailSubscriber]):

    @property
    def model_class(self) -> type[EmailSubscriber]:
        return EmailSubscriber

    def handle_subscription(
        self,
        subscriber: EmailSubscriber,
        domain: str | None,
        domain_segment: str | None,
        request: ElectionDayRequest
    ) -> None:
        """ Send the (new) subscriber a request to confirm the subscription.

        """

        from onegov.election_day.layouts import MailLayout  # circular

        token = request.new_url_safe_token({
            'address': subscriber.address,
            'domain': domain,
            'domain_segment': domain_segment,
            'locale': request.locale
        })
        optin = request.link(request.app.principal, 'optin-email')
        optin = f'{optin}?opaque={token}'
        optout = request.link(request.app.principal, 'optout-email')
        optout = f'{optout}?opaque={token}'

        # even though this is technically a transactional e-mail we send
        # it as marketing, since the actual subscription is sent as
        # a marketing e-mail as well
        title = request.translate(_('Please confirm your email'))
        request.app.send_marketing_email(
            subject=title,
            receivers=(subscriber.address, ),
            reply_to=Address(
                display_name=request.app.principal.name or '',
                addr_spec=request.app.principal.reply_to
                or request.app.mail['marketing']['sender']  # type:ignore
            ),
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

    def confirm_subscription(
        self,
        address: str,
        domain: str | None,
        domain_segment: str | None,
        locale: str,
    ) -> bool:
        """ Confirm the subscription. """

        subscriber = self.by_address(address, domain, domain_segment)
        if subscriber:
            if not subscriber.active:
                subscriber.active_since = utcnow()
                subscriber.inactive_since = None
            subscriber.active = True
            subscriber.locale = locale
            return True
        return False

    def handle_unsubscription(
        self,
        subscriber: EmailSubscriber,
        request: ElectionDayRequest
    ) -> None:
        """ Send the subscriber a request to confirm the unsubscription.
        """

        from onegov.election_day.layouts import MailLayout  # circular

        token = request.new_url_safe_token({
            'address': subscriber.address,
            'domain': subscriber.domain,
            'domain_segment': subscriber.domain_segment
        })
        optout = request.link(request.app.principal, 'optout-email')
        optout = f'{optout}?opaque={token}'

        # even though this is technically a transactional e-mail we send
        # it as marketing, since the actual subscription is sent as
        # a marketing e-mail as well
        title = request.translate(_('Please confirm your unsubscription'))
        request.app.send_marketing_email(
            subject=title,
            receivers=(subscriber.address, ),
            reply_to=Address(
                display_name=request.app.principal.name or '',
                addr_spec=request.app.principal.reply_to
                or request.app.mail['marketing']['sender']  # type:ignore
            ),
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

    def confirm_unsubscription(
        self,
        address: str,
        domain: str | None,
        domain_segment: str | None,
    ) -> bool:
        """ Confirm the unsubscription. """

        subscriber = self.by_address(address, domain, domain_segment)
        if subscriber:
            if subscriber.active:
                subscriber.inactive_since = utcnow()
            subscriber.active = False
            return True
        return False


class SmsSubscriberCollection(SubscriberCollection[SmsSubscriber]):

    @property
    def model_class(self) -> type[SmsSubscriber]:
        return SmsSubscriber

    def handle_subscription(
        self,
        subscriber: SmsSubscriber,
        domain: str | None,
        domain_segment: str | None,
        request: ElectionDayRequest
    ) -> None:
        """ Confirm the subscription by sending an SMS (if not already
        subscribed). There is no double-opt-in for SMS subscribers.

        """

        if not subscriber.active or subscriber.locale != request.locale:
            assert request.locale is not None
            if not subscriber.active:
                subscriber.active_since = utcnow()
                subscriber.inactive_since = None
            subscriber.locale = request.locale
            subscriber.active = True
            content = request.translate(_(
                'Successfully subscribed to the SMS service. You will'
                ' receive a SMS every time new results are published.'
            ))
            request.app.send_sms(subscriber.address, content)

    def handle_unsubscription(
        self,
        subscriber: SmsSubscriber,
        request: ElectionDayRequest
    ) -> None:
        """ Deactivate the subscriber. There is no double-opt-out for SMS
        subscribers.

        """
        if subscriber.active:
            subscriber.inactive_since = utcnow()
        subscriber.active = False
