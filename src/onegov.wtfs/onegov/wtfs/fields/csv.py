from onegov.core.csv import CSVFile
from onegov.core.errors import AmbiguousColumnsError
from onegov.core.errors import DuplicateColumnNamesError
from onegov.core.errors import EmptyFileError
from onegov.core.errors import EmptyLineInFileError
from onegov.core.errors import MissingColumnsError
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.wtfs import _


class CsvUploadField(UploadField):
    """ An upload field expecting CSV files. """

    def __init__(self, *args, **kwargs):
        self.encoding = kwargs.pop('encoding', None)
        self.dialect = kwargs.pop('dialect', None)
        self.expected_headers = kwargs.pop('expected_headers', None)
        self.rename_duplicate_column_names = kwargs.pop(
            'rename_duplicate_column_names', False
        )

        kwargs.setdefault('validators', [])
        kwargs['validators'].append(WhitelistedMimeType({'text/plain', }))
        kwargs['validators'].append(FileSizeLimit(10 * 1024 * 1024))

        kwargs.setdefault('render_kw', {})
        kwargs['render_kw']['force_simple'] = True

        super().__init__(*args, **kwargs)

    def post_validate(self, form, validation_stopped):
        super().post_validate(form, validation_stopped)
        if validation_stopped:
            return

        try:
            self.data = CSVFile(
                self.raw_data[0].file,
                encoding=self.encoding,
                dialect=self.dialect,
                expected_headers=self.expected_headers,
                rename_duplicate_column_names=(
                    self.rename_duplicate_column_names
                )
            )
            list(self.data.lines)
        except MissingColumnsError:
            raise ValueError(_("Some columns are missing."))
        except AmbiguousColumnsError:
            raise ValueError(_("Some column names are ambigous."))
        except DuplicateColumnNamesError:
            raise ValueError(_("Some column names appear twice."))
        except EmptyFileError:
            raise ValueError(_("The file is empty."))
        except EmptyLineInFileError:
            raise ValueError(_("The file contains an empty line."))
        except UnicodeDecodeError:
            raise ValueError(_("Invalid encoding."))
        except Exception:
            raise ValueError(_("Not a valid CSV file."))
