from __future__ import annotations

from onegov.core.converters import extended_date_converter
from onegov.core.i18n import SiteLocale
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import BallotCollection
from onegov.election_day.collections import CandidateCollection
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import ElectionCollection
from onegov.election_day.collections import ElectionCompoundCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import ListCollection
from onegov.election_day.collections import ScreenCollection
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.collections import VoteCollection
from onegov.election_day.models import Ballot
from onegov.election_day.models import Candidate
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import List
from onegov.election_day.models import Principal
from onegov.election_day.models import Screen
from onegov.election_day.models import Subscriber
from onegov.election_day.models import UploadToken
from onegov.election_day.models import Vote
from onegov.user import Auth
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.path(
    model=Auth,
    path='/auth'
)
def get_auth(request: ElectionDayRequest, to: str = '/') -> Auth:
    return Auth.from_request(request, to)


@ElectionDayApp.path(
    model=Principal,
    path='/'
)
def get_principal(app: ElectionDayApp) -> Principal:
    return app.principal


@ElectionDayApp.path(
    model=ElectionCollection,
    path='/manage/elections',
    converters={
        'page': int,
        'year': int
    }
)
def get_manage_elections(
    app: ElectionDayApp,
    page: int = 0,
    year: int | None = None
) -> ElectionCollection:
    return ElectionCollection(app.session(), page=page, year=year)


@ElectionDayApp.path(
    model=ElectionCompoundCollection,
    path='/manage/election-compounds',
    converters={
        'page': int,
        'year': int
    }
)
def get_manage_election_compsites(
    app: ElectionDayApp,
    page: int = 0,
    year: int | None = None
) -> ElectionCompoundCollection:
    return ElectionCompoundCollection(app.session(), page=page, year=year)


@ElectionDayApp.path(
    model=VoteCollection,
    path='/manage/votes',
    converters={
        'page': int,
        'year': int
    }
)
def get_manage_votes(
    app: ElectionDayApp,
    page: int = 0,
    year: int | None = None
) -> VoteCollection:
    return VoteCollection(app.session(), page=page, year=year)


@ElectionDayApp.path(
    model=SmsSubscriberCollection,
    path='/manage/subscribers/sms',
    converters={
        'page': int,
        'active_only': bool
    }
)
def get_manage_sms_subscribers(
    app: ElectionDayApp,
    page: int = 0,
    term: str | None = None,
    active_only: bool | None = None
) -> SmsSubscriberCollection:
    return SmsSubscriberCollection(
        app.session(), page=page, term=term, active_only=active_only
    )


@ElectionDayApp.path(
    model=EmailSubscriberCollection,
    path='/manage/subscribers/email',
    converters={
        'page': int,
        'active_only': bool
    }
)
def get_manage_email_subscribers(
    app: ElectionDayApp,
    page: int = 0,
    term: str | None = None,
    active_only: bool | None = None
) -> EmailSubscriberCollection:
    return EmailSubscriberCollection(
        app.session(), page=page, term=term, active_only=active_only
    )


@ElectionDayApp.path(
    model=UploadTokenCollection,
    path='/manage/upload-tokens'
)
def get_manage_upload_tokens(app: ElectionDayApp) -> UploadTokenCollection:
    return UploadTokenCollection(app.session())


@ElectionDayApp.path(
    model=DataSourceCollection,
    path='/manage/sources',
    converters={
        'page': int
    }
)
def get_manage_data_sources(
    app: ElectionDayApp,
    page: int = 0
) -> DataSourceCollection:
    return DataSourceCollection(app.session(), page=page)


@ElectionDayApp.path(
    model=DataSourceItemCollection,
    path='/manage/source/{id}/items',
    converters={
        'id': UUID,
        'page': int
    }
)
def get_manage_data_source_items(
    app: ElectionDayApp,
    id: UUID,
    page: int = 0
) -> DataSourceItemCollection:
    return DataSourceItemCollection(app.session(), id, page=page)


