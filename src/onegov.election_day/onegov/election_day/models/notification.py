from json import dumps
from onegov.ballot.models import Election
from onegov.ballot.models import Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.core.utils import PostThread
from onegov.election_day import _
from onegov.election_day.models.subscriber import Subscriber
from onegov.election_day.utils import get_summary
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class Notification(Base, TimestampMixin):
    """ Stores triggered notifications. """

    __tablename__ = 'notifications'

    #: Identifies the notification
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The action made (e.g. the URL called)
    action = Column(Text, nullable=False)

    #: The last update of the corresponding election/vote
    last_change = Column(UTCDateTime, nullable=False)

    #: The corresponding election id
    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    #: The corresponding election
    election = relationship('Election', backref=backref('notifications'))

    #: The corresponding vote id
    vote_id = Column(Text, ForeignKey(Vote.id), nullable=True)

    #: The corresponding vote
    vote = relationship('Vote', backref=backref('notifications'))

    def update_from_model(self, model):
        """ Copy """
        self.last_change = model.last_result_change
        if isinstance(model, Election):
            self.election_id = model.id
        if isinstance(model, Vote):
            self.vote_id = model.id

    def trigger(self, request, model):
        """ Trigger the custom actions. """

        raise NotImplementedError


class WebhookNotification(Notification):

    def trigger(self, request, model):
        """ Posts the summary of the given vote or election to the webhook
        URL defined for this principal.

        This only works for external URL. If posting to server itself is
        needed, use a process instead of the thread:

            process = Process(target=send_post_request, args=(urls, data))
            process.start()

        """
        self.update_from_model(model)
        self.action = 'webhooks'

        webhooks = request.app.principal.webhooks
        if webhooks:
            summary = get_summary(model, request)
            data = dumps(summary).encode('utf-8')
            for url, headers in webhooks.items():
                headers = headers or {}
                headers['Content-Type'] = 'application/json; charset=utf-8'
                headers['Content-Length'] = len(data)
                PostThread(
                    url,
                    data,
                    tuple((key, value) for key, value in headers.items())
                ).start()


class SmsNotification(Notification):

    def trigger(self, request, model):
        """ Posts a link to the vote or election to all subscribers.

        This is done by writing files to a directory similary to maildir,
        sending the SMS is done using an external command, probably called
        by a cronjob.

        """
        self.update_from_model(model)
        self.action = 'sms'

        content = _(
            "New results are available on ${url}",
            mapping={'url': request.app.principal.sms_notification}
        )

        session = request.app.session()
        subscribers = session.query(Subscriber).all()
        for subscriber in subscribers:
            translator = request.app.translations.get(subscriber.locale)
            translated = translator.gettext(content) if translator else content
            translated = content.interpolate(translated)

            request.app.send_sms(subscriber.phone_number, translated)
