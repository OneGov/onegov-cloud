import json
import logging
import urllib.request

from _thread import start_new_thread
from onegov.ballot.models import Election, Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.election_day.utils import get_summary
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Text
from uuid import uuid4


log = logging.getLogger('onegov.election_day')  # noqa


class Notification(Base, TimestampMixin):
    """ Stores triggered notifications. """

    __tablename__ = 'notifications'

    #: Identifies the notification
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The action made (e.g. the URL called)
    action = Column(Text, nullable=False)

    #: The corresponding election
    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    #: The corresponding vote
    vote_id = Column(Text, ForeignKey(Vote.id), nullable=True)

    #: The last update of the corresponding election/vote
    last_change = Column(UTCDateTime)

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


def send_post_request(url, data, headers, timeout=30):
    """ """
    try:
        request = urllib.request.Request(url)
        for header in headers:
            request.add_header(header[0], header[1])
        urllib.request.urlopen(request, data, timeout)
    except Exception as e:
        log.error(
            'Error while sending a POST request to {}: {}'.format(
                url, str(e)
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
        urls = request.app.principal.webhooks
        if urls:
            self.update_from_model(model)
            self.action = 'webhooks'

            summary = get_summary(model, request)
            data = json.dumps(summary).encode('utf-8')
            headers = (
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Content-Length', len(data))
            )
            for url in urls:
                start_new_thread(send_post_request, (url, data, headers))
