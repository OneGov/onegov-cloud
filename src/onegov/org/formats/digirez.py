from __future__ import annotations

import csv
import os.path
import subprocess
import tempfile

from onegov.core.csv import CSVFile


from typing import IO, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.csv import DefaultRow


class DigirezDB:
    """ Offers access to a Digirez Room Booking Software Database
    (see http://www.digiappz.com).

    Expects that mdbtools are installed (http://mdbtools.sourceforge.net).

    """

    csv_directory: tempfile.TemporaryDirectory[str] | None

    def __init__(self, accessdb_path: str) -> None:
        self.accessdb_path = accessdb_path
        self.csv_directory = None

    @property
    def tables(self) -> list[str]:
        output = subprocess.check_output(  # nosec:B603
            ('mdb-tables', self.accessdb_path))
        output_str = output.decode('utf-8').rstrip('\n ')

        return output_str.split(' ')

    @property
    def opened(self) -> bool:
        return self.csv_directory is not None

    @property
    def csv_path(self) -> str | None:
        return self.csv_directory.name if self.csv_directory else None

    def open(self) -> None:
        assert not self.opened
        self.csv_directory = tempfile.TemporaryDirectory()
        assert self.csv_path is not None

        for table in self.tables:
            output_path = os.path.join(self.csv_path, f'{table}.csv')

            with open(output_path, 'w') as output_file:
                subprocess.check_call(  # nosec:B603
                    args=(
                        'mdb-export', '-D', '%Y-%m-%dT%T',
                        self.accessdb_path, table
                    ),
                    stdout=output_file)

    @property
    def records(self) -> RecordsAccessor:
        assert self.opened and self.csv_path
        return RecordsAccessor(self.csv_path)


class RecordsAccessor:

    files: dict[str, IO[bytes]]

    def __init__(self, csv_path: str) -> None:
        self.csv_path = csv_path
        self.files = {}

    def get_file(self, name: str) -> IO[bytes]:
        if name not in self.files:
            path = os.path.join(self.csv_path, f'{name}.csv')
            self.files[name] = open(path, 'rb')  # noqa: SIM115

        return self.files[name]

    def __getattr__(self, name: str) -> Iterator[DefaultRow]:
        csv_file = CSVFile(
            self.get_file(name),
            expected_headers=None,
            dialect=csv.unix_dialect
        )

        return csv_file.lines
