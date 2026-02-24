from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Secret, Private
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.forms.language import LanguageForm
from onegov.translator_directory import _
from onegov.translator_directory.layout import (
    LanguageCollectionLayout, AddLanguageLayout, EditLanguageLayout)
from onegov.translator_directory.models.language import Language


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.form(
    model=LanguageCollection,
    template='form.pt',
    name='new',
    form=LanguageForm,
    permission=Secret
)
def add_new_language(
    self: LanguageCollection,
    request: TranslatorAppRequest,
    form: LanguageForm
) -> RenderData | Response:

    if form.submitted(request):
        lang = self.add(**form.get_useful_data())
        request.success(
            _('Added language ${name}', mapping={'name': lang.name})
        )
        return request.redirect(request.class_link(LanguageCollection))

    layout = AddLanguageLayout(self, request)
    layout.edit_mode = True

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': _('Add new language')
    }


@TranslatorDirectoryApp.html(
    model=LanguageCollection,
    template='languages.pt',
    permission=Private,
)
def view_languages(
    self: LanguageCollection,
    request: TranslatorAppRequest
) -> RenderData:

    letters = tuple(
        Link(
            text=letter,
            url=request.link(
                self.by_letter(
                    letter=letter if (letter != self.letter) else None
                )
            ),
            active=(letter == self.letter),
        ) for letter in self.used_letters
    )

    return {
        'layout': LanguageCollectionLayout(self, request),
        'model': self,
        'title': _('Languages'),
        'languages': self.batch,
        'letters': letters
    }


@TranslatorDirectoryApp.form(
    model=Language,
    permission=Secret,
    name='edit',
    form=LanguageForm,
    template='form.pt'
)
def edit_language(
    self: Language,
    request: TranslatorAppRequest,
    form: LanguageForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(
            _('Updated language ${name}', mapping={'name': self.name})
        )
        return request.redirect(request.link(LanguageCollection(
            request.session, letter=self.name[0].upper()
        )))

    if not form.errors:
        form.process(obj=self)

    layout = EditLanguageLayout(self, request)
    layout.edit_mode = True
    layout.editmode_links.extend(layout.editbar_links)

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': _('Edit language')
    }


@TranslatorDirectoryApp.view(
    model=Language,
    request_method='DELETE',
    permission=Secret
)
def delete_language(self: Language, request: TranslatorAppRequest) -> None:
    request.assert_valid_csrf_token()
    if not self.deletable:
        request.warning(_("This language is used and can't be deleted."))
    else:
        LanguageCollection(request.session).delete(self)
        request.success(_('Language successfully deleted'))
