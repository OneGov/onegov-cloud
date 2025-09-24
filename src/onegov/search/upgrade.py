""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.search.utils import searchable_sqlalchemy_models


@upgrade_task('Remove fts index column from all searchable models')
def remove_fts_index_columns(context: UpgradeContext) -> None:
    tables = {
        model.__tablename__
        for base in context.app.session_manager.bases
        for model in searchable_sqlalchemy_models(base)
    }
    for table in tables:
        if context.has_column(table, 'fts_idx'):
            context.operations.drop_column(table, 'fts_idx')
