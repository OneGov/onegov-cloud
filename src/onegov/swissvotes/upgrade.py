""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.core.upgrade import UpgradeContext
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import TSVECTOR


@upgrade_task('Rename recommendation columns')
def rename_recommendation_columns(context: UpgradeContext) -> None:
    pass  # deleted later


@upgrade_task('Add tsvector columns')
def add_tsvector_columns(context: UpgradeContext) -> None:
    for column in ('searchable_text_de_CH', 'searchable_text_fr_CH'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, TSVECTOR())
            )


@upgrade_task('Add parliament position columns')
def add_parliament_position_columns(context: UpgradeContext) -> None:
    columns = ('position_national_council', 'position_council_of_states')

    for col in columns:
        if not context.has_column('swissvotes', col):
            context.operations.add_column('swissvotes', Column(col, Integer))


@upgrade_task('Add cantonal result columns')
def add_cantonal_result_columns(context: UpgradeContext) -> None:
    for canton in (
        'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
        'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
        'zg', 'zh'
    ):
        column = f'result_{canton}_accepted'
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, Integer)
            )


@upgrade_task('Add order column to pages')
def add_order_column_to_pagess(context: UpgradeContext) -> None:
    if context.has_column('swissvotes_page', 'order'):
        context.operations.drop_column(
            'swissvotes_page', 'order'
        )
    if not context.has_column('swissvotes_page', 'order'):
        context.operations.add_column(
            'swissvotes_page',
            Column('order', Integer, default=2 ** 16)
        )


@upgrade_task('Add recommendations column')
def add_recommendations_column(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'recommendations'):
        context.operations.add_column(
            'swissvotes',
            Column('recommendations', JSON())
        )

    for column in (
        'recommendation_fdp',
        'recommendation_cvp',
        'recommendation_sps',
        'recommendation_svp',
        'recommendation_lps',
        'recommendation_ldu',
        'recommendation_evp',
        'recommendation_ucsp',
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
        'recommendation_zsa',
        'recommendation_sav',
        'recommendation_eco',
        'recommendation_sgv',
        'recommendation_sbv',
        'recommendation_sbv_usp',
        'recommendation_sgb',
        'recommendation_cng_travs',
        'recommendation_travs',
        'recommendation_vsa'
    ):
        if context.has_column('swissvotes', column):
            context.operations.drop_column('swissvotes', column)


@upgrade_task('Add BFS map link columns')
def add_bfs_map_columns(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'bfs_map_de'):
        context.operations.add_column('swissvotes', Column('bfs_map_de', Text))
    if not context.has_column('swissvotes', 'bfs_map_fr'):
        context.operations.add_column('swissvotes', Column('bfs_map_fr', Text))


@upgrade_task('Add other recommendation columns')
def add_other_recommendation_columns(context: UpgradeContext) -> None:
    for name in ('yes', 'no', 'free'):
        column = f'recommendations_other_{name}'
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text))


@upgrade_task('Add divergent recommendations column')
def add_divergent_recommendations_column(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'recommendations_divergent'):
        context.operations.add_column(
            'swissvotes',
            Column('recommendations_divergent', JSON())
        )


@upgrade_task('Rename sbv-usp column')
def rename_sbv_usp_column(context: UpgradeContext) -> None:
    pass


@upgrade_task('Adds french and short titles')
def add_french_and_short_title_columns(context: UpgradeContext) -> None:
    for column in ('title_de', 'title_fr', 'short_title_de', 'short_title_fr'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text()))
    if context.has_column('swissvotes', 'title'):
        context.operations.drop_column('swissvotes', 'title')


@upgrade_task('Adds national council share parole columns')
def add_national_council_share_parole_columns(context: UpgradeContext) -> None:
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
def remove_decade_column(context: UpgradeContext) -> None:
    if context.has_column('swissvotes', 'decade'):
        context.operations.drop_column('swissvotes', 'decade')


@upgrade_task('Adds links for extensions 2019')
def add_curiavista_and_additional_links(context: UpgradeContext) -> None:
    pass  # deleted


