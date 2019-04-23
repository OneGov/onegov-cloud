from dateutil.parser import parse
from onegov.wtfs import _
from onegov.wtfs.fields.csv import CsvUploadField


class MunicipalityDataUploadField(CsvUploadField):
    """ An upload field containg municipality data. """

    def __init__(self, *args, **kwargs):
        kwargs.pop('expected_headers', None)
        kwargs.pop('rename_duplicate_column_names', None)
        super().__init__(
            *args,
            **kwargs,
            expected_headers=[
                'Gemeinde-Nr.',
                'Vordefinierte Termine',
            ],
            rename_duplicate_column_names=True,
        )

    def post_validate(self, form, validation_stopped):
        super().post_validate(form, validation_stopped)
        if validation_stopped:
            return

        date_columns = [
            self.data.as_valid_identifier(name)
            for name in self.data.headers.keys() if 'definiert' in name
        ]

        errors = []
        data = {}
        for line in self.data.lines:
            try:
                bfs_number = int(line.gemeinde_nr_)
                dates = [getattr(line, column) for column in date_columns]
                dates = [parse(d, dayfirst=True).date() for d in dates if d]
            except (AssertionError, TypeError, ValueError):
                errors.append(line.rownumber)
            else:
                data[bfs_number] = {'dates': dates}

        if errors:
            raise ValueError(_(
                "Some rows contain invalid values: ${errors}.",
                mapping={'errors': ', '.join((str(e) for e in errors))}
            ))

        self.data = data
