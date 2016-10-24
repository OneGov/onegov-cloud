import json
import logging
import urllib.request

from onegov.ballot.models import Election, Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.election_day.utils import get_summary
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Text
from threading import Thread
from uuid import uuid4


log = logging.getLogger('onegov.election_day')  # noqa


class Notification(Base, TimestampMixin):
    """ Stores triggered notifications. """

    __tablename__ = 'notifications'

    #: Identifies the notification
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The action made (e.g. the URL called)
    action = Column(Text, nullable=False)

    #: The last update of the corresponding election/vote
    last_change = Column(UTCDateTime, nullable=False)

    #: The corresponding election
    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    #: The corresponding vote
    vote_id = Column(Text, ForeignKey(Vote.id), nullable=True)

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


class WebhookThread(Thread):

    def __init__(self, url, data, headers, timeout=30):
        Thread.__init__(self)
        self.url = url
        self.data = data
        self.headers = headers
        self.timeout = timeout

    def run(self):
        try:
            request = urllib.request.Request(self.url)
            for header in self.headers:
                request.add_header(header[0], header[1])
            urllib.request.urlopen(request, self.data, self.timeout)
        except Exception as e:
            log.error(
                'Error while sending a POST request to {}: {}'.format(
                    self.url, str(e)
                )
            )


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
            data = json.dumps(summary).encode('utf-8')
            for url, headers in webhooks.items():
                headers = headers or {}
                headers['Content-Type'] = 'application/json; charset=utf-8'
                headers['Content-Length'] = len(data)
                WebhookThread(
                    url,
                    data,
                    tuple((key, value) for key, value in headers.items())
                ).start()