@upgrade_task('Adds poster_yes and poster_no')
def add_poster_yes_no(context: UpgradeContext) -> None:
    for col in ('posters_yes', 'posters_no'):
        if not context.has_column('swissvotes', col):
            context.operations.add_column('swissvotes', Column(col, Text()))


@upgrade_task('Adds meta and content for external data sources')
def add_meta_content(context: UpgradeContext) -> None:

    if not context.has_column('swissvotes', 'meta'):
        context.add_column_with_defaults(
            'swissvotes',
            Column('meta', JSON, nullable=False),
            default={}
        )

    if not context.has_column('swissvotes', 'content'):
        context.add_column_with_defaults(
            'swissvotes',
            Column('content', JSON, nullable=False),
            default={}
        )


@upgrade_task('Adds swissvoteslink')
def add_swissvoteslink(context: UpgradeContext) -> None:
    pass  # deleted later


@upgrade_task('Changes procedure number type to text')
def change_procedure_number_type(context: UpgradeContext) -> None:
    context.operations.execute(
        'ALTER TABLE swissvotes ALTER COLUMN procedure_number TYPE TEXT'
    )


@upgrade_task('Adds post-vote poll links')
def add_post_vote_poll_links(context: UpgradeContext) -> None:
    pass  # deleted later


@upgrade_task('Adds media fields')
def add_media_fields(context: UpgradeContext) -> None:
    columns = (
        ('media_ads_total', Integer()),
        ('media_ads_yea_p', Numeric(13, 10)),
        ('media_coverage_articles_total', Integer()),
        ('media_coverage_tonality_total', Integer()),
    )
    for column, type_ in columns:
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, type_))


@upgrade_task(
    'Add additional poster links',
    requires='onegov.swissvotes:Adds poster_yes and poster_no'
)
def add_additional_poster_links(context: UpgradeContext) -> None:
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


@upgrade_task(
    'Change media tonality types to numeric',
    requires='onegov.swissvotes:Adds media fields'
)
def change_media_tonality_types(context: UpgradeContext) -> None:
    context.operations.execute(
        'ALTER TABLE swissvotes '
        'ALTER COLUMN media_coverage_tonality_total TYPE NUMERIC(13, 10)'
    )


@upgrade_task('Adds die Mitte columns')
def add_die_mittel_columns(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'national_council_share_mitte'):
        context.operations.add_column(
            'swissvotes',
            Column('national_council_share_mitte', Numeric(13, 10))
        )


@upgrade_task('Adds brief description title column')
def add_brief_description_title(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'brief_description_title'):
        context.operations.add_column(
            'swissvotes',
            Column('brief_description_title', Text())
        )


@upgrade_task('Moves links to meta')
def move_links_to_meta(context: UpgradeContext) -> None:
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
def drop_unused_columns(context: UpgradeContext) -> None:
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
        'legislation_decade',
        'swissvoteslink',
        'votes_on_same_day',
        'result_people_yeas',
        'result_people_nays',
        'result_cantons_yeas_p',
        '_department_in_charge',
        'duration_post_federal_assembly',
        'duration_initative_federal_council',
        'duration_referendum_total',
        'signatures_invalid',
    )
    for column in columns:
        if context.has_column('swissvotes', column):
            context.operations.drop_column('swissvotes', column)


@upgrade_task('Rename national council share sps column')
def rename_national_council_share_sps_column(context: UpgradeContext) -> None:
    old = 'national_council_share_sp'
    new = 'national_council_share_sps'
    if (
        context.has_column('swissvotes', old)
        and not context.has_column('swissvotes', new)
    ):
        context.operations.alter_column('swissvotes', old, new_column_name=new)


@upgrade_task('Add more recommendation columns')
def add_more_recommendation_columns(context: UpgradeContext) -> None:
    for column in (
        'recommendations_other_counter_proposal',
        'recommendations_other_popular_initiative'
    ):
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, Text())
            )


