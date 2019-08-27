import csv
import os.path
import subprocess
import tempfile

from onegov.core.csv import CSVFile


class DigirezDB(object):
    """ Offers access to a Digirez Room Booking Software Database
    (see http://www.digiappz.com).

    Expects that mdbtools are installed (http://mdbtools.sourceforge.net).

    """

    def __init__(self, accessdb_path):
        self.accessdb_path = accessdb_path
        self.csv_directory = None

    @property
    def tables(self):
        output = subprocess.check_output(('mdb-tables', self.accessdb_path))
        output = output.decode('utf-8').rstrip('\n ')

        return output.split(' ')

    @property
    def opened(self):
        return self.csv_directory is not None

    @property
    def csv_path(self):
        return self.csv_directory and self.csv_directory.name

    def open(self):
        assert not self.opened
        self.csv_directory = tempfile.TemporaryDirectory()

        for table in self.tables:
            output_path = os.path.join(self.csv_path, '{}.csv'.format(table))

            with open(output_path, 'w') as output_file:
                subprocess.check_call(
                    args=(
                        'mdb-export', '-D', '%Y-%m-%dT%T',
                        self.accessdb_path, table
                    ),
                    stdout=output_file)

    @property
    def records(self):
        assert self.opened
        return RecordsAccessor(self.csv_path)


class RecordsAccessor(object):

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.files = {}

    def get_file(self, name):
        if name not in self.files:
            path = os.path.join(self.csv_path, '{}.csv'.format(name))
            self.files[name] = open(path, 'rb')

        return self.files[name]

    def __getattr__(self, name):
        csv_file = CSVFile(
            self.get_file(name),
            expected_headers=None,
            dialect=csv.unix_dialect
        )

        return csv_file.lines
