""" The manage subscription views. """

import morepath

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.forms import EmptyForm
# from onegov.election_day.layouts import ManageUploadTokenItemsLayout
from onegov.election_day.layouts import ManageUploadTokensLayout
from onegov.election_day.models import UploadToken
# from uuid import uuid4


@ElectionDayApp.manage_html(
    model=UploadTokenCollection,
    template='manage/upload_tokens.pt'
)
def view_upload_tokens(self, request):

    """ View all upload tokens as a list. """

    return {
        'layout': ManageUploadTokensLayout(self, request),
        'title': _("Upload tokens"),
        'upload_tokens': self.query().all(),
        'new_token': request.link(self, 'create-token'),
    }


@ElectionDayApp.manage_form(
    model=UploadTokenCollection,
    name='create-token',
    form=EmptyForm
)
def create_upload_token(self, request, form):

    """ Create a new upload token. """

    layout = ManageUploadTokensLayout(self, request)

    if form.submitted(request):
        self.create()
        request.message(_("Upload token created."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'message': _("Create a new upload token?"),
        'button_text': _("Create"),
        'title': _("Create token"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=UploadToken,
    name='delete'
)
def delete_upload_token(self, request, form):

    """ Delete the upload token item. """

    layout = ManageUploadTokensLayout(self, request)

    if form.submitted(request):
        upload_tokens = UploadTokenCollection(request.session)
        upload_tokens.delete(self)
        request.message(_("Upload token deleted."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.token}
        ),
        'layout': layout,
        'form': form,
        'title': self.token,
        'subtitle': _("Delete upload token"),
        'button_text': _("Delete upload token"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
