from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import Translator, Language


@TranslatorDirectoryApp.path(
    model=Translator, path='/translator/{id}',
    converters=dict(id=int)
)
def get_translator(request, id):
    return TranslatorCollection(request.session).by_id(id)


@TranslatorDirectoryApp.path(
    model=TranslatorCollection, path='/translators',
    converters=dict(page=int, wlang=[int], slang=[int])
)
def get_translators(request, page=None, wlang=None, slang=None):
    return TranslatorCollection(
        request.session, page, written_langs=wlang, spoken_langs=slang)


@TranslatorDirectoryApp.path(
    model=Language, path='/language/{id}',
    converters=dict(id=int)
)
def get_language(request, id):
    return LanguageCollection(request.session).by_id(id)


@TranslatorDirectoryApp.path(
    model=LanguageCollection, path='/languages',
)
def get_language_collection(request):
    return LanguageCollection(request.session)
