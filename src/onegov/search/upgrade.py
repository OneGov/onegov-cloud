""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.search.utils import searchable_sqlalchemy_models
from sqlalchemy import inspect, String
from sqlalchemy.dialects.postgresql import ARRAY


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


@upgrade_task('Make last_change nullable')
def make_last_change_nullable(context: UpgradeContext) -> None:
    if context.has_table('search_index'):
        context.operations.alter_column(
            'search_index',
            'last_change',
            nullable=True
        )


@upgrade_task('Change tags from HSTORE to ARRAY')
def change_tags_from_hstore_to_array(context: UpgradeContext) -> None:
    if context.has_table('search_index'):
        ins = inspect(context.engine)
        for meta in ins.get_columns('search_index', context.schema):
            if meta['name'] == 'tags':
                current_type = meta['type']
                break
        else:
            # the column doesn't exist, although this shouldn't happen
            # let's just do nothing for now, if it ever does
            return

        if isinstance(current_type, ARRAY):
            # the column is already the correct type
            return
        context.operations.alter_column(
            'search_index',
            'tags',
            type_=ARRAY(String),
            postgresql_using='akeys(tags)'
        )
