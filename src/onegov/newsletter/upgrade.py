""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import UTCDateTime, JSON
from sqlalchemy import Column


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add scheduled column')
def add_scheduled_column(context: 'UpgradeContext') -> None:
    context.operations.add_column('newsletters', Column(
        'scheduled', UTCDateTime, nullable=True
    ))


@upgrade_task('Add content and meta columns')
def add_content_column(context: 'UpgradeContext') -> None:
    if not context.has_column('recipients', 'content'):
        context.operations.add_column('recipients', Column('content', JSON()))
    if not context.has_column('recipients', 'meta'):
        context.operations.add_column('recipients', Column('meta', JSON()))
