from onegov.core.templates import render_template
from onegov.org.layout import DefaultMailLayout
from onegov.org.utils import ticket_directory_groups_of_type,\
    subset_of_interest


def send_html_mail(request, template, content, **kwargs):
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

    kwargs['subject'] = request.translate(kwargs['subject'])

    if 'layout' not in content:
        content['layout'] = DefaultMailLayout(content['model'], request)

    if 'title' not in content:
        content['title'] = kwargs['subject']

    kwargs['content'] = render_template(template, request, content)

    # the email is queued here, not actually sent!
    request.app.send_email(**kwargs)


def send_transactional_html_mail(*args, **kwargs):
    kwargs['category'] = 'transactional'
    return send_html_mail(*args, **kwargs)


def send_marketing_html_mail(*args, **kwargs):
    kwargs['category'] = 'marketing'
    return send_html_mail(*args, **kwargs)


def predicate_should_include_ticket(ticket, request):

    # If the ticket is not a directory ticket, it should be included
    if ticket.handler_code != 'DIR':
        return True

    user_group_directories = subset_of_interest(
        request, ticket.group
    )

    # If the ticket is a directory ticket, and the user is not part of a
    # UserGroup that defines directories, it should be included
    if user_group_directories is None:
        return True

    # Else, it should be included if the ticket's directory group is part of
    # the ones defined in the usergroup
    return user_group_directories in ticket_directory_groups_of_type(
        request.session
    )


def send_ticket_mail(request, template, subject, receivers, ticket,
                     content=None, force=False, send_self=False, **kwargs):
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

        if not predicate_should_include_ticket(ticket, request.session):
            return

    subject = ticket.reference(request) + ': ' + request.translate(subject)

    content = content or {}

    # legacy behavior
    if 'model' not in content:
        content['model'] = ticket

    if 'ticket' not in content:
        content['ticket'] = ticket

    return send_transactional_html_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=receivers,
        content=content,
        **kwargs)
