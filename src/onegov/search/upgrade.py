""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.search.utils import searchable_sqlalchemy_models


@upgrade_task('Adds fts index column to all searchable models')
def adds_index_data_columns(context: UpgradeContext) -> None:
    models = (
        model
        for base in context.app.session_manager.bases
        for model in searchable_sqlalchemy_models(base)
    )
    for model in models:
        assert hasattr(model, '__tablename__')
        if not context.has_column(model.__tablename__, 'fts_idx'):
            context.operations.add_column(
                model.__tablename__,
                Column(
                    'fts_idx',
                    TSVECTOR,
                )
            )
