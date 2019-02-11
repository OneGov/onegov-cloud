""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import TranslatablePage
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Numeric
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
            context.has_column('swissvotes', old)
            and not context.has_column('swissvotes', new)
        ):
            context.operations.alter_column(
                'swissvotes', old, new_column_name=new
            )


@upgrade_task('Add tsvector columns')
def add_tsvector_columns(context):
    for column in ('searchable_text_de_CH', 'searchable_text_fr_CH'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, TSVECTOR())
            )

    for vote in context.app.session().query(SwissVote):
        vote.vectorize_files()


@upgrade_task('Add parliament position columns')
def add_parliament_position_columns(context):
    columns = ('position_national_council', 'position_council_of_states')

    for col in columns:
        if not context.has_column('swissvotes', col):
            context.operations.add_column('swissvotes', Column(col, Integer))

    for vote in context.app.session().query(SwissVote):
        for col in columns:
            yeas = getattr(vote, f'{col}_yeas')
            nays = getattr(vote, f'{col}_nays')
            if yeas is not None and nays is not None:
                if yeas > nays:
                    setattr(vote, f'_{col}', 1)
                elif yeas < nays:
                    setattr(vote, f'_{col}', 2)


@upgrade_task('Add cantonal result columns')
def add_cantonal_result_columns(context):
    for canton in (
        'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
        'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
        'zg', 'zh'
    ):
        for column in (
            f'result_{canton}_eligible_voters',
            f'result_{canton}_votes_valid',
            f'result_{canton}_votes_total',
            f'result_{canton}_yeas',
            f'result_{canton}_nays',
            f'result_{canton}_accepted'
        ):
            if not context.has_column('swissvotes', column):
                context.operations.add_column(
                    'swissvotes', Column(column, Integer)
                )

        for column in (
            f'result_{canton}_turnout',
            f'result_{canton}_yeas_p'
        ):
            if not context.has_column('swissvotes', column):
                context.operations.add_column(
                    'swissvotes', Column(column, Numeric(13, 10))
                )


@upgrade_task('Add order column to pages')
def add_order_column_to_pagess(context):
    if context.has_column('swissvotes_page', 'order'):
        context.operations.drop_column(
            'swissvotes_page', 'order'
        )
    if not context.has_column('swissvotes_page', 'order'):
        context.operations.add_column(
            'swissvotes_page',
            Column('order', Integer, default=2 ** 16)
        )

        default = (
            'home', 'disclaimer', 'imprint', 'data-protection', 'dataset',
            'about', 'contact'
        )
        pages = TranslatablePageCollection(context.app.session())
        for id in default:
            pages.setdefault(id)
        for order, id in enumerate(default):
            pages.by_id(id).order = order
        for page in pages.query().filter(TranslatablePage.id.notin_(default)):
            order += 1
            page.order = order
