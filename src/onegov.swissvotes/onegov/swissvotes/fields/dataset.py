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
