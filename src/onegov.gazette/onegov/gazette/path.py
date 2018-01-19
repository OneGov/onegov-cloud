from onegov.core.converters import extended_date_converter
from onegov.core.converters import uuid_converter
from onegov.file.integration import get_file
from onegov.gazette import GazetteApp
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import Organization
from onegov.gazette.models import OrganizationMove
from onegov.gazette.models import Principal
from onegov.gazette.models.issue import IssuePdfFile
from onegov.user import Auth
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection


@GazetteApp.path(model=Auth, path='/auth')
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@GazetteApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal


@GazetteApp.path(model=UserCollection, path='/users')
def get_users(app):
    return UserCollection(app.session())


@GazetteApp.path(model=User, path='/user/{username}')
def get_user(app, username):
    return UserCollection(app.session()).by_username(username)


@GazetteApp.path(model=UserGroupCollection, path='/groups')
def get_groups(app):
    return UserGroupCollection(app.session())


@GazetteApp.path(model=UserGroup, path='/group/{id}')
def get_group(app, id):
    return UserGroupCollection(app.session()).by_id(id)


@GazetteApp.path(model=CategoryCollection, path='/categories')
def get_categories(app):
    return CategoryCollection(app.session())


@GazetteApp.path(model=Category, path='/category/{id}')
def get_category(app, id):
    return CategoryCollection(app.session()).by_id(id)


@GazetteApp.path(model=OrganizationCollection, path='/organizations')
def get_organizations(app):
    return OrganizationCollection(app.session())


@GazetteApp.path(model=Organization, path='/organization/{id}')
def get_organization(app, id):
    return OrganizationCollection(app.session()).by_id(id)


@GazetteApp.path(
    model=OrganizationMove,
    path='/move/organization/{subject_id}/{direction}/{target_id}',
    converters=dict(subject_id=int, target_id=int))
def get_page_move(app, subject_id, direction, target_id):
    return OrganizationMove(app.session(), subject_id, target_id, direction)


@GazetteApp.path(model=IssueCollection, path='/issues')
def get_issues(app):
    return IssueCollection(app.session())


@GazetteApp.path(model=Issue, path='/issue/{name}')
def get_issue(app, name):
    return IssueCollection(app.session()).by_name(name)


@GazetteApp.path(model=IssuePdfFile, path='/pdf/{name}')
def get_issue_pdf(request, app, name):
    issue = IssueCollection(app.session()).by_name(name.replace('.pdf', ''))
    if issue and issue.pdf:
        return get_file(app, issue.pdf.id)


@GazetteApp.path(
    model=GazetteNoticeCollection,
    path='/notices/{state}',
    converters=dict(
        from_date=extended_date_converter,
        to_date=extended_date_converter,
        source=uuid_converter
    )
)
def get_notices(app, state, page=0, term=None, order=None, direction=None,
                from_date=None, to_date=None, source=None):
    return GazetteNoticeCollection(
        app.session(),
        state=state,
        page=page,
        term=term,
        order=order,
        direction=direction,
        from_date=from_date,
        to_date=to_date,
        source=source
    )


@GazetteApp.path(model=GazetteNotice, path='/notice/{name}')
def get_notice(app, name):
    return GazetteNoticeCollection(app.session()).by_name(name)
