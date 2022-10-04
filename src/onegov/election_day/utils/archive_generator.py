from onegov.core.utils import module_path
from onegov.ballot import Vote, Election, ElectionCompound
from onegov.core.csv import convert_list_of_dicts_to_csv
from sqlalchemy import desc
from collections import defaultdict
from fs import path
from fs.subfs import SubFS
from fs.copy import copy_dir
from fs.copy import copy_file
from fs.zipfs import WriteZipFS
from fs.tempfs import TempFS
from fs.osfs import OSFS


class ArchiveGenerator:
    def __init__(self, app):
        self.app = app
        self.session = self.app.session()
        self.archive_dir: SubFS = self.app.filestorage.makedir("archive",
                                                               recreate=True)
        self.temp_fs = TempFS()
        self.archive_parent_dir = "zip"
        self.MAX_FILENAME_LENGTH = 240

    def generate_csv(self):
        """
        Creates csv files with a directory structure like this:

        archive
        ├── elections
        │        └── 2022
        │             ├── election1.csv
        │             ├── election2.csv
        │             └── ...
        │
        └── votes
            ├── 2021
            │   └── vote1.csv
            └── 2022
                └── vote1.csv

        """

        names = ["votes", "elections", "elections"]
        entities = [
            self.all_votes(),
            self.all_elections(),
            self.all_election_compounds()
        ]
        for entity_name, entity in zip(names, entities):

            grouped_by_year = self.group_by_year(entity)

            for yearly_package in grouped_by_year:
                year = str(yearly_package[0].date.year)
                year_dir = f"{entity_name}/{year}"
                self.temp_fs.makedirs(year_dir, recreate=True)
                for item in yearly_package:
                    # item may be of type Vote, Election or ElectionCompound
                    filename = item.id[: self.MAX_FILENAME_LENGTH] + ".csv"
                    combined_path = path.combine(year_dir, filename)
                    with self.temp_fs.open(combined_path, "w") as f:
                        rows = item.export(sorted(self.app.locales))
                        f.write(convert_list_of_dicts_to_csv(rows))

    def group_by_year(self, entities):
        """Creates a list of lists, grouped by year.

        :param entities: Iterable of entities
        :type entities: list[Vote] | list[Election] | list[ElectionCompound]

        :returns: A nested list, where each sublist contains all from one year.

        For example:

            Given a list:
            votes = [vote_1, vote_2, vote_3, ...]

            We create a new  list:
            groups = [[vote_1, vote_2], [vote_3], ...]

            where vote_1.date.year == vote_2.date.year
        """
        groups = defaultdict(list)
        for entity in entities:
            groups[entity.date.year].append(entity)
        return list(groups.values())

    def zip_dir(self, base_dir: SubFS) -> str:
        """Recursively zips a directory (base_dir).

        :param base_dir: is a directory in a temporary file system.
        Contains subdirectories 'votes' and 'elections', as well as various
        other files to include.

        :returns path to the zipfile
        """
        self.archive_dir.makedir(self.archive_parent_dir, recreate=True)
        zip_path = f"{self.archive_parent_dir}/archive.zip"
        self.archive_dir.create(zip_path)

        with self.archive_dir.open(zip_path, mode="wb") as file:
            with WriteZipFS(file) as zip_filesystem:
                for entity in base_dir.listdir('/'):
                    if base_dir.isdir(entity):
                        copy_dir(
                            src_fs=base_dir,
                            src_path=entity,
                            dst_fs=zip_filesystem,
                            dst_path=entity,
                        )
                    if base_dir.isfile(entity):
                        copy_file(
                            src_fs=base_dir,
                            src_path=entity,
                            dst_fs=zip_filesystem,
                            dst_path=entity,
                        )
                return zip_path

    def all_votes(self):
        return self.session.query(Vote).order_by(desc(Vote.date)).all()

    def all_elections(self):
        return self.session.query(Election).order_by(desc(Election.date)).all()

    def all_election_compounds(self):
        return (
            self.session.query(ElectionCompound)
            .order_by(desc(ElectionCompound.date))
            .all()
        )

    @property
    def archive_system_path(self):
        zip_path = f"{self.archive_parent_dir}/archive.zip"
        return self.archive_dir.getsyspath(zip_path)

    def include_docs(self):
        api = module_path("onegov.election_day", "static/docs/api")
        native_fs = OSFS(api)

        for match in native_fs.glob("**/open_data*.md"):
            copy_file(
                src_fs=native_fs,
                src_path=match.path,
                dst_fs=self.temp_fs,
                dst_path=match.path,
            )

    def generate_archive(self):
        self.generate_csv()
        self.include_docs()
        root = self.temp_fs.opendir('/')
        return self.zip_dir(root)
