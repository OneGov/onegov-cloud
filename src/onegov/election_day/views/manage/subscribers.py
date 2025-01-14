from __future__ import annotations

from morepath import redirect
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.forms import SubscribersCleanupForm
from onegov.election_day.layouts import ManageSubscribersLayout
from onegov.election_day.models import Subscriber


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.forms import EmptyForm
    from onegov.election_day.request import ElectionDayRequest
    from onegov.election_day.formats.imports.common import FileImportError
    from webob.response import Response


@ElectionDayApp.manage_html(
    model=SmsSubscriberCollection,
    template='manage/subscribers.pt'
)
def view_sms_subscribers(
    self: SmsSubscriberCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ View a list with all SMS subscribers. """

    return {
        'layout': ManageSubscribersLayout(self, request),
        'title': _('SMS subscribers'),
        'address_title': _('Phone number'),
        'count': self.query().count(),
        'subscribers': self.batch,
        'term': self.term,
    }


@ElectionDayApp.manage_html(
    model=EmailSubscriberCollection,
    template='manage/subscribers.pt'
)
def view_email_subscribers(
    self: EmailSubscriberCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ View a list with all email subscribers. """

    return {
        'layout': ManageSubscribersLayout(self, request),
        'title': _('Email subscribers'),
        'address_title': _('Email'),
        'count': self.query().count(),
        'subscribers': self.batch,
        'term': self.term
    }


@ElectionDayApp.csv_file(
    model=SmsSubscriberCollection,
    name='export',
    permission=Private
)
def export_sms_subscribers(
    self: SmsSubscriberCollection,
    request: ElectionDayRequest
) -> RenderData:

    """ Export all SMS subscribers as a CSV. """

    return {
        'data': self.export(),
        'name': 'sms-subscribers'
    }


@ElectionDayApp.csv_file(
    model=EmailSubscriberCollection,
    name='export',
    permission=Private
)
def export_email_subscribers(
    self: EmailSubscriberCollection,
    request: ElectionDayRequest
) -> RenderData:

    """ Export all email subscribers as a CSV. """

    return {
        'data': self.export(),
        'name': 'email-subscribers'
    }


def handle_cleanup_subscribers(
    collection: EmailSubscriberCollection | SmsSubscriberCollection,
    request: ElectionDayRequest,
    form: SubscribersCleanupForm
) -> RenderData | Response:

    layout = ManageSubscribersLayout(collection, request)

    errors: list[FileImportError] = []
    if form.submitted(request):
        assert form.file.data is not None
        assert form.file.file is not None
        errors, count = collection.cleanup(
            form.file.file,
            form.file.data['mimetype'],
            form.type.data == 'delete'
        )
        if not errors:
            request.message(
                _(
                    '${count} subscribers cleaned up.',
                    mapping={'count': count}
                ),
                'success'
            )
            return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _('Clean up subscribers'),
        'cancel': layout.manage_model_link,
        'file_import_errors': errors
    }


@ElectionDayApp.manage_form(
    model=SmsSubscriberCollection,
    name='cleanup',
    form=SubscribersCleanupForm
)
def cleanup_sms_subscribers(
    self: SmsSubscriberCollection,
    request: ElectionDayRequest,
    form: SubscribersCleanupForm
) -> RenderData | Response:

    """ Deletes a list of SMS subscribers. """

    return handle_cleanup_subscribers(self, request, form)


@ElectionDayApp.manage_form(
    model=EmailSubscriberCollection,
    name='cleanup',
    form=SubscribersCleanupForm
)
def cleanup_email_subscribers(
    self: EmailSubscriberCollection,
    request: ElectionDayRequest,
    form: SubscribersCleanupForm
) -> RenderData | Response:

    """ Deletes a list of email subscribers. """

    return handle_cleanup_subscribers(self, request, form)


@ElectionDayApp.manage_form(
    model=Subscriber,
    name='delete'
)
def delete_subscriber(
    self: Subscriber,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:

    """ Delete a single subscriber. """

    layout = ManageSubscribersLayout(self, request)

    if form.submitted(request):
        request.session.delete(self)
        request.message(_('Subscriber deleted.'), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.address
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.address,
        'subtitle': _('Delete subscriber'),
        'button_text': _('Delete subscriber'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Subscriber,
    name='activate'
)
def activate_subscriber(
    self: Subscriber,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:

    """ Activate a single subscriber. """

    layout = ManageSubscribersLayout(self, request)

    if form.submitted(request):
        self.active = True
        request.message(_('Subscriber activated.'), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to activate "${item}"?',
            mapping={
                'item': self.address
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.address,
        'subtitle': _('Activate subscriber'),
        'button_text': _('Activate subscriber'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Subscriber,
    name='deactivate'
)
def deactivate_subscriber(
    self: Subscriber,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:

    """ Deactivate a single subscriber. """

    layout = ManageSubscribersLayout(self, request)

    if form.submitted(request):
        self.active = False
        request.message(_('Subscriber deactivated.'), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to deactivate "${item}"?',
            mapping={
                'item': self.address
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.address,
        'subtitle': _('Deactivate subscriber'),
        'button_text': _('Deactivate subscriber'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
