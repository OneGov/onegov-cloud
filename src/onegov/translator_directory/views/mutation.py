from morepath import redirect
from onegov.core.security import Secret
from onegov.org.elements import Link
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.mutation import ApplyMutationForm
from onegov.translator_directory.layout import ApplyTranslatorChangesLayout
from onegov.translator_directory.models.message import \
    TranslatorMutationMessage
from onegov.translator_directory.models.mutation import TranslatorMutation


@TranslatorDirectoryApp.form(
    model=TranslatorMutation,
    name='apply',
    template='form.pt',
    permission=Secret,
    form=ApplyMutationForm
)
def apply_translator_mutation(self, request, form):
    if form.submitted(request):
        form.update_model()
        request.success(_("Proposed changes applied."))
        TranslatorMutationMessage.create(self.ticket, request, 'applied')
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    else:
        form.apply_model()

    layout = ApplyTranslatorChangesLayout(self.target, request)
    layout.breadcrumbs.append(Link(_("Apply proposed changes"), '#'))

    return {
        'layout': layout,
        'title': _("Apply proposed changes"),
        'form': form
    }
