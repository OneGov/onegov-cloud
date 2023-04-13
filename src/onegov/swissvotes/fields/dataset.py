from dateutil.parser import parse
from decimal import Decimal
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import ColumnMapperDataset
from onegov.swissvotes.models import SwissVote
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel
from wtforms.validators import ValidationError


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
                (
                    'application/vnd.openxmlformats-officedocument'
                    '.spreadsheetml.sheet'
                ),
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

        super().post_validate(form, validation_stopped)
        if validation_stopped:
            return

        errors = []
        data = []
        mapper = ColumnMapperDataset()

        try:
            workbook = load_workbook(self.file, data_only=True)
        except Exception as exception:
            raise ValidationError(_("Not a valid XLSX file.")) from exception

        if len(workbook.worksheets) < 1:
            raise ValidationError(_("No data."))

        if 'DATA' not in workbook.sheetnames:
            raise ValidationError(_('Sheet DATA is missing.'))

        sheet = workbook['DATA']

        if sheet.max_row <= 1:
            raise ValidationError(_("No data."))

        headers = [column.value for column in next(sheet.rows)]
        missing = set(mapper.columns.values()) - set(headers)
        if missing:
            raise ValidationError(_(
                "Some columns are missing: ${columns}.",
                mapping={'columns': ', '.join(missing)}
            ))

        for index in range(2, sheet.max_row + 1):
            vote = SwissVote()
            all_columns_empty = True
            column_errors = []
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
                            raise ValidationError('Not a valid date format')
                    elif type_ == 'INTEGER':
                        if cell.data_type == 's':
                            value = cell.value
                            value = '' if value == '.' else value
                            value = int(value) if value else None
                        else:
                            value = int(cell.value)
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
                        column_errors.append((index, column, "∅"))
                    mapper.set_value(vote, attribute, value)

            if not all_columns_empty:
                errors.extend(column_errors)
                data.append(vote)

        if errors:
            raise ValidationError(_(
                "Some cells contain invalid values: ${errors}.",
                mapping={
                    'errors': '; '.join([
                        '{}:{} {}'.format(*error) for error in errors
                    ])
                }
            ))

        self.data = data
