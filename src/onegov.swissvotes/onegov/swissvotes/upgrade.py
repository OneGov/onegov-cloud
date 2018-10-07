""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.swissvotes.models import SwissVote
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR


@upgrade_task('Rename recommendation columns')
def rename_recommendation_columns(context):
    for old, new in (
        ('ucsp', 'csp'),
        ('sbv', 'sbv_usp'),
        ('cng_travs', 'travs'),
        ('zsa', 'sav')
    ):
        old = f'recommendation_{old}'
        new = f'recommendation_{new}'
        if (
            context.has_column('swissvotes', old) and
            not context.has_column('swissvotes', new)
        ):
            context.operations.alter_column(
                'swissvotes', old, new_column_name=new
            )


@upgrade_task('Add tsvector columns')
def add_tsvector_columns(context):
    for column in ('searchable_text_de_CH', 'searchable_text_fr_CH', 'french'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, TSVECTOR())
            )

    for vote in context.app.session().query(SwissVote):
        vote.vectorize_files()
