""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.core.upgrade import UpgradeContext
from onegov.gazette.collections.categories import CategoryCollection
from onegov.gazette.collections.issues import IssueCollection
from onegov.gazette.collections.organizations import OrganizationCollection
from onegov.gazette.models.notice import GazetteNotice
from sedate import standardize_date
from sqlalchemy.schema import Column


@upgrade_task(
    'Move gazette category IDs',
    requires='onegov.notice:Add categories column to official notices'
)
def migrate_category_ids(context: UpgradeContext) -> None:
    for notice in context.session.query(GazetteNotice):
        if notice.meta:
            if 'category_id' in notice.meta:
                category_id = notice.meta['category_id']
                notice.category_id = category_id
                del notice.meta['category_id']


@upgrade_task(
    'Move gazette organization IDs',
    requires='onegov.notice:Add organizations column to official notices'
)
def migrate_organization_ids(context: UpgradeContext) -> None:
    for notice in context.session.query(GazetteNotice):
        if notice.meta:
            if 'organization_id' in notice.meta:
                organization_id = notice.meta['organization_id']
                notice.organization_id = organization_id
                del notice.meta['organization_id']


@upgrade_task('Migrate gazette categories')
def migrate_categories(context: UpgradeContext) -> bool | None:
    principal = getattr(context.app, 'principal', None)
    if not principal:
        return False

    categories = getattr(principal, '_categories', None)
    if not categories:
        return False

    if not context.has_table('gazette_categories'):
        return False

    session = context.app.session_manager.session()
    count = session.execute('select count(*) from gazette_categories')
    if count.scalar() != 0:
        return False

    collection = CategoryCollection(session)
    for name, title in categories.items():
        collection.add_root(name=name, title=title, active=True)

    return None


@upgrade_task('Migrate gazette organizations')
def migrate_organizations(context: UpgradeContext) -> bool | None:
    principal = getattr(context.app, 'principal', None)
    if not principal:
        return False

    organizations = getattr(principal, '_organizations', None)
    if not organizations:
        return False

    if not context.has_table('gazette_organizations'):
        return False

    session = context.app.session_manager.session()
    count = session.execute('select count(*) from gazette_organizations')
    if count.scalar() != 0:
        return False

    collection = OrganizationCollection(session)
    for index, name in enumerate(organizations):
        collection.add_root(
            name=name,
            title=organizations[name],
            active=True,
            order=index
        )

    return None


@upgrade_task('Migrate gazette issues')
def migrate_issues(context: UpgradeContext) -> bool | None:
    principal = getattr(context.app, 'principal', None)
    if not principal:
        return False

    issues = getattr(principal, '_issues', None)
    if not issues:
        return False

    if not context.has_table('gazette_issues'):
        return False

    session = context.app.session_manager.session()
    count = session.execute('select count(*) from gazette_issues')
    if count.scalar() != 0:
        return False

    collection = IssueCollection(session)
    for year, values in issues.items():
        for number, dates in values.items():
            assert dates.issue_date.year == year
            collection.add(
                name='{}-{}'.format(year, number),
                number=number,
                date=dates.issue_date,
                deadline=standardize_date(dates.deadline, 'UTC')
            )

    return None


@upgrade_task('Add content and meta data')
def add_content_and_meta_data_columns(context: UpgradeContext) -> None:
    if not context.has_column('gazette_categories', 'meta'):
        context.operations.add_column(
            'gazette_categories',
            Column('meta', JSON)
        )
    if not context.has_column('gazette_categories', 'content'):
        context.operations.add_column(
            'gazette_categories',
            Column('content', JSON)
        )

    if not context.has_column('gazette_organizations', 'meta'):
        context.operations.add_column(
            'gazette_organizations',
            Column('meta', JSON)
        )
    if not context.has_column('gazette_organizations', 'content'):
        context.operations.add_column(
            'gazette_organizations',
            Column('content', JSON)
        )


@upgrade_task('Make gazette models polymorphic type non-nullable')
def make_gazette_models_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    for table in ('gazette_categories', 'gazette_organizations'):
        if context.has_table(table):
            context.operations.execute(f"""
                UPDATE {table} SET type = 'generic' WHERE type IS NULL;
            """)

            context.operations.alter_column(table, 'type', nullable=False)
