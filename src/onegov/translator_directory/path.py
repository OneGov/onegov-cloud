from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import Translator, Language


@TranslatorDirectoryApp.path(
    model=Translator, path='/translator/{id}'
)
def get_translator(request, id):
    return TranslatorCollection(request.session).by_id(id)


@TranslatorDirectoryApp.path(
    model=TranslatorCollection, path='/translators',
    converters=dict(page=int, wlang=[], slang=[])
)
def get_translators(request, page=None, written_langs=None, spoken_langs=None):
    return TranslatorCollection(
        request.session, page or 0,
        written_langs=written_langs,
        spoken_langs=spoken_langs
    )


@TranslatorDirectoryApp.path(
    model=Language, path='/language/{id}'
)
def get_language(request, id):
    return LanguageCollection(request.session).by_id(id)


@TranslatorDirectoryApp.path(
    model=LanguageCollection, path='/languages',
)
def get_language_collection(request):
    return LanguageCollection(request.session)
