from collections import OrderedDict
from dateutil.parser import parse
from decimal import Decimal
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import SwissVote
from psycopg2.extras import NumericRange
from xlrd import open_workbook
from xlrd import XL_CELL_EMPTY
from xlrd import xldate


COLUMNS = OrderedDict((
    ('bfs_number', 'anr'),
    ('date', 'datum'),
    ('legislation_number', 'legislatur'),
    ('legislation_decade', 'legisjahr'),
    ('decade', 'jahrzehnt'),
    ('title', 'titel'),
    ('keyword', 'stichwort'),
    ('votes_on_same_day', 'anzahl'),
    ('_legal_form', 'rechtsform'),
    ('descriptor_1_level_1', 'd1e1'),
    ('descriptor_1_level_2', 'd1e2'),
    ('descriptor_1_level_3', 'd1e3'),
    ('descriptor_2_level_1', 'd2e1'),
    ('descriptor_2_level_2', 'd2e2'),
    ('descriptor_2_level_3', 'd2e3'),
    ('descriptor_3_level_1', 'd3e1'),
    ('descriptor_3_level_2', 'd3e2'),
    ('descriptor_3_level_3', 'd3e3'),
    ('_result_people_accepted', 'volk'),
    ('_result_cantons_accepted', 'stand'),
    ('_result', 'annahme'),
    ('result_eligible_voters', 'berecht'),
    ('result_votes_total', 'stimmen'),
    ('result_turnout', 'bet'),
    ('result_votes_empty', 'leer'),
    ('result_votes_invalid', 'ungultig'),
    ('result_votes_valid', 'gultig'),
    ('result_people_yeas', 'volkja'),
    ('result_people_nays', 'volknein'),
    ('result_people_yeas_p', 'volkja-proz'),
    ('result_cantons_yeas', 'kt-ja'),
    ('result_cantons_nays', 'kt-nein'),
    ('result_cantons_yeas_p', 'ktjaproz'),
    ('result_zh_eligible_voters', 'zh-berecht'),
    ('result_zh_votes_total', 'zh-stimmen'),
    ('result_zh_turnout', 'zh-bet'),
    ('result_zh_votes_valid', 'zh-gultig'),
    ('result_zh_yeas', 'zh-ja'),
    ('result_zh_nays', 'zh-nein'),
    ('result_zh_yeas_p', 'zh-japroz'),
    ('_result_zh_accepted', 'zh-annahme'),
    ('result_be_eligible_voters', 'be-berecht'),
    ('result_be_votes_total', 'be-stimmen'),
    ('result_be_turnout', 'be-bet'),
    ('result_be_votes_valid', 'be-gultig'),
    ('result_be_yeas', 'be-ja'),
    ('result_be_nays', 'be-nein'),
    ('result_be_yeas_p', 'be-japroz'),
    ('_result_be_accepted', 'be-annahme'),
    ('result_lu_eligible_voters', 'lu-berecht'),
    ('result_lu_votes_total', 'lu-stimmen'),
    ('result_lu_turnout', 'lu-bet'),
    ('result_lu_votes_valid', 'lu-gultig'),
    ('result_lu_yeas', 'lu-ja'),
    ('result_lu_nays', 'lu-nein'),
    ('result_lu_yeas_p', 'lu-japroz'),
    ('_result_lu_accepted', 'lu-annahme'),
    ('result_ur_eligible_voters', 'ur-berecht'),
    ('result_ur_votes_total', 'ur-stimmen'),
    ('result_ur_turnout', 'ur-bet'),
    ('result_ur_votes_valid', 'ur-gultig'),
    ('result_ur_yeas', 'ur-ja'),
    ('result_ur_nays', 'ur-nein'),
    ('result_ur_yeas_p', 'ur-japroz'),
    ('_result_ur_accepted', 'ur-annahme'),
    ('result_sz_eligible_voters', 'sz-berecht'),
    ('result_sz_votes_total', 'sz-stimmen'),
    ('result_sz_turnout', 'sz-bet'),
    ('result_sz_votes_valid', 'sz-gultig'),
    ('result_sz_yeas', 'sz-ja'),
    ('result_sz_nays', 'sz-nein'),
    ('result_sz_yeas_p', 'sz-japroz'),
    ('_result_sz_accepted', 'sz-annahme'),
    ('result_ow_eligible_voters', 'ow-berecht'),
    ('result_ow_votes_total', 'ow-stimmen'),
    ('result_ow_turnout', 'ow-bet'),
    ('result_ow_votes_valid', 'ow-gultig'),
    ('result_ow_yeas', 'ow-ja'),
    ('result_ow_nays', 'ow-nein'),
    ('result_ow_yeas_p', 'ow-japroz'),
    ('_result_ow_accepted', 'ow-annahme'),
    ('result_nw_eligible_voters', 'nw-berecht'),
    ('result_nw_votes_total', 'nw-stimmen'),
    ('result_nw_turnout', 'nw-bet'),
    ('result_nw_votes_valid', 'nw-gultig'),
    ('result_nw_yeas', 'nw-ja'),
    ('result_nw_nays', 'nw-nein'),
    ('result_nw_yeas_p', 'nw-japroz'),
    ('_result_nw_accepted', 'nw-annahme'),
    ('result_gl_eligible_voters', 'gl-berecht'),
    ('result_gl_votes_total', 'gl-stimmen'),
    ('result_gl_turnout', 'gl-bet'),
    ('result_gl_votes_valid', 'gl-gultig'),
    ('result_gl_yeas', 'gl-ja'),
    ('result_gl_nays', 'gl-nein'),
    ('result_gl_yeas_p', 'gl-japroz'),
    ('_result_gl_accepted', 'gl-annahme'),
    ('result_zg_eligible_voters', 'zg-berecht'),
    ('result_zg_votes_total', 'zg-stimmen'),
    ('result_zg_turnout', 'zg-bet'),
    ('result_zg_votes_valid', 'zg-gultig'),
    ('result_zg_yeas', 'zg-ja'),
    ('result_zg_nays', 'zg-nein'),
    ('result_zg_yeas_p', 'zg-japroz'),
    ('_result_zg_accepted', 'zg-annahme'),
    ('result_fr_eligible_voters', 'fr-berecht'),
    ('result_fr_votes_total', 'fr-stimmen'),
    ('result_fr_turnout', 'fr-bet'),
    ('result_fr_votes_valid', 'fr-gultig'),
    ('result_fr_yeas', 'fr-ja'),
    ('result_fr_nays', 'fr-nein'),
    ('result_fr_yeas_p', 'fr-japroz'),
    ('_result_fr_accepted', 'fr-annahme'),
    ('result_so_eligible_voters', 'so-berecht'),
    ('result_so_votes_total', 'so-stimmen'),
    ('result_so_turnout', 'so-bet'),
    ('result_so_votes_valid', 'so-gultig'),
    ('result_so_yeas', 'so-ja'),
    ('result_so_nays', 'so-nein'),
    ('result_so_yeas_p', 'so-japroz'),
    ('_result_so_accepted', 'so-annahme'),
    ('result_bs_eligible_voters', 'bs-berecht'),
    ('result_bs_votes_total', 'bs-stimmen'),
    ('result_bs_turnout', 'bs-bet'),
    ('result_bs_votes_valid', 'bs-gultig'),
    ('result_bs_yeas', 'bs-ja'),
    ('result_bs_nays', 'bs-nein'),
    ('result_bs_yeas_p', 'bs-japroz'),
    ('_result_bs_accepted', 'bs-annahme'),
    ('result_bl_eligible_voters', 'bl-berecht'),
    ('result_bl_votes_total', 'bl-stimmen'),
    ('result_bl_turnout', 'bl-bet'),
    ('result_bl_votes_valid', 'bl-gultig'),
    ('result_bl_yeas', 'bl-ja'),
    ('result_bl_nays', 'bl-nein'),
    ('result_bl_yeas_p', 'bl-japroz'),
    ('_result_bl_accepted', 'bl-annahme'),
    ('result_sh_eligible_voters', 'sh-berecht'),
    ('result_sh_votes_total', 'sh-stimmen'),
    ('result_sh_turnout', 'sh-bet'),
    ('result_sh_votes_valid', 'sh-gultig'),
    ('result_sh_yeas', 'sh-ja'),
    ('result_sh_nays', 'sh-nein'),
    ('result_sh_yeas_p', 'sh-japroz'),
    ('_result_sh_accepted', 'sh-annahme'),
    ('result_ar_eligible_voters', 'ar-berecht'),
    ('result_ar_votes_total', 'ar-stimmen'),
    ('result_ar_turnout', 'ar-bet'),
    ('result_ar_votes_valid', 'ar-gultig'),
    ('result_ar_yeas', 'ar-ja'),
    ('result_ar_nays', 'ar-nein'),
    ('result_ar_yeas_p', 'ar-japroz'),
    ('_result_ar_accepted', 'ar-annahme'),
    ('result_ai_eligible_voters', 'ai-berecht'),
    ('result_ai_votes_total', 'ai-stimmen'),
    ('result_ai_turnout', 'ai-bet'),
    ('result_ai_votes_valid', 'ai-gultig'),
    ('result_ai_yeas', 'ai-ja'),
    ('result_ai_nays', 'ai-nein'),
    ('result_ai_yeas_p', 'ai-japroz'),
    ('_result_ai_accepted', 'ai-annahme'),
    ('result_sg_eligible_voters', 'sg-berecht'),
    ('result_sg_votes_total', 'sg-stimmen'),
    ('result_sg_turnout', 'sg-bet'),
    ('result_sg_votes_valid', 'sg-gultig'),
    ('result_sg_yeas', 'sg-ja'),
    ('result_sg_nays', 'sg-nein'),
    ('result_sg_yeas_p', 'sg-japroz'),
    ('_result_sg_accepted', 'sg-annahme'),
    ('result_gr_eligible_voters', 'gr-berecht'),
    ('result_gr_votes_total', 'gr-stimmen'),
    ('result_gr_turnout', 'gr-bet'),
    ('result_gr_votes_valid', 'gr-gultig'),
    ('result_gr_yeas', 'gr-ja'),
    ('result_gr_nays', 'gr-nein'),
    ('result_gr_yeas_p', 'gr-japroz'),
    ('_result_gr_accepted', 'gr-annahme'),
    ('result_ag_eligible_voters', 'ag-berecht'),
    ('result_ag_votes_total', 'ag-stimmen'),
    ('result_ag_turnout', 'ag-bet'),
    ('result_ag_votes_valid', 'ag-gultig'),
    ('result_ag_yeas', 'ag-ja'),
    ('result_ag_nays', 'ag-nein'),
    ('result_ag_yeas_p', 'ag-japroz'),
    ('_result_ag_accepted', 'ag-annahme'),
    ('result_tg_eligible_voters', 'tg-berecht'),
    ('result_tg_votes_total', 'tg-stimmen'),
    ('result_tg_turnout', 'tg-bet'),
    ('result_tg_votes_valid', 'tg-gultig'),
    ('result_tg_yeas', 'tg-ja'),
    ('result_tg_nays', 'tg-nein'),
    ('result_tg_yeas_p', 'tg-japroz'),
    ('_result_tg_accepted', 'tg-annahme'),
    ('result_ti_eligible_voters', 'ti-berecht'),
    ('result_ti_votes_total', 'ti-stimmen'),
    ('result_ti_turnout', 'ti-bet'),
    ('result_ti_votes_valid', 'ti-gultig'),
    ('result_ti_yeas', 'ti-ja'),
    ('result_ti_nays', 'ti-nein'),
    ('result_ti_yeas_p', 'ti-japroz'),
    ('_result_ti_accepted', 'ti-annahme'),
    ('result_vd_eligible_voters', 'vd-berecht'),
    ('result_vd_votes_total', 'vd-stimmen'),
    ('result_vd_turnout', 'vd-bet'),
    ('result_vd_votes_valid', 'vd-gultig'),
    ('result_vd_yeas', 'vd-ja'),
    ('result_vd_nays', 'vd-nein'),
    ('result_vd_yeas_p', 'vd-japroz'),
    ('_result_vd_accepted', 'vd-annahme'),
    ('result_vs_eligible_voters', 'vs-berecht'),
    ('result_vs_votes_total', 'vs-stimmen'),
    ('result_vs_turnout', 'vs-bet'),
    ('result_vs_votes_valid', 'vs-gultig'),
    ('result_vs_yeas', 'vs-ja'),
    ('result_vs_nays', 'vs-nein'),
    ('result_vs_yeas_p', 'vs-japroz'),
    ('_result_vs_accepted', 'vs-annahme'),
    ('result_ne_eligible_voters', 'ne-berecht'),
    ('result_ne_votes_total', 'ne-stimmen'),
    ('result_ne_turnout', 'ne-bet'),
    ('result_ne_votes_valid', 'ne-gultig'),
    ('result_ne_yeas', 'ne-ja'),
    ('result_ne_nays', 'ne-nein'),
    ('result_ne_yeas_p', 'ne-japroz'),
    ('_result_ne_accepted', 'ne-annahme'),
    ('result_ge_eligible_voters', 'ge-berecht'),
    ('result_ge_votes_total', 'ge-stimmen'),
    ('result_ge_turnout', 'ge-bet'),
    ('result_ge_votes_valid', 'ge-gultig'),
    ('result_ge_yeas', 'ge-ja'),
    ('result_ge_nays', 'ge-nein'),
    ('result_ge_yeas_p', 'ge-japroz'),
    ('_result_ge_accepted', 'ge-annahme'),
    ('result_ju_eligible_voters', 'ju-berecht'),
    ('result_ju_votes_total', 'ju-stimmen'),
    ('result_ju_turnout', 'ju-bet'),
    ('result_ju_votes_valid', 'ju-gultig'),
    ('result_ju_yeas', 'ju-ja'),
    ('result_ju_nays', 'ju-nein'),
    ('result_ju_yeas_p', 'ju-japroz'),
    ('_result_ju_accepted', 'ju-annahme'),
    ('_department_in_charge', 'dep'),
    ('procedure_number', 'gesch_nr'),
    ('_position_federal_council', 'br-pos'),
    ('_position_parliament', 'bv-pos'),
    ('_position_national_council', 'nr-pos'),
    ('position_national_council_yeas', 'nrja'),
    ('position_national_council_nays', 'nrnein'),
    ('_position_council_of_states', 'sr-pos'),
    ('position_council_of_states_yeas', 'srja'),
    ('position_council_of_states_nays', 'srnein'),
    ('duration_federal_assembly', 'dauer_bv'),
    ('duration_post_federal_assembly', 'dauer_abst'),
    ('duration_initative_collection', 'i-dauer_samm'),
    ('duration_initative_federal_council', 'i-dauer_br'),
    ('duration_initative_total', 'i-dauer_tot'),
    ('duration_referendum_collection', 'fr-dauer_samm'),
    ('duration_referendum_total', 'fr-dauer_tot'),
    ('signatures_valid', 'unter_g'),
    ('signatures_invalid', 'unter_u'),
    ('_recommendation_fdp', 'p-fdp'),
    ('_recommendation_cvp', 'p-cvp'),
    ('_recommendation_sps', 'p-sps'),
    ('_recommendation_svp', 'p-svp'),
    ('_recommendation_lps', 'p-lps'),
    ('_recommendation_ldu', 'p-ldu'),
    ('_recommendation_evp', 'p-evp'),
    ('_recommendation_csp', 'p-ucsp'),
    ('_recommendation_pda', 'p-pda'),
    ('_recommendation_poch', 'p-poch'),
    ('_recommendation_gps', 'p-gps'),
    ('_recommendation_sd', 'p-sd'),
    ('_recommendation_rep', 'p-rep'),
    ('_recommendation_edu', 'p-edu'),
    ('_recommendation_fps', 'p-fps'),
    ('_recommendation_lega', 'p-lega'),
    ('_recommendation_kvp', 'p-kvp'),
    ('_recommendation_glp', 'p-glp'),
    ('_recommendation_bdp', 'p-bdp'),
    ('_recommendation_mcg', 'p-mcg'),
    ('_recommendation_sav', 'zsa'),
    ('_recommendation_eco', 'eco'),
    ('_recommendation_sgv', 'sgv'),
    ('_recommendation_sbv_usp', 'sbv'),
    ('_recommendation_sgb', 'sgb'),
    ('_recommendation_travs', 'cng-travs'),
    ('_recommendation_vsa', 'vsa'),
    ('national_council_election_year', 'nr-wahl'),
    ('national_council_share_fdp', 'w-fdp'),
    ('national_council_share_cvp', 'w-cvp'),
    ('national_council_share_sp', 'w-sp'),
    ('national_council_share_svp', 'w-svp'),
    ('national_council_share_lps', 'w-lps'),
    ('national_council_share_ldu', 'w-ldu'),
    ('national_council_share_evp', 'w-evp'),
    ('national_council_share_csp', 'w-csp'),
    ('national_council_share_pda', 'w-pda'),
    ('national_council_share_poch', 'w-poch'),
    ('national_council_share_gps', 'w-gps'),
    ('national_council_share_sd', 'w-sd'),
    ('national_council_share_rep', 'w-rep'),
    ('national_council_share_edu', 'w-edu'),
    ('national_council_share_fps', 'w-fps'),
    ('national_council_share_lega', 'w-lega'),
    ('national_council_share_kvp', 'w-kvp'),
    ('national_council_share_glp', 'w-glp'),
    ('national_council_share_bdp', 'w-bdp'),
    ('national_council_share_mcg', 'w-mcg'),
    ('national_council_share_ubrige', 'w-ubrige'),
    ('national_council_share_yeas', 'ja-lager'),
    ('national_council_share_nays', 'nein-lager'),
    ('national_council_share_neutral', 'neutral'),
    ('national_council_share_vague', 'unbestimmt'),
    ('initiator', 'urheber'),
    ('anneepolitique', 'anneepolitique'),
))