@upgrade_task('Add campaign material meta column')
def add_campaign_material_meta_column(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'campaign_material_metadata'):
        context.operations.add_column(
            'swissvotes',
            Column('campaign_material_metadata', JSON())
        )


@upgrade_task('Add tsvector column for italian')
def add_tsvector_column_it(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'searchable_text_it_CH'):
        context.operations.add_column(
            'swissvotes', Column('searchable_text_it_CH', TSVECTOR())
        )


@upgrade_task('Add tsvector column for english')
def add_tsvector_column_en(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'searchable_text_en_US'):
        context.operations.add_column(
            'swissvotes', Column('searchable_text_en_US', TSVECTOR())
        )


@upgrade_task('Drops department in charge column')
def drop_departement_in_charge_columns(context: UpgradeContext) -> None:
    if context.has_column('swissvotes', 'department_in_charge'):
        context.operations.drop_column('swissvotes', 'department_in_charge')


@upgrade_task('Adds english short title column')
def add_english_short_title_column(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'short_title_en'):
        context.operations.add_column(
            'swissvotes', Column('short_title_en', Text())
        )


@upgrade_task('Adds parliamentary initiative')
def add_parliamentary_initiative(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'parliamentary_initiated'):
        context.operations.add_column(
            'swissvotes', Column('parliamentary_initiated', Integer())
        )


@upgrade_task('Adds meta to pages')
def add_meta_to_pages(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes_page', 'meta'):
        context.add_column_with_defaults(
            'swissvotes_page',
            Column('meta', JSON, nullable=False),
            default={}
        )


@upgrade_task('Adds french initiator and recommendations')
def add_french_initiator_and_recommendations(context: UpgradeContext) -> None:
    for old in (
        'initiator',
        'recommendations_other_yes',
        'recommendations_other_no',
        'recommendations_other_counter_proposal',
        'recommendations_other_popular_initiative',
        'recommendations_other_free',
    ):
        new = f'{old}_de'
        if (
            context.has_column('swissvotes', old)
            and not context.has_column('swissvotes', new)
        ):
            context.operations.alter_column(
                'swissvotes', old, new_column_name=new
            )

    for column in (
        'initiator_fr',
        'recommendations_other_yes_fr',
        'recommendations_other_no_fr',
        'recommendations_other_counter_proposal_fr',
        'recommendations_other_popular_initiative_fr',
        'recommendations_other_free_fr',
    ):
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes', Column(column, Text())
            )


@upgrade_task('Add campaign finances')
def add_campaign_finances(context: UpgradeContext) -> None:
    for position in ('yea', 'nay'):
        column = f'campaign_finances_{position}_total'
        if not context.has_column('swissvotes', column):
            context.operations.add_column(
                'swissvotes',
                Column(column, Integer)
            )


@upgrade_task('Rename file association keys')
def rename_file_associations_keys(context: UpgradeContext) -> None:
    old = 'file_id'
    for (table, new) in (
        ('files_for_swissvotes_files', 'swissvotefile_id'),
        ('files_for_swissvotes_page_files', 'translatablepagefile_id'),
    ):
        if (
            context.has_table(table)
            and context.has_column(table, old)
            and not context.has_column(table, new)
        ):
            context.operations.alter_column(table, old, new_column_name=new)


@upgrade_task('Add english bfs map')
def add_english_bfs_map(context: UpgradeContext) -> None:
    if not context.has_column('swissvotes', 'bfs_map_en'):
        context.operations.add_column(
            'swissvotes',
            Column('bfs_map_en', Text)
        )


@upgrade_task('Add bfs dashboard')
def add_bfs_dashboard(context: UpgradeContext) -> None:
    for locale in ('de', 'en', 'fr'):
        column = f'bfs_dashboard_{locale}'
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text))


@upgrade_task('Add poster columns basel 2')
def add_poster_columns_basel(context: UpgradeContext) -> None:
    for column in ('posters_bs_yea', 'posters_bs_nay'):
        if not context.has_column('swissvotes', column):
            context.operations.add_column('swissvotes', Column(column, Text))
