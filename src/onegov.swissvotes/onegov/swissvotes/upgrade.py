""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm import as_selectable
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import TranslatablePage
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import select
from sqlalchemy import Text
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


@upgrade_task('Add recommendations column')
def add_recommendations_column(context):
    if not context.has_column('swissvotes', 'recommendations'):
        context.operations.add_column(
            'swissvotes',
            Column('recommendations', JSON())
        )

        query = as_selectable("""
            SELECT
                id,  -- Integer
                recommendation_fdp,  -- Integer
                recommendation_cvp,  -- Integer
                recommendation_sps,  -- Integer
                recommendation_svp,  -- Integer
                recommendation_lps,  -- Integer
                recommendation_ldu,  -- Integer
                recommendation_evp,  -- Integer
                recommendation_csp,  -- Integer
                recommendation_pda,  -- Integer
                recommendation_poch,  -- Integer
                recommendation_gps,  -- Integer
                recommendation_sd,  -- Integer
                recommendation_rep,  -- Integer
                recommendation_edu,  -- Integer
                recommendation_fps,  -- Integer
                recommendation_lega,  -- Integer
                recommendation_kvp,  -- Integer
                recommendation_glp,  -- Integer
                recommendation_bdp,  -- Integer
                recommendation_mcg,  -- Integer
                recommendation_sav,  -- Integer
                recommendation_eco,  -- Integer
                recommendation_sgv,  -- Integer
                recommendation_sbv_usp,  -- Integer
                recommendation_sgb,  -- Integer
                recommendation_travs,  -- Integer
                recommendation_vsa  -- Integer
            FROM
                swissvotes
        """)
        session = context.app.session_manager.session()
        for result in session.execute(select(query.c)):
            vote = session.query(SwissVote).filter_by(id=result.id).one()
            vote.recommendations = {
                'fdp': result.recommendation_fdp,
                'cvp': result.recommendation_cvp,
                'sps': result.recommendation_sps,
                'svp': result.recommendation_svp,
                'lps': result.recommendation_lps,
                'ldu': result.recommendation_ldu,
                'evp': result.recommendation_evp,
                'csp': result.recommendation_csp,
                'pda': result.recommendation_pda,
                'poch': result.recommendation_poch,
                'gps': result.recommendation_gps,
                'sd': result.recommendation_sd,
                'rep': result.recommendation_rep,
                'edu': result.recommendation_edu,
                'fps': result.recommendation_fps,
                'lega': result.recommendation_lega,
                'kvp': result.recommendation_kvp,
                'glp': result.recommendation_glp,
                'bdp': result.recommendation_bdp,
                'mcg': result.recommendation_mcg,
                'sav': result.recommendation_sav,
                'eco': result.recommendation_eco,
                'sgv': result.recommendation_sgv,
                'sbv_usp': result.recommendation_sbv_usp,
                'sgb': result.recommendation_sgb,
                'travs': result.recommendation_travs,
                'vsa': result.recommendation_vsa,
            }

    for column in (
        'recommendation_fdp',
        'recommendation_cvp',
        'recommendation_sps',
        'recommendation_svp',
        'recommendation_lps',
        'recommendation_ldu',
        'recommendation_evp',
        'recommendation_csp',
        'recommendation_pda',
        'recommendation_poch',
        'recommendation_gps',
        'recommendation_sd',
        'recommendation_rep',
        'recommendation_edu',
        'recommendation_fps',
        'recommendation_lega',
        'recommendation_kvp',
        'recommendation_glp',
        'recommendation_bdp',
        'recommendation_mcg',
        'recommendation_sav',
        'recommendation_eco',
        'recommendation_sgv',
        'recommendation_sbv_usp',
        'recommendation_sgb',
        'recommendation_travs',
        'recommendation_vsa'
    ):
        if context.has_column('swissvotes', column):
            context.operations.drop_column('swissvotes', column)


@upgrade_task('Add BFS map link columns')
def add_bfs_map_columns(context):
    if not context.has_column('swissvotes', 'bfs_map_de'):
        context.operations.add_column('swissvotes', Column('bfs_map_de', Text))
    if not context.has_column('swissvotes', 'bfs_map_fr'):
        context.operations.add_column('swissvotes', Column('bfs_map_fr', Text))


@upgrade_task('Add other recommendation columns')
def add_other_recommendation_columns(context):
    for name in ('yes', 'no', 'free'):
        column = f'recommendations_other_{name}'
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text))


@upgrade_task('Add divergent recommendations column')
def add_divergent_recommendations_column(context):
    if not context.has_column('swissvotes', 'recommendations_divergent'):
        context.operations.add_column(
            'swissvotes',
            Column('recommendations_divergent', JSON())
        )


@upgrade_task('Rename sbv-usp column')
def rename_sbv_usp_column(context):
    for vote in context.app.session().query(SwissVote):
        if 'sbv_usp' in vote.recommendations:
            vote.recommendations['sbv-usp'] = vote.recommendations['sbv_usp']
            del vote.recommendations['sbv_usp']


@upgrade_task('Adds french and short titles')
def add_french_and_short_title_columns(context):
    for column in ('title_de', 'title_fr', 'short_title_de', 'short_title_fr'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text()))
    if context.has_column('swissvotes', 'title'):
        context.operations.drop_column('swissvotes', 'title')


@upgrade_task('Adds national council share parole columns')
def add_national_council_share_parole_columns(context):
    for column in (
        'national_council_share_none',
        'national_council_share_empty',
        'national_council_share_free_vote',
        'national_council_share_unknown',
    ):
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, Numeric(13, 10))
            )

    if context.has_column('swissvotes', 'national_council_share_vague'):
        context.operations.drop_column(
            'swissvotes', 'national_council_share_vague'
        )
