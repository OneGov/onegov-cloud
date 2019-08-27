from onegov.ballot.models import Election
from onegov.ballot.models import Vote
from onegov.core.custom import json
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.core.templates import render_template
from onegov.core.utils import PostThread
from onegov.election_day import _
from onegov.election_day.models.subscriber import EmailSubscriber
from onegov.election_day.models.subscriber import SmsSubscriber
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

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': None
    }

    #: Identifies the notification
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The last update of the corresponding election/vote
    last_modified = Column(UTCDateTime, nullable=True)

    #: The corresponding election id
    election_id = Column(
        Text, ForeignKey(Election.id, onupdate='CASCADE'), nullable=True
    )

    #: The corresponding election
    election = relationship('Election', backref=backref('notifications'))

    #: The corresponding vote id
    vote_id = Column(
        Text, ForeignKey(Vote.id, onupdate='CASCADE'), nullable=True
    )

    #: The corresponding vote
    vote = relationship('Vote', backref=backref('notifications'))

    def update_from_model(self, model):
        """ Copy """

        self.last_modified = model.last_modified
        if isinstance(model, Election):
            self.election_id = model.id
        if isinstance(model, Vote):
            self.vote_id = model.id

    def trigger(self, request, model):
        """ Trigger the custom actions. """

        raise NotImplementedError


class WebhookNotification(Notification):

    __mapper_args__ = {'polymorphic_identity': 'webhooks'}

    def trigger(self, request, model):
        """ Posts the summary of the given vote or election to the webhook
        URL defined for this principal.

        This only works for external URLs. If posting to the server itself is
        needed, use a process instead of the thread:

            process = Process(target=send_post_request, args=(urls, data))
            process.start()

        """
        self.update_from_model(model)

        webhooks = request.app.principal.webhooks
        if webhooks:
            summary = get_summary(model, request)
            data = json.dumps(summary).encode('utf-8')
            for url, headers in webhooks.items():
                headers = headers or {}
                headers['Content-Type'] = 'application/json; charset=utf-8'
                headers['Content-Length'] = len(data)
                PostThread(
                    url,
                    data,
                    tuple((key, value) for key, value in headers.items())
                ).start()


class EmailNotification(Notification):

    __mapper_args__ = {'polymorphic_identity': 'email'}

    def set_locale(self, request, locale=None):
        """ Changes the locale of the request.

        (Re)stores the intial locale if no locale is given.

        """
        if not locale:
            locale = request.__dict__.setdefault('_old_locale', request.locale)

        request.locale = locale
        if 'translator' in request.__dict__:
            del request.__dict__['translator']

    def send_emails(self, request, elections, votes, subject=None):
        """ Sends the results of the vote or election to all subscribers.

        Adds unsubscribe headers (RFC 2369, RFC 8058).

        """
        from onegov.election_day.layouts import MailLayout  # circular

        if not elections and not votes:
            return

        self.set_locale(request)

        reply_to = '{} <{}>'.format(
            request.app.principal.name,
            request.app.mail['marketing']['sender']
        )

        for locale in request.app.locales:
            addresses = request.session.query(EmailSubscriber.address)
            addresses = addresses.filter(EmailSubscriber.locale == locale)
            addresses = addresses.all()
            addresses = [address[0] for address in addresses]
            if not addresses:
                continue

            self.set_locale(request, locale)

            layout = MailLayout(self, request)

            if subject:
                subject_ = request.translate(subject)
            else:
                subject_ = layout.subject((elections + votes)[0])

            content = render_template(
                'mail_results.pt',
                request,
                {
                    'title': subject_,
                    'elections': elections,
                    'votes': votes,
                    'layout': layout
                }
            )

            for address in addresses:
                token = request.new_url_safe_token({'address': address})
                optout_custom = f'{layout.optout_link}?opaque={token}'
                request.app.send_marketing_email(
                    subject=subject_,
                    receivers=(address, ),
                    reply_to=reply_to,
                    content=content.replace(layout.optout_link, optout_custom),
                    headers={
                        'List-Unsubscribe': f'<{optout_custom}>',
                        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
                    }
                )

        self.set_locale(request)

    def trigger(self, request, model):
        """ Sends the results of the vote or election to all subscribers.

        Adds unsubscribe headers (RFC 2369, RFC 8058).

        """

        self.update_from_model(model)

        self.send_emails(
            request,
            elections=[model] if isinstance(model, Election) else [],
            votes=[model] if isinstance(model, Vote) else []
        )


class SmsNotification(Notification):

    __mapper_args__ = {'polymorphic_identity': 'sms'}

    def send_sms(self, request, content):
        """ Sends the given text to all subscribers. """

        subscribers = request.session.query(SmsSubscriber).all()
        for subscriber in subscribers:
            translator = request.app.translations.get(subscriber.locale)
            translated = translator.gettext(content) if translator else content
            translated = content.interpolate(translated)

            request.app.send_sms(subscriber.address, translated)

    def trigger(self, request, model):
        """ Posts a link to the vote or election to all subscribers.

        This is done by writing files to a directory similary to maildir,
        sending the SMS is done using an external command, probably called
        by a cronjob.

        """
        self.update_from_model(model)

        if model.completed:
            content = _(
                "Final results are available on ${url}",
                mapping={'url': request.app.principal.sms_notification}
            )
        else:
            content = _(
                "New intermediate results are available on ${url}",
                mapping={'url': request.app.principal.sms_notification}
            )

        self.send_sms(request, content)
