""" The manage subscription views. """
from __future__ import annotations

import morepath

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.forms import EmptyForm
from onegov.election_day.layouts import ManageUploadTokensLayout
from onegov.election_day.models import UploadToken


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.manage_html(
    model=UploadTokenCollection,
    template='manage/upload_tokens.pt'
)
def view_upload_tokens(
    self: UploadTokenCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ View all upload tokens as a list. """

    return {
        'layout': ManageUploadTokensLayout(self, request),
        'title': _('Upload tokens'),
        'upload_tokens': self.query().all(),
        'new_token': request.link(self, 'create-token'),
    }


@ElectionDayApp.manage_form(
    model=UploadTokenCollection,
    name='create-token',
    form=EmptyForm
)
def create_upload_token(
    self: UploadTokenCollection,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:
    """ Create a new upload token. """

    layout = ManageUploadTokensLayout(self, request)

    if form.submitted(request):
        self.create()
        request.message(_('Upload token created.'), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'message': _('Create a new upload token?'),
        'button_text': _('Create'),
        'title': _('Create token'),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=UploadToken,
    name='delete'
)
def delete_upload_token(
    self: UploadToken,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:
    """ Delete the upload token item. """

    layout = ManageUploadTokensLayout(self, request)

    if form.submitted(request):
        upload_tokens = UploadTokenCollection(request.session)
        upload_tokens.delete(self)
        request.message(_('Upload token deleted.'), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.token}
        ),
        'layout': layout,
        'form': form,
        'title': self.token,
        'subtitle': _('Delete upload token'),
        'button_text': _('Delete upload token'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
