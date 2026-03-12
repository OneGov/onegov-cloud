from __future__ import annotations

from onegov.core.templates import render_template
from onegov.org.layout import DefaultMailLayout
from onegov.ticket import Ticket, TicketCollection
from ulid import ULID


from typing import cast, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import Iterable, Sequence
    from email.headerregistry import Address
    from onegov.core.mail import Attachment
    from onegov.core.types import SequenceOrScalar
    from onegov.org.request import OrgRequest
    from typing import TypedDict, Required
    from typing_extensions import Unpack

    class TicketEmailExtraArguments(TypedDict, total=False):
        reply_to: Address | str | None
        cc: SequenceOrScalar[Address | str]
        headers: dict[str, str] | None

    class EmailArguments(TicketEmailExtraArguments, total=False):
        subject: Required[str]
        receivers: Required[SequenceOrScalar[Address | str]]
        bcc: SequenceOrScalar[Address | str]
        attachments: Iterable[Attachment | StrPath]

    class EmailArgumentsWithCategory(EmailArguments, total=False):
        category: Literal['marketing', 'transactional']

    class AllEmailArguments(EmailArgumentsWithCategory):
        content: str


def send_html_mail(
    request: OrgRequest,
    template: str,
    content: dict[str, Any],
    **kwargs: Unpack[EmailArgumentsWithCategory]
) -> None:
    """" Sends an email rendered from the given template.

    Example::

        send_html_mail(request, 'mail_template.pt', {'model': self},
            subject=_("Test subject")
            receivers=('recipient@example.org', )
        )

    """

    assert 'model' in content
    assert 'subject' in kwargs
    assert 'receivers' in kwargs

    kwargs = cast('AllEmailArguments', kwargs)

    kwargs['subject'] = request.translate(kwargs['subject'])

    if 'layout' not in content:
        content['layout'] = DefaultMailLayout(content['model'], request)

    if 'title' not in content:
        content['title'] = kwargs['subject']

    kwargs['content'] = render_template(template, request, content)

    # the email is queued here, not actually sent!
    request.app.send_email(**kwargs)


def send_transactional_html_mail(
    request: OrgRequest,
    template: str,
    content: dict[str, Any],
    **kwargs: Unpack[EmailArguments]
) -> None:

    send_html_mail(
        request,
        template,
        content,
        category='transactional',
        **kwargs
    )


def send_marketing_html_mail(
    request: OrgRequest,
    template: str,
    content: dict[str, Any],
    **kwargs: Unpack[EmailArguments]
) -> None:

    send_html_mail(
        request,
        template,
        content,
        category='marketing',
        **kwargs
    )


def send_ticket_mail(
    request: OrgRequest,
    template: str,
    subject: str,
    receivers: Sequence[Address | str],
    ticket: Ticket,
    content: dict[str, Any] | None = None,
    force: bool = False,
    send_self: bool = False,
    bcc: SequenceOrScalar[Address | str] = (),
    attachments: Iterable[Attachment | StrPath] = (),
    **kwargs: Unpack[TicketEmailExtraArguments]
) -> None:

    org = request.app.org
    if not force:

        if org.mute_all_tickets:
            return

        if ticket.muted:
            return

        skip_handler_codes_o = org.tickets_skip_opening_email or []
        skip_handler_codes_c = org.tickets_skip_closing_email or []
        opened = ticket.state == 'open'
        if opened and ticket.handler_code in skip_handler_codes_o:
            return

        if opened and request.auto_accept(ticket):
            return

        if ticket.state == 'closed':
            if request.auto_accept(ticket):
                return
            if ticket.handler_code in skip_handler_codes_c:
                return

        if not send_self and request.current_username in receivers:
            if len(receivers) == 1:
                return

            receivers = tuple(
                r for r in receivers if r != request.current_username
            )

    # FIXME: Should this method be part of the base Ticket?
    assert hasattr(ticket, 'reference')
    subject = ticket.reference(request) + ': ' + request.translate(subject)

    content = content or {}

    # legacy behavior
    if 'model' not in content:
        content['model'] = ticket

    if 'ticket' not in content:
        content['ticket'] = ticket

    if 'reply_to' not in kwargs and ticket.handler.reply_to:
        kwargs['reply_to'] = ticket.handler.reply_to

    headers = kwargs.setdefault('headers', {})
    if headers is None:
        headers = kwargs['headers'] = {}

    message_id = headers.setdefault(
        'Message-ID',
        # NOTE: We use ULIDs so we can easily get a chronological history
        #       even if there are multiple tickets grouped into the same
        #       e-mail thread.
        f'<{ULID()}@{request.domain}>'
    )
    if ticket.customer_message_ids is None:
        ticket.customer_message_ids = []

    references = sorted(
        customer_message_id
        for customer_message_ids, in TicketCollection(request.session)
        .by_order(ticket.order_id)
        .with_entities(Ticket.customer_message_ids)
        if customer_message_ids
        for customer_message_id in customer_message_ids
    ) if ticket.order_id else ticket.customer_message_ids

    if references:
        # we are replying to the last message sent for this group of tickets
        headers.setdefault('In-Reply-To', references[-1])

        # and we are also referencing the 10 latest messages
        headers.setdefault('References', ' '.join(references[-10:]))

    # finally append the new message id
    ticket.customer_message_ids.append(message_id)

    # we flush in order to make sure subsequent calls to `send_ticket_mail`
    # in the same request will have access to the full list of message ids
    request.session.flush()

    send_transactional_html_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=receivers,
        content=content,
        bcc=bcc,
        attachments=attachments,
        **kwargs
    )
