from dateutil.parser import parse
from decimal import Decimal
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import ColumnMapper
from onegov.swissvotes.models import SwissVote
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel
from psycopg2.extras import NumericRange


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
                'application/vnd.openxmlformats-officedocument',
                'spreadsheetml.sheet',
                'application/zip'
            })
        )
        kwargs['validators'].append(FileSizeLimit(10 * 1024 * 1024))

        kwargs.setdefault('render_kw', {})
        kwargs['render_kw']['force_simple'] = True

        super().__init__(*args, **kwargs)

    def post_validate(self, form, validation_stopped):
        """ Make sure the given XLSX is valid (all expected columns are
        present all cells contain reasonable values).

        Converts the XLSX to a list of SwissVote objects, available as
        ``data``.

        """

        super(SwissvoteDatasetField, self).post_validate(
            form,
            validation_stopped
        )
        if validation_stopped:
            return

        errors = []
        data = []
        mapper = ColumnMapper()

        try:
            workbook = load_workbook(self.raw_data[0].file, data_only=True)
        except Exception:
            raise ValueError(_("Not a valid XLSX file."))

        if len(workbook.worksheets) < 1:
            raise ValueError(_("No data."))

        if 'DATA' not in workbook.get_sheet_names():
            raise ValueError(_('Sheet DATA is missing.'))

        if 'CITATION' not in workbook.get_sheet_names():
            raise ValueError(_('Sheet CITATION is missing.'))

        sheet = workbook.get_sheet_by_name('DATA')

        if sheet.max_row <= 1:
            raise ValueError(_("No data."))

        headers = [column.value for column in tuple(sheet.rows)[0]]
        missing = set(mapper.columns.values()) - set(headers)
        if missing:
            raise ValueError(_(
                "Some columns are missing: ${columns}.",
                mapping={'columns': ', '.join(missing)}
            ))

        for index in range(2, sheet.max_row + 1):
            vote = SwissVote()
            all_columns_empty = True
            errors_of_empty_columns = []
            for (
                attribute, column, type_, nullable, precision, scale
            ) in mapper.items():
                cell = sheet.cell(index, headers.index(column) + 1)
                try:
                    if cell.value is None:
                        value = None
                    elif type_ == 'TEXT':
                        if (
                            cell.data_type == 'n'
                            and int(cell.value) == cell.value
                        ):
                            value = str(int(cell.value))
                        else:
                            value = str(cell.value)
                        value = '' if value == '.' else value
                    elif type_ == 'DATE':
                        if cell.data_type == 's':
                            value = parse(cell.value, dayfirst=True).date()
                        elif cell.data_type == 'n':
                            value = from_excel(cell.value).date()
                        elif cell.data_type == 'd':
                            value = cell.value.date()
                        else:
                            raise ValueError('Not a valid date format')
                    elif type_ == 'INTEGER':
                        if cell.data_type == 's':
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
                            value = Decimal(
                                format(value, f'{precision}.{scale}f')
                            )

                    all_columns_empty = all_columns_empty and value is None

                except Exception:
                    errors.append((
                        index, column, f"'{value}' ≠ {type_.lower()}"
                    ))

                else:
                    if not nullable and value is None:
                        errors_of_empty_columns.append((index, column, "∅"))
                    mapper.set_value(vote, attribute, value)

            if not all_columns_empty:
                errors.extend(errors_of_empty_columns)
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
