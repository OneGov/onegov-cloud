""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import UTCDateTime
from sqlalchemy import Column


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add scheduled column')
def add_scheduled_column(context: 'UpgradeContext') -> None:
    context.operations.add_column('newsletters', Column(
        'scheduled', UTCDateTime, nullable=True
    ))
