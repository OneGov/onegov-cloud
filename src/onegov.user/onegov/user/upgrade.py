""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import JSON
from sqlalchemy import Column


@upgrade_task('Add second_factor column')
def add_second_factor_column(context):
    context.operations.add_column(
        'users', Column('second_factor', JSON, nullable=True)
    )
