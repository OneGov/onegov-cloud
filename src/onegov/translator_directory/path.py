from onegov.translator_directory import TranslatorDirectoryApp





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
