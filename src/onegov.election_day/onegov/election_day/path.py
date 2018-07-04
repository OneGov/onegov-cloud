from onegov.ballot import Ballot
from onegov.ballot import BallotCollection
from onegov.ballot import Candidate
from onegov.ballot import CandidateCollection
from onegov.ballot import Election
from onegov.ballot import ElectionCollection
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundCollection
from onegov.ballot import List
from onegov.ballot import ListCollection
from onegov.ballot import Vote
from onegov.ballot import VoteCollection
from onegov.core.i18n import SiteLocale
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models import Principal
from onegov.election_day.models import Subscriber
from onegov.user import Auth


@ElectionDayApp.path(model=Auth, path='/auth')
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@ElectionDayApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal


@ElectionDayApp.path(model=ElectionCollection, path='/manage/elections')
def get_manage_elections(app, page=0):
    return ElectionCollection(app.session(), page=page)


@ElectionDayApp.path(
    model=ElectionCompoundCollection, path='/manage/election-compounds'
)
def get_manage_election_compsites(app, page=0):
    return ElectionCompoundCollection(app.session(), page=page)


@ElectionDayApp.path(model=VoteCollection, path='/manage/votes')
def get_manage_votes(app, page=0):
    return VoteCollection(app.session(), page=page)


@ElectionDayApp.path(
    model=SmsSubscriberCollection, path='/manage/subscribers/sms'
)
def get_manage_sms_subscribers(app, page=0, term=None):
    return SmsSubscriberCollection(app.session(), page=page, term=term)


@ElectionDayApp.path(
    model=EmailSubscriberCollection, path='/manage/subscribers/email'
)
def get_manage_email_subscribers(app, page=0, term=None):
    return EmailSubscriberCollection(app.session(), page=page, term=term)


@ElectionDayApp.path(model=DataSourceCollection,
                     path='/manage/sources')
def get_manage_data_sources(app, page=0):
    return DataSourceCollection(app.session(), page=page)


@ElectionDayApp.path(model=DataSourceItemCollection,
                     path='/manage/source/{id}/items')
def get_manage_data_source_items(app, id, page=0):
    return DataSourceItemCollection(app.session(), id, page=page)


@ElectionDayApp.path(model=Election, path='/election/{id}')
def get_election(app, id):
    return ElectionCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=Candidate, path='/candidate/{id}')
def get_candidate(app, id):
    return CandidateCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=List, path='/list/{id}')
def get_list(app, id):
    return ListCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=ElectionCompound, path='/elections/{id}')
def get_election_compound(app, id):
    return ElectionCompoundCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=Vote, path='/vote/{id}')
def get_vote(app, id):
    return VoteCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=Ballot, path='/ballot/{id}')
def get_ballot(app, id):
    return BallotCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=Subscriber, path='/subscriber/{id}')
def get_subscriber(app, id):
    return SubscriberCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=DataSource, path='/data-source/{id}')
def get_data_source(app, id):
    return DataSourceCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=DataSourceItem, path='/data-source-item/{id}')
def get_data_source_item(app, id):
    return DataSourceItemCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=ArchivedResultCollection, path='/archive/{date}')
def get_archive_by_year(app, date):
    return ArchivedResultCollection(app.session(), date)


@ElectionDayApp.path(model=SiteLocale, path='/locale/{locale}')
def get_locale(request, app, locale, to=None):
    to = to or request.link(app.principal)
    return SiteLocale.for_path(app, locale, to)
