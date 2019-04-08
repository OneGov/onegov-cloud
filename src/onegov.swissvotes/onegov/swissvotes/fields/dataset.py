from dateutil.parser import parse
from decimal import Decimal
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import ColumnMapper
from onegov.swissvotes.models import SwissVote
from psycopg2.extras import NumericRange
from xlrd import open_workbook
from xlrd import XL_CELL_EMPTY
from xlrd import xldate


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
        missing = set(mapper.columns.values()) - set(headers)
        if missing:
            raise ValueError(_(
                "Some columns are missing: ${columns}.",
                mapping={'columns': ', '.join(missing)}
            ))

        for index in range(1, sheet.nrows):
            row = sheet.row(index)
            vote = SwissVote()
            for (
                attribute, column, type_, nullable, precision, scale
            ) in mapper.items():
                cell = row[headers.index(column)]
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
                            value = Decimal(
                                format(value, f'{precision}.{scale}f')
                            )

                except Exception:
                    errors.append((
                        index, column, f"'{value}' ≠ {type_.lower()}"
                    ))

                else:
                    if not nullable and value is None:
                        errors.append((index, column, "∅"))
                    mapper.set_value(vote, attribute, value)

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
