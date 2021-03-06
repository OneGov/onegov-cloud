from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.language import Language
from onegov.translator_directory.models.translator import Translator


@TranslatorDirectoryApp.path(
    model=Translator, path='/translator/{id}'
)
def get_translator(request, id):
    return request.session.query(Translator).filter_by(id=id).first()


@TranslatorDirectoryApp.path(
    model=TranslatorCollection, path='/translators',
    converters=dict(page=int, written_langs=[str], spoken_langs=[str],
                    order_desc=bool, guilds=[str], interpret_types=[str])
)
def get_translators(request, page=None, written_langs=None, spoken_langs=None,
                    order_by=None, order_desc=None, search=None, guilds=None,
                    interpret_types=None):
    user = request.current_user
    return TranslatorCollection(
        request.session, page or 0,
        written_langs=written_langs,
        spoken_langs=spoken_langs,
        order_by=order_by,
        order_desc=order_desc,
        user_role=user and user.role or None,
        search=search,
        guilds=guilds,
        interpret_types=interpret_types
    )


@TranslatorDirectoryApp.path(
    model=Language, path='/language/{id}'
)
def get_language(app, id):
    return LanguageCollection(app.session()).by_id(id)


@TranslatorDirectoryApp.path(
    model=LanguageCollection, path='/languages',
)
def get_language_collection(app, page=0, letter=None):
    return LanguageCollection(app.session(), page, letter)


@TranslatorDirectoryApp.path(
    model=TranslatorDocumentCollection, path='/documents/{translator_id}'
)
def get_translator_documents(app, translator_id, category=None):
    return TranslatorDocumentCollection(app.session(), translator_id, category)
