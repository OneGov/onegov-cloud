from onegov.core.templates import render_template
from onegov.town.layout import DefaultMailLayout


def send_html_mail(request, template, content, **kwargs):
    """" Sends an email rendered from the given template.

    Example:

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
