from __future__ import annotations

from morepath import redirect
from onegov.core.security import Secret
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.mutation import ApplyMutationForm
from onegov.translator_directory.layout import ApplyTranslatorChangesLayout
from onegov.translator_directory.models.message import (
    TranslatorMutationMessage)
from onegov.translator_directory.models.mutation import TranslatorMutation
from webob import exc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.form(
    model=TranslatorMutation,
    name='apply',
    template='form.pt',
    permission=Secret,
    form=ApplyMutationForm
)
def apply_translator_mutation(
    self: TranslatorMutation,
    request: TranslatorAppRequest,
    form: ApplyMutationForm
) -> RenderData | Response:

    if self.target is None or self.ticket is None:
        raise exc.HTTPNotFound()

    if form.submitted(request):
        form.update_model()
        request.success(_('Proposed changes applied'))
        TranslatorMutationMessage.create(
            self.ticket,
            request,
            'applied',
            form.changes.data or []
        )
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    else:
        form.apply_model()

    layout = ApplyTranslatorChangesLayout(self.target, request)

    return {
        'layout': layout,
        'title': _('Apply proposed changes'),
        'form': form
    }
