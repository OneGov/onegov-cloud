from onegov.core.converters import extended_date_converter
from onegov.core.converters import move_direction_converter
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


from typing import Literal
from typing import TypeGuard
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.core.orm.abstract import MoveDirection
    from onegov.gazette.request import GazetteRequest
    from uuid import UUID


@GazetteApp.path(model=Auth, path='/auth')
def get_auth(request: 'GazetteRequest', to: str = '/') -> Auth:
    return Auth.from_request(request, to)


@GazetteApp.path(model=Principal, path='/')
def get_principal(app: GazetteApp) -> Principal:
    return app.principal


@GazetteApp.path(model=UserCollection, path='/users')
def get_users(app: GazetteApp) -> UserCollection:
    return UserCollection(app.session())


@GazetteApp.path(model=User, path='/user/{username}')
def get_user(app: GazetteApp, username: str) -> User | None:
    return UserCollection(app.session()).by_username(username)


@GazetteApp.path(model=UserGroupCollection, path='/groups')
def get_groups(app: GazetteApp) -> UserGroupCollection[UserGroup]:
    return UserGroupCollection(app.session())


@GazetteApp.path(model=UserGroup, path='/group/{id}')
def get_group(app: GazetteApp, id: str) -> UserGroup | None:
    return UserGroupCollection(app.session()).by_id(id)


@GazetteApp.path(model=CategoryCollection, path='/categories')
def get_categories(app: GazetteApp) -> CategoryCollection:
    return CategoryCollection(app.session())


@GazetteApp.path(
    model=Category,
    path='/category/{id}',
    converters={'id': int}
)
def get_category(app: GazetteApp, id: int) -> Category | None:
    return CategoryCollection(app.session()).by_id(id)


@GazetteApp.path(model=OrganizationCollection, path='/organizations')
def get_organizations(app: GazetteApp) -> OrganizationCollection:
    return OrganizationCollection(app.session())


@GazetteApp.path(
    model=Organization,
    path='/organization/{id}',
    converters={'id': int}
)
def get_organization(app: GazetteApp, id: int) -> Organization | None:
    return OrganizationCollection(app.session()).by_id(id)


@GazetteApp.path(
    model=OrganizationMove,
    path='/move/organization/{subject_id}/{direction}/{target_id}',
    converters={
        'subject_id': int,
        'direction': move_direction_converter,
        'target_id': int
    }
)
def get_page_move(
    app: GazetteApp,
    subject_id: int,
    direction: 'MoveDirection',
    target_id: int
) -> OrganizationMove:
    return OrganizationMove(app.session(), subject_id, target_id, direction)


@GazetteApp.path(model=IssueCollection, path='/issues')
def get_issues(app: GazetteApp) -> IssueCollection:
    return IssueCollection(app.session())


@GazetteApp.path(model=Issue, path='/issue/{name}')
def get_issue(app: GazetteApp, name: str) -> Issue | None:
    return IssueCollection(app.session()).by_name(name)


@GazetteApp.path(model=IssuePdfFile, path='/pdf/{name}')
def get_issue_pdf(
    request: 'GazetteRequest',
    app: GazetteApp,
    name: str
) -> IssuePdfFile | None:
    issue = IssueCollection(app.session()).by_name(name.replace('.pdf', ''))
    if issue and issue.pdf:
        # FIXME: Isn't this call to get_file redundant?
        return get_file(app, issue.pdf.id)  # type: ignore[return-value]
    return None


# FIXME: return None for invalid state? (i.e. return 404)
@GazetteApp.path(
    model=GazetteNoticeCollection,
    path='/notices/{state}',
    converters={
        'from_date': extended_date_converter,
        'to_date': extended_date_converter,
        'categories': [str],
        'organizations': [str],
        'source': uuid_converter,
        'own': bool
    }
)
def get_notices(
    app: GazetteApp,
    state: str,
    page: int = 0,
    term: str | None = None,
    order: str | None = None,
    direction: str | None = None,
    from_date: 'date | None' = None,
    to_date: 'date | None' = None,
    categories: list[str] | None = None,
    organizations: list[str] | None = None,
    source: 'UUID | None' = None,
    own: bool | None = None
) -> GazetteNoticeCollection:

    def is_direction(value: str | None) -> TypeGuard[Literal['asc', 'desc']]:
        return value in ('asc', 'desc')

    if not is_direction(direction):
        # avoid exceptions for invalid direction
        direction = None

    categories = [c for c in categories if c] if categories else None
    organizations = [c for c in organizations if c] if organizations else None
    return GazetteNoticeCollection(
        app.session(),
        state=state,  # type:ignore[arg-type]
        page=page,
        term=term,
        order=order,
        direction=direction,
        from_date=from_date,
        to_date=to_date,
        categories=categories,
        organizations=organizations,
        source=source,
        own=own
    )


@GazetteApp.path(model=GazetteNotice, path='/notice/{name}')
def get_notice(app: GazetteApp, name: str) -> GazetteNotice | None:
    return GazetteNoticeCollection(app.session()).by_name(name)