class SwissvoteDatasetField(UploadField):
    """ An upload field expecting a Swissvotes dataset (XLSX). """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('validators', [])
        kwargs['validators'].append(
            WhitelistedMimeType({
                'application/excel',
                'application/octet-stream',
                'application/vnd.ms-excel',
                'application/vnd.ms-office',
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet',
                'application/zip'
            })
        )
        kwargs['validators'].append(FileSizeLimit(10 * 1024 * 1024))

        kwargs.setdefault('render_kw', {})
        kwargs['render_kw']['force_simple'] = True

        super().__init__(*args, **kwargs)

    def post_validate(self, form, validation_stopped):
        super(SwissvoteDatasetField, self).post_validate(
            form,
            validation_stopped
        )
        if validation_stopped:
            return

        errors = []
        data = []

        try:
            workbook = open_workbook(
                file_contents=self.raw_data[0].file.read()
            )
        except Exception:
            raise ValueError(_("Not a valid XLSX file."))

        if workbook.nsheets < 1:
            raise ValueError(_("No data."))

        sheet = workbook.sheet_by_index(0)

        if sheet.nrows <= 1:
            raise ValueError(_("No data."))

        headers = [column.value for column in sheet.row(0)]
        missing = set(COLUMNS.values()) - set(headers)
        if missing:
            raise ValueError(_(
                "Some columns are missing: ${columns}.",
                mapping={'columns': ', '.join(missing)}
            ))

        for index in range(1, sheet.nrows):
            row = sheet.row(index)
            vote = SwissVote()
            for attribute, column in COLUMNS.items():
                cell = row[headers.index(column)]
                table_column = vote.__table__.columns[attribute.lstrip('_')]
                type_ = str(table_column.type)
                nullable = table_column.nullable
                try:
                    if cell.ctype == XL_CELL_EMPTY:
                        value = None
                    elif type_ == 'TEXT':
                        value = str(cell.value)
                        value = '' if value == '.' else value
                    elif type_ == 'DATE':
                        if isinstance(cell.value, str):
                            value = parse(cell.value, dayfirst=True).date()
                        else:
                            value = xldate.xldate_as_datetime(
                                cell.value,
                                workbook.datemode
                            ).date()
                    elif type_ == 'INTEGER':
                        if isinstance(cell.value, str):
                            value = cell.value
                            value = '' if value == '.' else value
                            value = int(value) if value else None
                        else:
                            value = int(cell.value)
                    elif type_ == 'INT4RANGE':
                        value = NumericRange(*[
                            int(bound) for bound in cell.value.split('-')
                        ])
                    elif type_.startswith('NUMERIC'):
                        if isinstance(cell.value, str):
                            value = cell.value
                            value = '' if value == '.' else value
                            value = Decimal(str(value)) if value else None
                        else:
                            value = Decimal(str(cell.value))
                        if value is not None:
                            prec = table_column.type.precision
                            scale = table_column.type.scale
                            value = Decimal(format(value, f'{prec}.{scale}f'))

                except Exception:
                    errors.append((
                        index, column, f"'{value}' ≠ {type_.lower()}"
                    ))

                else:
                    if not nullable and value is None:
                        errors.append((index, column, "∅"))
                    setattr(vote, attribute, value)

            data.append(vote)

        if errors:
            raise ValueError(_(
                "Some cells contain invalid values: ${errors}.",
                mapping={
                    'errors': '; '.join([
                        '{}:{} {}'.format(*error) for error in errors
                    ])
                }
            ))

        self.data = data
