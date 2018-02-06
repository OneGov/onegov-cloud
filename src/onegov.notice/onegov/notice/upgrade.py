""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE


@upgrade_task('Add categories column to official notices')
def add_categories(context):
    if not context.has_column('official_notices', 'categories'):
        context.operations.add_column(
            'official_notices',
            Column('categories', HSTORE, nullable=True)
        )


@upgrade_task('Add organizations column to official notices')
def add_organizations(context):
    if not context.has_column('official_notices', 'organizations'):
        context.operations.add_column(
            'official_notices',
            Column('organizations', HSTORE, nullable=True)
        )


@upgrade_task('Add author fields to official notices')
def add_author_fields(context):
    if not context.has_column('official_notices', 'author_name'):
        context.operations.add_column(
            'official_notices',
            Column('author_name', Text, nullable=True)
        )
    if not context.has_column('official_notices', 'author_place'):
        context.operations.add_column(
            'official_notices',
            Column('author_place', Text, nullable=True)
        )
    if not context.has_column('official_notices', 'author_date'):
        context.operations.add_column(
            'official_notices',
            Column('author_date', UTCDateTime, nullable=True)
        )
