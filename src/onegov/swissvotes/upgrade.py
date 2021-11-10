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


@upgrade_task('Removes decade column')
def remove_decade_column(context):
    if context.has_column('swissvotes', 'decade'):
        context.operations.drop_column('swissvotes', 'decade')


@upgrade_task('Adds links for extensions 2019')
def add_curiavista_and_additional_links(context):

    new_cols = (
        'curia_vista_de',
        'curia_vista_fr',
        'bkresults_de',
        'bkresults_fr',
        'bkchrono_de',
        'bkchrono_fr'
    )

    for col in new_cols:
        if not context.has_column('swissvotes', col):
            context.operations.add_column('swissvotes', Column(col, Text()))


@upgrade_task('Adds poster_yes and poster_no')
def add_poster_yes_no(context):
    for col in ('posters_yes', 'posters_no'):
        if not context.has_column('swissvotes', col):
            context.operations.add_column('swissvotes', Column(col, Text()))


@upgrade_task('Adds meta and content for external data sources')
def add_meta_content(context):

    if not context.has_column('swissvotes', 'meta'):
        context.add_column_with_defaults(
            'swissvotes',
            Column('meta', JSON, nullable=False),
            default=dict()
        )

    if not context.has_column('swissvotes', 'content'):
        context.add_column_with_defaults(
            'swissvotes',
            Column('content', JSON, nullable=False),
            default=dict()
        )


@upgrade_task('Adds swissvoteslink')
def add_swissvoteslink(context):
    if not context.has_column('swissvotes', 'swissvoteslink'):
        context.operations.add_column(
            'swissvotes', Column('swissvoteslink', Text())
        )


@upgrade_task('Changes procedure number type to text')
def change_procedure_number_type(context):
    context.operations.execute(
        'ALTER TABLE swissvotes ALTER COLUMN procedure_number TYPE TEXT'
    )


@upgrade_task('Adds post-vote poll links')
def add_post_vote_poll_links(context):
    columns = (
        'post_vote_poll_link_de',
        'post_vote_poll_link_fr',
        'post_vote_poll_link_en'
    )
    for column in columns:
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text()))


@upgrade_task('Adds media fields')
def add_media_fields(context):
    columns = (
        ('media_ads_total', Integer()),
        ('media_ads_per_issue', Numeric(13, 10)),
        ('media_ads_yea', Integer()),
        ('media_ads_nay', Integer()),
        ('media_ads_neutral', Integer()),
        ('media_ads_yea_p', Numeric(13, 10)),
        ('media_coverage_articles_total', Integer()),
        ('media_coverage_articles_d', Integer()),
        ('media_coverage_articles_f', Integer()),
        ('media_coverage_tonality_total', Integer()),
        ('media_coverage_tonality_d', Integer()),
        ('media_coverage_tonality_f', Integer()),
    )
    for column, type_ in columns:
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, type_))


@upgrade_task(
    'Add additional poster links',
    requires='onegov.swissvotes:Adds poster_yes and poster_no'
)
def add_additional_poster_links(context):
    for old, new in (
        ('posters_yes', 'posters_mfg_yea'),
        ('posters_no', 'posters_mfg_nay')
    ):
        if (
            context.has_column('swissvotes', old)
            and not context.has_column('swissvotes', new)
        ):
            context.operations.alter_column(
                'swissvotes', old, new_column_name=new
            )
    for column in ('posters_sa_yea', 'posters_sa_nay'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text()))


@upgrade_task('Change media tonality types to numeric')
def change_media_tonality_types(context):
    context.operations.execute(
        'ALTER TABLE swissvotes '
        'ALTER COLUMN media_coverage_tonality_total TYPE NUMERIC(13, 10)'
    )
    context.operations.execute(
        'ALTER TABLE swissvotes '
        'ALTER COLUMN media_coverage_tonality_d TYPE NUMERIC(13, 10)'
    )
    context.operations.execute(
        'ALTER TABLE swissvotes '
        'ALTER COLUMN media_coverage_tonality_f TYPE NUMERIC(13, 10)'
    )


