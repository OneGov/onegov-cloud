""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.search.utils import searchable_sqlalchemy_models
from sqlalchemy import inspect, Column, String
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR


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


@upgrade_task('Split title and data TSVECTOR')
def split_title_and_data_tsvector_columns(context: UpgradeContext) -> None:
    if not context.has_table('search_index'):
        return

    if context.has_column('search_index', 'fts_idx'):
        # truncate the search index so we don't have to worry about
        # new columns that can't be NULL, the search index will be
        # re-generated after the upgrade steps in production anyways
        context.operations.execute('TRUNCATE search_index')
        context.operations.drop_index(
            'ix_search_index_fts_idx',
            'search_index'
        )
        context.operations.drop_index(
            'ix_search_index_fts_idx_data',
            'search_index'
        )
        context.operations.drop_column('search_index', 'fts_idx')
        context.operations.drop_column('search_index', 'fts_idx_data')
        context.operations.add_column(
            'search_index',
             Column('title_vector', TSVECTOR, nullable=False)
        )
        context.operations.add_column(
            'search_index',
             Column('data_vector', TSVECTOR, nullable=False)
        )
        context.operations.create_index(
            'ix_search_index_title_vector',
            'search_index',
            columns=['title_vector'],
            postgresql_using='gin'
        )
        context.operations.create_index(
            'ix_search_index_data_vector',
            'search_index',
            columns=['data_vector'],
            postgresql_using='gin'
        )


@upgrade_task('Create it_ch text search config')
def create_it_ch_text_search_config(context: UpgradeContext) -> None:
    context.operations.execute("""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_ts_config
            WHERE cfgname = 'it_ch'
            AND cfgnamespace = CURRENT_SCHEMA()::regnamespace
          ) THEN
            CREATE TEXT SEARCH CONFIGURATION it_ch ( COPY = italian );
          END IF;
        END
        $$;
    """)
