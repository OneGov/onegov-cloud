""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from sqlalchemy import Text, Column, Computed  # type: ignore[attr-defined]
from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.upgrade import upgrade_task
from onegov.search.utils import searchable_sqlalchemy_models


def get_tsvector_index_data_column(model):
    """ Returns the tsvector for the 'index data' column. """

    column_string = "coalesce(fts_idx_data, '')"
    languages = ['simple', 'german', 'english', 'french', 'italian']

    tsvector = ' || '.join(
        "to_tsvector('{}', {})".format(language, column_string)
        for language in languages
    )

    return tsvector


@upgrade_task('Adds fts index and fts index data columns to all '
              'searchable models')
def adds_index_data_columns(context):
    models = [model for base in context.app.session_manager.bases
              for model in searchable_sqlalchemy_models(base)]
    for model in models:
        if not context.has_column(model.__tablename__, 'fts_idx_data'):
            context.operations.add_column(
                model.__tablename__, Column('fts_idx_data', Text, default='')
            )

        if not context.has_column(model.__tablename__, 'fts_idx'):
            context.operations.add_column(
                model.__tablename__,
                Column(
                    'fts_idx',
                    TSVECTOR,
                    Computed(
                        get_tsvector_index_data_column(model),
                        persisted=True
                    ),
                )
            )