@upgrade_task('Adds die Mitte columns')
def add_die_mittel_columns(context):
    if not context.has_column('swissvotes', 'national_council_share_mitte'):
        context.operations.add_column(
            'swissvotes',
            Column('national_council_share_mitte', Numeric(13, 10))
        )


@upgrade_task('Adds brief description title column')
def add_brief_description_title(context):
    if not context.has_column('swissvotes', 'brief_description_title'):
        context.operations.add_column(
            'swissvotes',
            Column('brief_description_title', Text())
        )


@upgrade_task('Moves links to meta')
def move_links_to_meta(context):
    columns = (
        'bkchrono_de',
        'bkchrono_fr',
        'bkresults_de',
        'bkresults_fr',
        'curia_vista_de',
        'curia_vista_fr',
        'post_vote_poll_link_de',
        'post_vote_poll_link_fr',
        'post_vote_poll_link_en',
    )
    for column in columns:
        if context.has_column('swissvotes', column):
            context.operations.drop_column('swissvotes', column)


@upgrade_task('Drops unused columns')
def drop_unused_columns(context):
    columns = (
        'media_ads_per_issue',
        'media_ads_yea',
        'media_ads_nay',
        'media_ads_neutral',
        'media_coverage_articles_d',
        'media_coverage_articles_f',
        'media_coverage_tonality_d',
        'media_coverage_tonality_f',
        'result_eligible_voters',
        'result_votes_empty',
        'result_votes_invalid',
        'result_votes_valid',
        'result_votes_total',
        'result_ag_eligible_voters',
        'result_ag_votes_valid',
        'result_ag_votes_total',
        'result_ag_turnout',
        'result_ag_yeas',
        'result_ag_nays',
        'result_ag_yeas_p',
        'result_ai_eligible_voters',
        'result_ai_votes_valid',
        'result_ai_votes_total',
        'result_ai_turnout',
        'result_ai_yeas',
        'result_ai_nays',
        'result_ai_yeas_p',
        'result_ar_eligible_voters',
        'result_ar_votes_valid',
        'result_ar_votes_total',
        'result_ar_turnout',
        'result_ar_yeas',
        'result_ar_nays',
        'result_ar_yeas_p',
        'result_be_eligible_voters',
        'result_be_votes_valid',
        'result_be_votes_total',
        'result_be_turnout',
        'result_be_yeas',
        'result_be_nays',
        'result_be_yeas_p',
        'result_bl_eligible_voters',
        'result_bl_votes_valid',
        'result_bl_votes_total',
        'result_bl_turnout',
        'result_bl_yeas',
        'result_bl_nays',
        'result_bl_yeas_p',
        'result_bs_eligible_voters',
        'result_bs_votes_valid',
        'result_bs_votes_total',
        'result_bs_turnout',
        'result_bs_yeas',
        'result_bs_nays',
        'result_bs_yeas_p',
        'result_fr_eligible_voters',
        'result_fr_votes_valid',
        'result_fr_votes_total',
        'result_fr_turnout',
        'result_fr_yeas',
        'result_fr_nays',
        'result_fr_yeas_p',
        'result_ge_eligible_voters',
        'result_ge_votes_valid',
        'result_ge_votes_total',
        'result_ge_turnout',
        'result_ge_yeas',
        'result_ge_nays',
        'result_ge_yeas_p',
        'result_gl_eligible_voters',
        'result_gl_votes_valid',
        'result_gl_votes_total',
        'result_gl_turnout',
        'result_gl_yeas',
        'result_gl_nays',
        'result_gl_yeas_p',
        'result_gr_eligible_voters',
        'result_gr_votes_valid',
        'result_gr_votes_total',
        'result_gr_turnout',
        'result_gr_yeas',
        'result_gr_nays',
        'result_gr_yeas_p',
        'result_ju_eligible_voters',
        'result_ju_votes_valid',
        'result_ju_votes_total',
        'result_ju_turnout',
        'result_ju_yeas',
        'result_ju_nays',
        'result_ju_yeas_p',
        'result_lu_eligible_voters',
        'result_lu_votes_valid',
        'result_lu_votes_total',
        'result_lu_turnout',
        'result_lu_yeas',
        'result_lu_nays',
        'result_lu_yeas_p',
        'result_ne_eligible_voters',
        'result_ne_votes_valid',
        'result_ne_votes_total',
        'result_ne_turnout',
        'result_ne_yeas',
        'result_ne_nays',
        'result_ne_yeas_p',
        'result_nw_eligible_voters',
        'result_nw_votes_valid',
        'result_nw_votes_total',
        'result_nw_turnout',
        'result_nw_yeas',
        'result_nw_nays',
        'result_nw_yeas_p',
        'result_ow_eligible_voters',
        'result_ow_votes_valid',
        'result_ow_votes_total',
        'result_ow_turnout',
        'result_ow_yeas',
        'result_ow_nays',
        'result_ow_yeas_p',
        'result_sg_eligible_voters',
        'result_sg_votes_valid',
        'result_sg_votes_total',
        'result_sg_turnout',
        'result_sg_yeas',
        'result_sg_nays',
        'result_sg_yeas_p',
        'result_sh_eligible_voters',
        'result_sh_votes_valid',
        'result_sh_votes_total',
        'result_sh_turnout',
        'result_sh_yeas',
        'result_sh_nays',
        'result_sh_yeas_p',
        'result_so_eligible_voters',
        'result_so_votes_valid',
        'result_so_votes_total',
        'result_so_turnout',
        'result_so_yeas',
        'result_so_nays',
        'result_so_yeas_p',
        'result_sz_eligible_voters',
        'result_sz_votes_valid',
        'result_sz_votes_total',
        'result_sz_turnout',
        'result_sz_yeas',
        'result_sz_nays',
        'result_sz_yeas_p',
        'result_tg_eligible_voters',
        'result_tg_votes_valid',
        'result_tg_votes_total',
        'result_tg_turnout',
        'result_tg_yeas',
        'result_tg_nays',
        'result_tg_yeas_p',
        'result_ti_eligible_voters',
        'result_ti_votes_valid',
        'result_ti_votes_total',
        'result_ti_turnout',
        'result_ti_yeas',
        'result_ti_nays',
        'result_ti_yeas_p',
        'result_ur_eligible_voters',
        'result_ur_votes_valid',
        'result_ur_votes_total',
        'result_ur_turnout',
        'result_ur_yeas',
        'result_ur_nays',
        'result_ur_yeas_p',
        'result_vd_eligible_voters',
        'result_vd_votes_valid',
        'result_vd_votes_total',
        'result_vd_turnout',
        'result_vd_yeas',
        'result_vd_nays',
        'result_vd_yeas_p',
        'result_vs_eligible_voters',
        'result_vs_votes_valid',
        'result_vs_votes_total',
        'result_vs_turnout',
        'result_vs_yeas',
        'result_vs_nays',
        'result_vs_yeas_p',
        'result_zg_eligible_voters',
        'result_zg_votes_valid',
        'result_zg_votes_total',
        'result_zg_turnout',
        'result_zg_yeas',
        'result_zg_nays',
        'result_zg_yeas_p',
        'result_zh_eligible_voters',
        'result_zh_votes_valid',
        'result_zh_votes_total',
        'result_zh_turnout',
        'result_zh_yeas',
        'result_zh_nays',
        'result_zh_yeas_p',
        'legislation_number',
        'legislation_decade'
    )
    for column in columns:
        if context.has_column('swissvotes', column):
            context.operations.drop_column('swissvotes', column)
