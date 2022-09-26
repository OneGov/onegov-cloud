from onegov.ballot import Vote, Election, ElectionCompound
from onegov.core.csv import convert_list_of_dicts_to_csv
from sqlalchemy import desc
from collections import defaultdict
from fs import path
from fs.subfs import SubFS
from fs.copy import copy_dir
from fs.zipfs import WriteZipFS
from onegov.election_day.utils.filenames import archive_filename


class ArchiveGenerator:
    def __init__(self, app):
        self.app = app
        self.session = self.app.session()
        self.archive_dir: SubFS = self.app.filestorage.makedir("archive",
                                                               recreate=True)
        self.archive_parent_dir = "zip"
        self.MAX_FILENAME_LENGTH = 240

    def generate_csv(self, subset=None):
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

        :param subset: Generate only votes or elections (Optional)
        :type subset: list of str

        :returns: The base directory
        :rtype: :class:`fs.subfs.SubFS`
        """

        names = ["votes", "elections", "elections"]
        entities = [
            self.all_votes(),
            self.all_elections(),
            self.all_election_compounds(),
        ]
        if subset:
            names = subset
            if set(subset) == {"votes"}:
                entities = [self.all_votes()]
            elif set(subset) == {"elections"}:
                entities = [self.all_elections()]
            else:
                raise ValueError(
                    f"Invalid argument: {subset}, "
                    f"Must be list ['votes', 'elections] or subset."
                )

        for entity_name, entity in zip(names, entities):

            grouped_by_year = self.group_by_year(entity)

            for yearly_package in grouped_by_year:
                year = str(yearly_package[0].date.year)
                year_dir = f"{entity_name}/{year}"
                self.archive_dir.makedirs(year_dir, recreate=True)
                for item in yearly_package:
                    # item may be of type Vote, Election or ElectionCompound
                    filename = item.id[: self.MAX_FILENAME_LENGTH] + ".csv"
                    combined_path = path.combine(year_dir, filename)
                    with self.archive_dir.open(combined_path, "w") as f:
                        rows = item.export(sorted(self.app.locales))
                        f.write(convert_list_of_dicts_to_csv(rows))

        return self.archive_dir

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

    def zip_dir(self, base_dir: SubFS) -> tuple[str, WriteZipFS]:
        """Recursively zips a directory (base_dir).

        :param base_dir: This is a directory in app.filestorage. Per default
        named "archive". Contains subdirectories 'votes' and 'elections'.

        :returns path to the zipfile and the zip filesystem itself
        """
        base_dir.makedir(self.archive_parent_dir)
        temp_path = f"{self.archive_parent_dir}/{archive_filename()}"
        base_dir.create(temp_path)
        with base_dir.open(temp_path, mode="wb") as file:
            with WriteZipFS(file) as zip_filesystem:
                for entity in ["votes", "elections"]:
                    if base_dir.isdir(entity):
                        copy_dir(
                            src_fs=base_dir,
                            src_path=entity,
                            dst_fs=zip_filesystem,
                            dst_path=entity,
                        )
                return temp_path, zip_filesystem

    def generate_votes_csv(self):
        return self.generate_csv(subset=["votes"])

    def generate_elections_csv(self):
        return self.generate_csv(subset=["elections"])

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
        zip_path = f"{self.archive_parent_dir}/{archive_filename()}"
        return self.archive_dir.getsyspath(zip_path)

    def generate_archive(self):
        self.archive_dir.removetree("/")  # clean up files from previous export
        archive_dir = self.generate_csv()
        temp_path, writable_zip_filesystem = self.zip_dir(archive_dir)
        return archive_dir, temp_path
