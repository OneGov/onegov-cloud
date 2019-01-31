""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import UUID
from sqlalchemy import ForeignKey
from sqlalchemy import Column


@upgrade_task('Add group_id to municipalities')
def add_group_id_to_municipalities(context):
    if not context.has_column('wtfs_municipalities', 'group_id'):
        context.operations.add_column(
            'wtfs_municipalities',
            Column(
                'group_id', UUID, ForeignKey("groups.id"), nullable=True
            )
        )
