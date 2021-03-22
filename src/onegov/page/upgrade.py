""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Column

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from sqlalchemy.sql.expression import text


@upgrade_task('Add parent order index')
def add_parent_order_index(context):
    context.operations.create_index(
        'page_order', 'pages', [
            text('"parent_id" NULLS FIRST'),
            text('"order" NULLS FIRST')
        ]
    )


@upgrade_task('Adds publication dates to pages')
def add_publication_dates_to_pages(context):
    if not context.has_column('pages', 'publication_start'):
        context.operations.add_column(
            'pages',
            Column('publication_start', UTCDateTime, nullable=True)
        )
    if not context.has_column('pages', 'publication_end'):
        context.operations.add_column(
            'pages',
            Column('publication_end', UTCDateTime, nullable=True)
        )
