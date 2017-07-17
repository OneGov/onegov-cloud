from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.templates import render_template
from onegov.core.utils import append_query_param
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.views import get_user_id
from webob.exc import HTTPForbidden


@GazetteApp.html(
    model=GazetteNotice,
    template='notice.pt',
    permission=Personal
)
def view_notice(self, request):
    """ View a notice notice.

    View the notice and its meta data. This is the main view for the notices
    to do the state changes.

    """

    layout = Layout(self, request)

    actions = []
    if request.is_personal(self) and not request.is_private(self):
        if self.state == 'drafted' or self.state == 'rejected':
            actions.append(
                (_("Submit"), request.link(self, 'submit'), 'primary')
            )
            actions.append(
                (_("Edit"), request.link(self, 'edit'), 'secondary')
            )
            actions.append(
                (_("Delete"), request.link(self, 'delete'), 'alert right')
            )
        if self.state == 'published':
            actions.append(
                (
                    _("Copy"),
                    append_query_param(
                        request.link(
                            GazetteNoticeCollection(
                                request.app.session(), state='published'
                            ),
                            name='new-notice'
                        ),
                        'source', self.id
                    ),
                    'secondary'
                )
            )
    if request.is_private(self):
        if self.state == 'submitted':
            actions.append(
                (_("Publish"), request.link(self, 'publish'), 'primary')
            )
            actions.append(
                (_("Edit"), request.link(self, 'edit'), 'secondary')
            )
            actions.append(
                (_("Reject"), request.link(self, 'reject'), 'alert right')
            )
    actions.append(
        (_("Preview"), request.link(self, 'preview'), 'secondary')
    )

    return {
        'layout': layout,
        'notice': self,
        'actions': actions
    }


@GazetteApp.html(
    model=GazetteNotice,
    template='preview.pt',
    name='preview',
    permission=Personal
)
def view_notice_preview(self, request):
    """ Preview the notice. """

    layout = Layout(self, request)

    return {
        'layout': layout,
        'notice': self
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='edit',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def edit_notice(self, request, form):
    """ Edit a notice.

    The issue can not be changed. This view is used by the editors and
    publishers. Editors may only edit their own notices, publishers may edit
    any notice.

    """

    layout = Layout(self, request)

    if self.user_id != get_user_id(request):
        if not request.is_private(self):
            raise HTTPForbidden()

    if self.state == 'published':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Edit Official Notice"),
            'callout': _(
                'Published official notices may not be edited.'
            ),
            'show_form': False
        }

    if form.submitted(request):
        form.update_model(self)
        self.add_change(request, _("edited"))
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Official Notice"),
        'button_text': _("Save"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='delete',
    template='form.pt',
    permission=Personal,
    form=EmptyForm
)
def delete_notice(self, request, form):
    """ Delete a notice.

    Only drafted notices may be deleted (usually by editors). Editors may only
    delete their own notices, publishers may delete any notice.

    """
    layout = Layout(self, request)

    if self.user_id != get_user_id(request):
        if not request.is_private(self):
            raise HTTPForbidden()

    if self.state != 'drafted' and self.state != 'rejected':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Delete Official Notice"),
            'callout': _(
                "Only drafted or rejected official notices may be deleted."
            ),
            'show_form': False
        }

    if form.submitted(request):
        collection = GazetteNoticeCollection(request.app.session())
        collection.delete(self)
        request.message(_("Official notice deleted."), 'success')
        return redirect(layout.homepage_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Delete Official Notice"),
        'button_text': _("Delete Official Notice"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='submit',
    template='form.pt',
    permission=Personal,
    form=EmptyForm
)
def submit_notice(self, request, form):
    """ Submit a notice.

    This view is used by the editors to submit their drafts for the publishers
    to review.

    Only drafted notices may be submitted. Editors may only submit their own
    notices (publishers may publish any notice).

    """

    layout = Layout(self, request)

    if self.user_id != get_user_id(request):
        if not request.is_private(self):
            raise HTTPForbidden()

    if self.state != 'drafted' and self.state != 'rejected':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Submit Official Note"),
            'callout': _(
                "Only drafted or rejected official notices may be published."
            ),
            'show_form': False
        }

    if form.submitted(request):
        self.submit(request)
        request.message(_("Official notice submitted."), 'success')
        return redirect(layout.homepage_link)

    return {
        'message': _(
            'Do you really want to submit "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Submit Official Note"),
        'button_text': _("Submit Official Note"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='publish',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def publish_notice(self, request, form):
    """ Publish a notice.

    This view is used by the publishers to publish a submitted notice.

    Only submitted notices may be published.

    """

    layout = Layout(self, request)

    if self.state != 'submitted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Publish Official Note"),
            'callout': _("Only submitted official notices may be published."),
            'show_form': False
        }

    if form.submitted(request):
        self.publish(request)
        request.message(_("Official notice published."), 'success')
        request.app.send_email(
            subject=request.translate(_("Official Notice Published")),
            receivers=(self.user.username, ),
            reply_to=request.app.mail_sender,
            content=render_template(
                'mail_notice_published.pt',
                request,
                {
                    'title': request.translate(_("Official Notice Published")),
                    'model': self,
                    'layout': MailLayout(self, request)
                }
            )
        )
        if request.app.principal.publish_to:
            request.app.send_email(
                subject=request.translate(_("Publish Official Notice")),
                receivers=(request.app.principal.publish_to, ),
                reply_to=request.app.mail_sender,
                content=render_template(
                    'mail_publish.pt',
                    request,
                    {
                        'title': request.translate((
                            _("Publish Official Notice")
                        )),
                        'model': self,
                        'layout': MailLayout(self, request)
                    }
                )
            )
            self.add_change(request, _("mail sent"))
        return redirect(layout.homepage_link)

    return {
        'message': _(
            'Do you really want to publish "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Publish Official Note"),
        'button_text': _("Publish Official Note"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='reject',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def reject_notice(self, request, form):
    """ Reject a notice.

    This view is used by the publishers to reject a submitted notice.

    Only submitted notices may be rejected.

    """

    layout = Layout(self, request)

    if self.state != 'submitted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Reject Official Note"),
            'callout': _("Only submitted official notices may be rejected."),
            'show_form': False
        }

    if form.submitted(request):
        self.reject(request)
        request.message(_("Official notice rejected."), 'success')
        request.app.send_email(
            subject=request.translate(_("Official Notice Rejected")),
            receivers=(self.user.username, ),
            reply_to=request.app.mail_sender,
            content=render_template(
                'mail_notice_rejected.pt',
                request,
                {
                    'title': request.translate(_("Official Notice Rejected")),
                    'model': self,
                    'layout': MailLayout(self, request)
                }
            )
        )
        return redirect(layout.homepage_link)

    return {
        'message': _(
            'Do you really want to reject "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Reject Official Note"),
        'button_text': _("Reject Official Note"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }
