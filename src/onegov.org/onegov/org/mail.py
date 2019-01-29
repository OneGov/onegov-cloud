from onegov.core.templates import render_template
from onegov.org.layout import DefaultMailLayout


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


def send_ticket_mail(request, template, subject, receivers, ticket,
                     content=None, force=False, **kwargs):

    if not force:

        if ticket.muted:
            return

        if request.current_username in receivers:
            if len(receivers) == 1:
                return

            receivers = tuple(
                r for r in receivers if r != request.current_username
            )

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
