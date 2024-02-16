""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Text, Column
from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.orm import Base
from onegov.core.upgrade import upgrade_task
from onegov.search.utils import searchable_sqlalchemy_models


@upgrade_task('Adds fts index and fts index data columns to all models')
def adds_index_data_columns(context):
    for model in searchable_sqlalchemy_models(Base):
        if not context.has_column(model.__tablename__, 'fts_idx'):
            context.operations.add_column(
                model.__tablename__, Column('fts_idx', TSVECTOR, default='')
            )
        if not context.has_column(model.__tablename__, 'fts_idx_data'):
            context.operations.add_column(
                model.__tablename__, Column('fts_idx_data', Text, default='')
            )
