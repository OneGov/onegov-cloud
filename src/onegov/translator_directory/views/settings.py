from __future__ import annotations

from onegov.core.security import Secret
from onegov.org.models import Organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.settings import (
    TranslatorDirectorySettingsForm)
from onegov.translator_directory.layout import DefaultLayout
from onegov.translator_directory import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.form(
    model=Organisation,
    name='directory-settings',
    template='form.pt',
    permission=Secret,
    form=TranslatorDirectorySettingsForm
)
def view_locations_settings(
    self: Organisation,
    request: TranslatorAppRequest,
    form: TranslatorDirectorySettingsForm
) -> RenderData | Response:

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        form.update_model(request.app)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self, 'directory-settings'))

    form.apply_model(request.app)

    return {
        'layout': layout,
        'model': self,
        'title': _('Settings translator directory'),
        'form': form,
    }
