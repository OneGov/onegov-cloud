from __future__ import annotations

from onegov.core.converters import extended_date_converter
from onegov.core.i18n import SiteLocale
from onegov.core.orm.abstract import MoveDirection
from onegov.file import FileCollection
from onegov.swissvotes.app import SwissvotesApp
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import Principal
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from onegov.swissvotes.models import TranslatablePage
from onegov.swissvotes.models import TranslatablePageMove
from onegov.user import Auth


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.swissvotes.request import SwissvotesRequest


@SwissvotesApp.path(
    model=Principal,
    path='/'
)
def get_principal(app: SwissvotesApp) -> Principal:
    return app.principal


@SwissvotesApp.path(
    model=Auth,
    path='/auth'
)
def get_auth(request: SwissvotesRequest, to: str = '/') -> Auth:
    return Auth.from_request(request, to)


@SwissvotesApp.path(
    model=SiteLocale,
    path='/locale/{locale}'
)
def get_locale(app: SwissvotesApp, locale: str) -> SiteLocale | None:
    return SiteLocale.for_path(app, locale)


@SwissvotesApp.path(
    model=SwissVoteCollection,
    path='/votes',
    converters={
        'page': int,
        'from_date': extended_date_converter,
        'to_date': extended_date_converter,
        'legal_form': [int],
        'result': [int],
        'policy_area': [str],
        'term': str,
        'full_text': bool,
        'position_federal_council': [int],
        'position_national_council': [int],
        'position_council_of_states': [int],
        'sort_by': str,
        'sort_order': str
    }
)
def get_votes(
    app: SwissvotesApp,
    page: int = 0,
    from_date: date | None = None,
    to_date: date | None = None,
    legal_form: list[int] | None = None,
    result: list[int] | None = None,
    policy_area: list[str] | None = None,
    term: str | None = None,
    full_text: bool | None = None,
    position_federal_council: list[int] | None = None,
    position_national_council: list[int] | None = None,
    position_council_of_states: list[int] | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None
) -> SwissVoteCollection:
    return SwissVoteCollection(
        app,
        page=page,
        from_date=from_date,
        to_date=to_date,
        legal_form=legal_form,
        result=result,
        policy_area=policy_area,
        term=term,
        full_text=full_text,
        position_federal_council=position_federal_council,
        position_national_council=position_national_council,
        position_council_of_states=position_council_of_states,
        sort_by=sort_by,
        sort_order=sort_order
    )


@SwissvotesApp.path(
    model=SwissVote,
    path='/vote/{bfs_number}',
    converters={'term': str}
)
def get_vote(
    app: SwissvotesApp,
    bfs_number: str,
    term: str | None = None
) -> SwissVote | None:

    vote = SwissVoteCollection(app).by_bfs_number(bfs_number)
    if vote:
        vote.term = term
    return vote


@SwissvotesApp.path(
    model=SwissVoteFile,
    path='/attachments/{id}'
)
def get_attachment(app: SwissvotesApp, id: str) -> SwissVoteFile | None:
    return FileCollection(app.session(), type='swissvote').by_id(id)


@SwissvotesApp.path(
    model=TranslatablePageCollection,
    path='/pages'
)
def get_pages(app: SwissvotesApp) -> TranslatablePageCollection:
    return TranslatablePageCollection(app.session())


@SwissvotesApp.path(
    model=TranslatablePage,
    path='/page/{id}'
)
def get_page(app: SwissvotesApp, id: str) -> TranslatablePage | None:
    return TranslatablePageCollection(app.session()).by_id(id)


@SwissvotesApp.path(
    model=TranslatablePageMove,
    path='/move/page/{subject_id}/{direction}/{target_id}',
    converters={'direction': MoveDirection}
)
def get_page_move(
    app: SwissvotesApp,
    subject_id: str,
    direction: MoveDirection,
    target_id: str
) -> TranslatablePageMove:
    return TranslatablePageMove(
        app.session(), subject_id, target_id, direction
    )
