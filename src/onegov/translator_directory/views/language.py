from onegov.core.security import Secret, Personal
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.forms.language import LanguageForm
from onegov.translator_directory import _
from onegov.translator_directory.layout import DefaultLayout
from onegov.translator_directory.models.translator import Language


@TranslatorDirectoryApp.form(
    model=LanguageCollection,
    template='form.pt',
    name='new',
    form=LanguageForm,
    permission=Secret
)
def add_new_language(self, request, form):

    if form.submitted(request):
        lang = self.add(**form.get_useful_data())
        request.success(
            _('Added language ${name}', mapping={'name': lang.name})
        )
        return request.redirect(request.class_link(LanguageCollection))

    return {
        'layout': DefaultLayout(self, request),
        'model': self,
        'form': form,
        'title': _('Add new language')
    }


@TranslatorDirectoryApp.html(
    model=LanguageCollection,
    template='languages.pt',
    permission=Personal,
)
def view_translators(self, request):

    return {
        'layout': DefaultLayout(self, request),
        'model': self,
        'title': _('Languages'),
        'languages': self.batch
    }


@TranslatorDirectoryApp.view(
    model=Language,
    request_method='DELETE',
    permission=Secret
)
def delete_language(self, request):
    request.assert_valid_csrf_token()
    if self.speaker.first() or self.writers.first():
        request.warning(_(
            "This language is used and can't be deleted"))
    else:
        LanguageCollection(request.session).delete(self)
        request.success(_('Language successfully deleted'))
