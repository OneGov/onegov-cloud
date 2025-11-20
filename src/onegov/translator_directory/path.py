from __future__ import annotations

from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import (
    TranslatorDocumentCollection)
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.time_report import (
    TimeReportCollection,
)
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.language import Language
from onegov.translator_directory.models.mutation import TranslatorMutation
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.translator_directory.models.translator import Translator
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.request import TranslatorAppRequest


@TranslatorDirectoryApp.path(
    model=Translator, path='/translator/{id}',
    converters={'id': UUID}
)
def get_translator(
    request: TranslatorAppRequest,
    id: UUID
) -> Translator | None:
    return request.session.query(Translator).filter_by(id=id).first()


@TranslatorDirectoryApp.path(
    model=TranslatorCollection, path='/translators',
    converters={
        'page': int,
        'written_langs': [str],
        'spoken_langs': [str],
        'monitor_langs': [str],
        'order_desc': bool,
        'guilds': [str],
        'interpret_types': [str],
        'admissions': [str],
        'genders': [str],
        'include_hidden': bool
    }
)
def get_translators(
    request: TranslatorAppRequest,
    page: int | None = None,
    written_langs: list[str] | None = None,
    spoken_langs: list[str] | None = None,
    monitor_langs: list[str] | None = None,
    order_by: str | None = None,
    order_desc: bool = False,
    search: str | None = None,
    guilds: list[str] | None = None,
    interpret_types: list[str] | None = None,
    admissions: list[str] | None = None,
    genders: list[str] | None = None,
    include_hidden: bool | None = None
) -> TranslatorCollection:

    user = request.current_user
    return TranslatorCollection(
        request.app,
        page or 0,
        written_langs=written_langs,
        spoken_langs=spoken_langs,
        monitor_langs=monitor_langs,
        order_by=order_by,
        order_desc=order_desc,
        user_role=user.role if user else None,
        search=search,
        guilds=guilds,
        interpret_types=interpret_types,
        admissions=admissions,
        genders=genders,
        include_hidden=include_hidden if include_hidden is not None else False
    )


@TranslatorDirectoryApp.path(
    model=Language, path='/language/{id}',
    converters={'id': UUID}
)
def get_language(app: TranslatorDirectoryApp, id: UUID) -> Language | None:
    return LanguageCollection(app.session()).by_id(id)


@TranslatorDirectoryApp.path(
    model=LanguageCollection, path='/languages', converters={'page': int}
)
def get_language_collection(
    app: TranslatorDirectoryApp,
    page: int = 0,
    letter: str | None = None
) -> LanguageCollection:
    return LanguageCollection(app.session(), page, letter)


@TranslatorDirectoryApp.path(
    model=TranslatorDocumentCollection, path='/documents/{translator_id}',
    converters={'translator_id': UUID}
)
def get_translator_documents(
    app: TranslatorDirectoryApp,
    translator_id: UUID,
    category: str | None = None
) -> TranslatorDocumentCollection | None:
    result = TranslatorDocumentCollection(
        app.session(), translator_id, category
    )
    if not result.translator:
        return None
    return result


@TranslatorDirectoryApp.path(
    model=TranslatorMutation,
    path='/mutation/{target_id}/{ticket_id}',
    converters={'target_id': UUID, 'ticket_id': UUID}
)
def get_translator_mutation(
    app: TranslatorDirectoryApp,
    target_id: UUID,
    ticket_id: UUID
) -> TranslatorMutation:
    return TranslatorMutation(app.session(), target_id, ticket_id)


@TranslatorDirectoryApp.path(
    model=Accreditation,
    path='/accreditation/{target_id}/{ticket_id}',
    converters={'target_id': UUID, 'ticket_id': UUID}
)
def get_accreditation(
    app: TranslatorDirectoryApp,
    target_id: UUID,
    ticket_id: UUID
) -> Accreditation:
    return Accreditation(app.session(), target_id, ticket_id)


@TranslatorDirectoryApp.path(
    model=TimeReportCollection,
    path='/time-reports',
    converters={'page': int, 'month': int, 'year': int},
)
def get_time_reports(
    app: TranslatorDirectoryApp,
    page: int = 0,
    month: int | None = None,
    year: int | None = None,
) -> TimeReportCollection:
    return TimeReportCollection(app, page, month, year)


@TranslatorDirectoryApp.path(
    model=TranslatorTimeReport,
    path='/time-report/{id}',
    converters={'id': UUID},
)
def get_time_report(
    request: TranslatorAppRequest, id: UUID
) -> TranslatorTimeReport | None:
    return request.session.query(TranslatorTimeReport).filter_by(id=id).first()
