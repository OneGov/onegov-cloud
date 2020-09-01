from onegov.translator_directory import _
from onegov.core.security import Secret, Personal
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.forms.translator import TranslatorForm
from onegov.translator_directory.layouts.translator import (
    AddTranslatorLayout, TranslatorLayout
)
from onegov.translator_directory.models.translator import Translator


@TranslatorDirectoryApp.form(
    model=TranslatorCollection,
    template='form.pt',
    name='new',
    form=TranslatorForm,
    permission=Secret
)
def add_new_translator(self, request, form):

    if form.submitted(request):
        translator = self.add(**form.get_useful_data())
        request.success(_('Added a new translator'))
        return request.redirect(request.link(translator))

    layout = AddTranslatorLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': layout.title
    }


@TranslatorDirectoryApp.html(
    model=Translator,
    template='translator.pt',
    permission=Personal
)
def view_translator(self, request):
    layout = TranslatorLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'title': self.full_name
    }


@TranslatorDirectoryApp.form(
    model=Translator,
    template='form.pt',
    name='edit',
    form=TranslatorForm,
    permission=Secret
)
def edit_translator(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))
    layout = AddTranslatorLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': layout.title
    }

