from __future__ import annotations

from itertools import chain
from onegov.election_day import _
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import EmailNotification
from onegov.election_day.models import Notification
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import Vote
from onegov.election_day.models import WebhookNotification


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Iterator
    from collections.abc import Sequence
    from onegov.election_day.request import ElectionDayRequest
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session


class NotificationCollection:

    def __init__(self, session: Session):
        self.session = session

    def query(self) -> Query[Notification]:
        return self.session.query(Notification)

    def by_model(
        self,
        model: Election | ElectionCompound | Vote,
        current: bool = True
    ) -> list[Notification]:
        """ Returns the notification for the given election or vote and its
        modification times. Only returns the current by default.

        """

        query = self.query()
        if isinstance(model, Election):
            query = query.filter(Notification.election_id == model.id)
        if isinstance(model, ElectionCompound):
            query = query.filter(Notification.election_compound_id == model.id)
        if isinstance(model, Vote):
            query = query.filter(Notification.vote_id == model.id)

        if current:
            query = query.filter(
                Notification.last_modified == model.last_modified
            )
        else:
            query = query.order_by(
                Notification.last_change.desc(), Notification.type
            )

        return query.all()

    def trigger(
        self,
        request: ElectionDayRequest,
        model: Election | ElectionCompound | Vote,
        options: Collection[str]
    ) -> None:
        """ Triggers and adds the selected notifications. """

        notification: Notification

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

    def trigger_summarized(
        self,
        request: ElectionDayRequest,
        elections: Sequence[Election],
        election_compounds: Sequence[ElectionCompound],
        votes: Sequence[Vote],
        options: Collection[str]
    ) -> None:
        """ Triggers and adds a single notification for all given votes and
        elections.

        """

        model_chain: Iterator[Election | ElectionCompound | Vote]
        model_chain = chain(elections, election_compounds, votes)
        models = tuple(model_chain)

        if not models or not options:
            return

        notification: Notification

        if 'email' in options and request.app.principal.email_notification:
            completed = True
            for model in models:
                completed &= model.completed
                notification = EmailNotification()
                notification.update_from_model(model)
                self.session.add(notification)

            notification = EmailNotification()
            notification.send_emails(
                request,
                elections,
                election_compounds,
                votes,
                _('The final results are available') if completed else
                _('New results are available')
            )

        if 'sms' in options and request.app.principal.sms_notification:
            for model in models:
                notification = SmsNotification()
                notification.update_from_model(model)
                self.session.add(notification)

            notification = SmsNotification()
            notification.send_sms(
                request,
                elections,
                election_compounds,
                votes,
                _(
                    'New results are available on ${url}',
                    mapping={'url': request.app.principal.sms_notification}
                )
            )

        if 'webhooks' in options and request.app.principal.webhooks:
            for model in models:
                notification = WebhookNotification()
                notification.trigger(request, model)
                self.session.add(notification)

        self.session.flush()
