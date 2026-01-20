from __future__ import annotations

from collections import defaultdict
from fs import path
from fs.copy import copy_dir
from fs.copy import copy_file
from fs.errors import NoSysPath
from fs.osfs import OSFS
from fs.tempfs import TempFS
from fs.zipfs import WriteZipFS
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.utils import module_path
from onegov.election_day.formats import export_internal
from onegov.election_day.formats import export_parties_internal
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Vote
from sqlalchemy import desc


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Iterable
    from fs.subfs import FS
    from fs.subfs import SubFS
    from onegov.election_day import ElectionDayApp
    from typing import TypeVar
    from typing import TypeAlias

    Entity: TypeAlias = Election | ElectionCompound | Vote
    EntityT = TypeVar('EntityT', bound=Entity)


class ArchiveGenerator:
    """
    Iterates over all Votes, Election and ElectionCompounds and runs the
    csv export function on each of them.
    This creates a bunch of csv files, which are zipped and the path to
    the zip is returned.
    """
    archive_dir: SubFS[FS]

    def __init__(self, app: ElectionDayApp):
        assert app.filestorage is not None
        self.app = app
        self.session = app.session()
        self.archive_dir = app.filestorage.makedir('archive', recreate=True)
        self.temp_fs = TempFS()
        self.archive_parent_dir = 'zip'
        self.MAX_FILENAME_LENGTH = 60

    def generate_csv(self) -> None:
        """
        Creates csv files with a directory structure like this::

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

        votes = self.all_counted_votes_with_results()
        entities: Iterable[tuple[str, Collection[Entity]]] = [
            ('votes', votes),
            ('elections', self.all_counted_election_with_results()),
            ('elections', self.all_counted_election_compounds_with_results())
        ]

        for entity_name, entity in entities:

            grouped_by_year = self.group_by_year(entity)

            for yearly_package in grouped_by_year:
                year = str(yearly_package[0].date.year)
                year_dir = f'{entity_name}/{year}'
                self.temp_fs.makedirs(year_dir, recreate=True)
                for item in yearly_package:
                    self.export_item(item, year_dir)

        # Additionally, create 'flat csv' containing all votes in a single file
        if votes:
            filename = 'all_votes.csv'
            combined_path = path.combine('votes', filename)
            with self.temp_fs.open(combined_path, 'w') as f:
                votes_exports = self.get_all_rows_for_votes(votes)
                f.write(convert_list_of_dicts_to_csv(votes_exports))

    def get_all_rows_for_votes(
        self,
        votes: Collection[Vote]
    ) -> list[dict[str, Any]]:

        locales = sorted(self.app.locales)
        return [
            vote_record
            for vote in votes
            for vote_record in export_internal(vote, locales)
        ]

    def group_by_year(
        self,
        entities: Iterable[EntityT]
    ) -> list[list[EntityT]]:
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

    def zip_dir(self, base_dir: SubFS[FS]) -> str | None:
        """Recursively zips a directory (base_dir).

        :param base_dir: is a directory in a temporary file system.
            Contains subdirectories 'votes' and 'elections', as well as various
            other files to include.

        :returns path to the zipfile or None if base_dir doesn't exist
            or is empty.
        """
        self.archive_dir.makedir(self.archive_parent_dir, recreate=True)
        zip_path = f'{self.archive_parent_dir}/archive.zip'
        self.archive_dir.create(zip_path)

        with (
            self.archive_dir.open(zip_path, mode='wb') as file,
            WriteZipFS(file) as zip_filesystem  # type:ignore[arg-type]
        ):
            counts = base_dir.glob('**/*.csv').count()
            if counts.files != 0:
                if len(base_dir.listdir('/')) != 0:
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
        return None

    def all_counted_votes_with_results(self) -> list[Vote]:
        query = self.session.query(Vote).order_by(desc(Vote.date))
        return self.filter_by_final_results(query)

    def all_counted_election_with_results(self) -> list[Election]:
        query = self.session.query(Election).order_by(desc(Election.date))
        return self.filter_by_final_results(query)

    def all_counted_election_compounds_with_results(
        self
    ) -> list[ElectionCompound]:

        query = (
            self.session.query(ElectionCompound)
            .order_by(desc(ElectionCompound.date))
        )
        return self.filter_by_final_results(query)

    def filter_by_final_results(
        self,
        all_entities: Iterable[EntityT]
    ) -> list[EntityT]:

        return [
            entity
            for entity in all_entities
            if entity.counted and entity.has_results
        ]

    @property
    def archive_system_path(self) -> str | None:
        zip_path = f'{self.archive_parent_dir}/archive.zip'
        # syspath may not be available, depending on the actual filestorage
        try:
            sys_path = self.archive_dir.getsyspath(zip_path)
            return sys_path
        except NoSysPath:
            return None

    def include_docs(self) -> None:
        api = module_path('onegov.election_day', 'static/docs/api')
        native_fs = OSFS(api)

        for match in native_fs.glob('**/open_data*.md'):
            copy_file(
                src_fs=native_fs,
                src_path=match.path,
                dst_fs=self.temp_fs,
                dst_path=match.path,
            )

    def export_item(self, item: EntityT, dir: str) -> None:
        locales = sorted(self.app.locales)
        assert self.app.default_locale
        default_locale = self.app.default_locale

        # results
        filename = item.id[:self.MAX_FILENAME_LENGTH] + '.csv'
        combined_path = path.combine(dir, filename)
        rows = export_internal(item, locales)
        with self.temp_fs.open(combined_path, 'w') as f:
            f.write(convert_list_of_dicts_to_csv(rows))

        # party results
        if getattr(item, 'has_party_results', False):
            assert isinstance(item, (ProporzElection, ElectionCompound))
            filename = item.id[:self.MAX_FILENAME_LENGTH + 8] + '-parties.csv'
            combined_path = path.combine(dir, filename)
            rows = export_parties_internal(
                item,
                locales,
                default_locale=default_locale,
            )
            with self.temp_fs.open(combined_path, 'w') as f:
                f.write(convert_list_of_dicts_to_csv(rows))

    def generate_archive(self) -> str | None:
        self.generate_csv()
        self.include_docs()
        root = self.temp_fs.opendir('/')
        return self.zip_dir(root)
