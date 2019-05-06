from onegov.core.converters import extended_date_converter
from onegov.core.i18n import SiteLocale
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


@SwissvotesApp.path(
    model=Principal,
    path='/'
)
def get_principal(app):
    return app.principal


@SwissvotesApp.path(
    model=Auth,
    path='/auth'
)
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@SwissvotesApp.path(
    model=SiteLocale,
    path='/locale/{locale}'
)
def get_locale(request, app, locale, to=None):
    to = to or request.link(app.principal)
    return SiteLocale.for_path(app, locale, to)


@SwissvotesApp.path(
    model=SwissVoteCollection,
    path='/votes',
    converters=dict(
        page=int,
        from_date=extended_date_converter,
        to_date=extended_date_converter,
        legal_form=[int],
        result=[int],
        policy_area=[str],
        term=str,
        full_text=bool,
        position_federal_council=[int],
        position_national_council=[int],
        position_council_of_states=[int],
        sort_by=str,
        sort_order=str
    )
)
def get_votes(
    app,
    page=None,
    from_date=None,
    to_date=None,
    legal_form=None,
    result=None,
    policy_area=None,
    term=None,
    full_text=None,
    position_federal_council=None,
    position_national_council=None,
    position_council_of_states=None,
    sort_by=None,
    sort_order=None
):
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
    path='/vote/{bfs_number}'
)
def get_vote(app, bfs_number):
    return SwissVoteCollection(app).by_bfs_number(bfs_number)


@SwissvotesApp.path(
    model=SwissVoteFile,
    path='/attachments/{id}'
)
def get_attachment(app, id):
    return FileCollection(app.session()).by_id(id)


@SwissvotesApp.path(
    model=TranslatablePageCollection,
    path='/pages'
)
def get_pages(app):
    return TranslatablePageCollection(app.session())


@SwissvotesApp.path(
    model=TranslatablePage,
    path='/page/{id}'
)
def get_page(app, id):
    return TranslatablePageCollection(app.session()).by_id(id)


@SwissvotesApp.path(
    model=TranslatablePageMove,
    path='/move/page/{subject_id}/{direction}/{target_id}',
)
def get_page_move(app, subject_id, direction, target_id):
    return TranslatablePageMove(
        app.session(), subject_id, target_id, direction
    )
