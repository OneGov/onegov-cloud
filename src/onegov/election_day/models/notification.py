from __future__ import annotations

from email.headerregistry import Address
from itertools import chain
from onegov.core.custom import json
from onegov.core.html import html_to_text
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.core.templates import render_template
from onegov.core.utils import PostThread
from onegov.election_day import _
from onegov.election_day.models.election import Election
from onegov.election_day.models.election_compound import ElectionCompound
from onegov.election_day.models.subscriber import EmailSubscriber
from onegov.election_day.models.subscriber import SmsSubscriber
from onegov.election_day.models.vote import Vote
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator
    from collections.abc import Sequence
    from datetime import datetime
    from onegov.core.types import EmailJsonDict
    from onegov.election_day.request import ElectionDayRequest
    from translationstring import TranslationString


class Notification(Base, TimestampMixin):
    """ Stores triggered notifications. """

    __tablename__ = 'notifications'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    #: Identifies the notification
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The last update of the corresponding election/vote
    last_modified: Column[datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )

    #: The corresponding election id
    election_id: Column[str | None] = Column(
        Text,
        ForeignKey(Election.id, onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: The corresponding election
    election: relationship[Election | None] = relationship(
        'Election',
        back_populates='notifications'
    )

    #: The corresponding election compound id
    election_compound_id: Column[str | None] = Column(
        Text,
        ForeignKey(
            ElectionCompound.id, onupdate='CASCADE', ondelete='CASCADE'
        ),
        nullable=True
    )

    #: The corresponding election compound
    election_compound: relationship[ElectionCompound | None] = relationship(
        'ElectionCompound',
        back_populates='notifications'
    )

    #: The corresponding vote id
    vote_id: Column[str | None] = Column(
        Text,
        ForeignKey(Vote.id, onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: The corresponding vote
    vote: relationship[Vote | None] = relationship(
        'Vote',
        back_populates='notifications'
    )

    def update_from_model(
        self,
        model: Election | ElectionCompound | Vote
    ) -> None:
        """ Copy """

        self.last_modified = model.last_modified
        if isinstance(model, Election):
            self.election_id = model.id
        elif isinstance(model, ElectionCompound):
            self.election_compound_id = model.id
        elif isinstance(model, Vote):
            self.vote_id = model.id

    def trigger(
        self,
        request: ElectionDayRequest,
        model: Election | ElectionCompound | Vote
    ) -> None:
        """ Trigger the custom actions. """

        raise NotImplementedError


class WebhookNotification(Notification):

    __mapper_args__ = {'polymorphic_identity': 'webhooks'}

    def trigger(
        self,
        request: ElectionDayRequest,
        model: Election | ElectionCompound | Vote
    ) -> None:
        """ Posts the summary of the given vote or election to the webhook
        URL defined for this principal.

        This only works for external URLs. If posting to the server itself is
        needed, use a process instead of the thread:

            process = Process(target=send_post_request, args=(urls, data))
            process.start()

        """
        from onegov.election_day.utils import get_summary

        self.update_from_model(model)

        webhooks = request.app.principal.webhooks
        if webhooks:
            summary = get_summary(model, request)
            data = json.dumps_bytes(summary)
            for url, headers in webhooks.items():
                headers = headers or {}
                headers['Content-Type'] = 'application/json; charset=utf-8'
                headers['Content-Length'] = str(len(data))
                PostThread(
                    url,
                    data,
                    tuple((key, value) for key, value in headers.items())
                ).start()


class EmailNotification(Notification):

    __mapper_args__ = {'polymorphic_identity': 'email'}

    def set_locale(
        self,
        request: ElectionDayRequest,
        locale: str | None = None
    ) -> None:
        """ Changes the locale of the request.

        (Re)stores the intial locale if no locale is given.

        """
        if not locale:
            locale = request.__dict__.setdefault('_old_locale', request.locale)

        request.locale = locale
        if 'translator' in request.__dict__:
            del request.__dict__['translator']

    def send_emails(
        self,
        request: ElectionDayRequest,
        elections: Sequence[Election],
        election_compounds: Sequence[ElectionCompound],
        votes: Sequence[Vote],
        subject: str | None = None
    ) -> None:
        """ Sends the results of the vote or election to all subscribers.

        Adds unsubscribe headers (RFC 2369, RFC 8058).

        """
        from onegov.election_day.layouts import MailLayout  # circular
        from onegov.election_day.utils import segment_models

        if not elections and not election_compounds and not votes:
            return

        self.set_locale(request)

        groups = segment_models(elections, election_compounds, votes)

        reply_to = Address(
            display_name=request.app.principal.name or '',
            addr_spec=request.app.principal.reply_to
            or request.app.mail['marketing']['sender']  # type:ignore[index]
        )

        # We use a generator function to submit the email batch since that
        # is significantly more memory efficient for large batches.
        def email_iter() -> Iterator[EmailJsonDict]:
            for locale in request.app.locales:
                for group in groups:
                    query = request.session.query(EmailSubscriber.address)
                    query = query.filter(
                        EmailSubscriber.active.is_(True),
                        EmailSubscriber.locale == locale,
                        group.filter
                    )
                    addresses = {address for address, in query}
                    if not addresses:
                        continue

                    self.set_locale(request, locale)

                    layout = MailLayout(self, request)

                    if subject:
                        subject_ = request.translate(subject)
                    else:
                        items: Iterator[Election | ElectionCompound | Vote]
                        items = chain(
                            group.election_compounds,
                            group.elections,
                            group.votes
                        )
                        subject_ = layout.subject(next(items))

                    content = render_template(
                        'mail_results.pt',
                        request,
                        {
                            'title': subject_,
                            'elections': group.elections,
                            'election_compounds': group.election_compounds,
                            'votes': group.votes,
                            'layout': layout
                        }
                    )
                    plaintext = html_to_text(content)

                    for address in addresses:
                        token = request.new_url_safe_token({
                            'address': address
                        })
                        optout_custom = f'{layout.optout_link}?opaque={token}'
                        yield request.app.prepare_email(
                            subject=subject_,
                            receivers=(address, ),
                            reply_to=reply_to,
                            content=content.replace(
                                layout.optout_link,
                                optout_custom
                            ),
                            plaintext=plaintext.replace(
                                layout.optout_link,
                                optout_custom
                            ),
                            headers={
                                'List-Unsubscribe': f'<{optout_custom}>',
                                'List-Unsubscribe-Post':
                                    'List-Unsubscribe=One-Click'
                            }
                        )

        request.app.send_marketing_email_batch(email_iter())
        self.set_locale(request)

    def trigger(
        self,
        request: ElectionDayRequest,
        model: Election | ElectionCompound | Vote
    ) -> None:
        """ Sends the results of the vote, election or election compound to
        all subscribers.

        Adds unsubscribe headers (RFC 2369, RFC 8058).

        """

        self.update_from_model(model)

        self.send_emails(
            request,
            elections=[model] if isinstance(model, Election) else [],
            election_compounds=(
                [model] if isinstance(model, ElectionCompound) else []
            ),
            votes=[model] if isinstance(model, Vote) else []
        )


class SmsNotification(Notification):

    __mapper_args__ = {'polymorphic_identity': 'sms'}

    def send_sms(
        self,
        request: ElectionDayRequest,
        elections: Sequence[Election],
        election_compounds: Sequence[ElectionCompound],
        votes: Sequence[Vote],
        content: TranslationString,
        url: str | None = None
    ) -> None:
        """ Sends the given text to all subscribers. """

        from onegov.election_day.utils import segment_models

        groups = segment_models(elections, election_compounds, votes)

        query = request.session.query(
            SmsSubscriber.locale,
            func.array_agg(SmsSubscriber.address),
        )
        query = query.filter(
            SmsSubscriber.active.is_(True),
            or_(*(group.filter for group in groups))
        )
        query = query.group_by(SmsSubscriber.locale)
        query = query.order_by(SmsSubscriber.locale)

        for locale, addresses in query:
            translator = request.app.translations.get(locale)
            translated = translator.gettext(content) if translator else content
            if url is not None and len(translated) + len(url) <= 154:
                # If the given url fits into a single SMS, then prefer it
                # over the generic one it's bound to by default
                content = content % {'url': url}
            translated = content.interpolate(translated)

            request.app.send_sms(tuple(set(addresses)), translated)

    def trigger(
        self,
        request: ElectionDayRequest,
        model: Election | ElectionCompound | Vote
    ) -> None:
        """ Posts a link to the vote or election to all subscribers.

        This is done by writing files to a directory similary to maildir,
        sending the SMS is done using an external command, probably called
        by a cronjob.

        """
        self.update_from_model(model)

        self.send_sms(
            request,
            elections=[model] if isinstance(model, Election) else [],
            election_compounds=(
                [model] if isinstance(model, ElectionCompound) else []
            ),
            votes=[model] if isinstance(model, Vote) else [],
            content=_(
                'New results are available on ${url}',
                mapping={'url': request.app.principal.sms_notification}
            ),
            # NOTE: A SiteLocale link would be nicer UX, but that will make
            #       the URL significantly longer, so we take what we can get
            url=request.link(model)
        )