@ElectionDayApp.path(
    model=Election,
    path='/election/{id}',
)
def get_election(app: ElectionDayApp, id: str) -> Election | None:
    return ElectionCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=Candidate,
    path='/candidate/{id}',
    converters={
        'id': UUID
    }
)
def get_candidate(app: ElectionDayApp, id: UUID) -> Candidate | None:
    return CandidateCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=List,
    path='/list/{id}',
    converters={
        'id': UUID
    }
)
def get_list(app: ElectionDayApp, id: UUID) -> List | None:
    return ListCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=ElectionCompound,
    path='/elections/{id}'
)
def get_election_compound(
    app: ElectionDayApp,
    id: str
) -> ElectionCompound | None:
    return ElectionCompoundCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=ElectionCompoundPart,
    path='/elections-part/{election_compound_id}/{domain}/{id}'
)
def get_superregion(
    app: ElectionDayApp,
    election_compound_id: str,
    domain: str,
    id: str
) -> ElectionCompoundPart | None:

    compound = ElectionCompoundCollection(app.session()).by_id(
        election_compound_id
    )
    if compound is None:
        return None

    if domain == 'district':
        segments = app.principal.get_districts(compound.date.year)
    elif domain == 'region':
        segments = app.principal.get_regions(compound.date.year)
    elif domain == 'superregion':
        segments = app.principal.get_superregions(compound.date.year)
    else:
        return None

    segment = id.title().replace('-', ' ')
    if segment in segments:
        return ElectionCompoundPart(compound, domain, segment)
    return None


@ElectionDayApp.path(
    model=Vote,
    path='/vote/{id}'
)
def get_vote(app: ElectionDayApp, id: str) -> Vote | None:
    return VoteCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=Ballot,
    path='/ballot/{id}',
    converters={
        'id': UUID
    }
)
def get_ballot(app: ElectionDayApp, id: UUID) -> Ballot | None:
    return BallotCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=Subscriber,
    path='/subscriber/{id}',
    converters={
        'id': UUID
    }
)
def get_subscriber(app: ElectionDayApp, id: UUID) -> Subscriber | None:
    return SubscriberCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=UploadToken,
    path='/upload-token/{id}',
    converters={
        'id': UUID
    }
)
def get_upload_token(app: ElectionDayApp, id: UUID) -> UploadToken | None:
    return UploadTokenCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=DataSource,
    path='/data-source/{id}',
    converters={
        'id': UUID
    }
)
def get_data_source(app: ElectionDayApp, id: UUID) -> DataSource | None:
    return DataSourceCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=DataSourceItem,
    path='/data-source-item/{id}',
    converters={
        'id': UUID
    }
)
def get_data_source_item(
    app: ElectionDayApp,
    id: UUID
) -> DataSourceItem | None:
    return DataSourceItemCollection(app.session()).by_id(id)


@ElectionDayApp.path(
    model=ArchivedResultCollection,
    path='/archive/{date}'
)
def get_archive_by_year(
    app: ElectionDayApp,
    date: str
) -> ArchivedResultCollection:
    return ArchivedResultCollection(app.session(), date)


@ElectionDayApp.path(
    model=SearchableArchivedResultCollection,
    path='archive-search/{item_type}',
    converters={
        'from_date': extended_date_converter,
        'to_date': extended_date_converter,
        'domains': [str],
        'answers': [str],
        'page': int
    }
)
def get_archive_search(
    app: ElectionDayApp,
    from_date: date | None = None,
    to_date: date | None = None,
    answers: list[str] | None = None,
    item_type: str | None = None,
    domains: list[str] | None = None,
    term: str | None = None,
    page: int = 0
) -> SearchableArchivedResultCollection | None:

    return SearchableArchivedResultCollection.for_item_type(
        app,
        item_type,
        to_date=to_date,
        from_date=from_date,
        answers=answers,
        domains=domains,
        term=term,
        page=page
    )


@ElectionDayApp.path(
    model=SiteLocale,
    path='/locale/{locale}'
)
def get_locale(
    request: ElectionDayRequest,
    app: ElectionDayApp,
    locale: str
) -> SiteLocale | None:
    return SiteLocale.for_path(app, locale)


@ElectionDayApp.path(
    model=ScreenCollection,
    path='/manage/screens',
    converters={
        'page': int
    }
)
def get_manage_screens(app: ElectionDayApp, page: int = 0) -> ScreenCollection:
    return ScreenCollection(app.session(), page)


@ElectionDayApp.path(
    model=Screen,
    path='/screen/{number}',
    converters={
        'number': int
    }
)
def get_screen(app: ElectionDayApp, number: int) -> Screen | None:
    return ScreenCollection(app.session()).by_number(number)
