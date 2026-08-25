from __future__ import annotations

import os
import os.path

from collections import defaultdict
from glob import iglob
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.utils import module_path
from onegov.election_day.formats import export_internal
from onegov.election_day.formats import export_parties_internal
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Vote
from sqlalchemy import desc
from shutil import copy2, make_archive
from tempfile import TemporaryDirectory


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Iterable
    from onegov.core.filestorage import Filestorage
    from onegov.election_day import ElectionDayApp

    type Entity = Election | ElectionCompound | Vote


class ArchiveGenerator:
    """
    Iterates over all Votes, Election and ElectionCompounds and runs the
    csv export function on each of them.
    This creates a bunch of csv files, which are zipped and the path to
    the zip is returned.
    """
    archive_dir: Filestorage

    def __init__(self, app: ElectionDayApp):
        assert app.filestorage is not None
        self.app = app
        self.session = app.session()
        self.archive_dir = app.filestorage.makedir('archive', recreate=True)
        self.MAX_FILENAME_LENGTH = 60

    def generate_csv(self, temp_dir: str) -> bool:
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

        Returns whether or not any files have been written

        """

        result = False
        votes = self.all_counted_votes_with_results()
        entities: Iterable[tuple[str, Collection[Entity]]] = [
            ('votes', votes),
            ('elections', self.all_counted_election_with_results()),
            ('elections', self.all_counted_election_compounds_with_results())
        ]

        for entity_name, entity in entities:

            grouped_by_year = self.group_by_year(entity)

            for yearly_package in grouped_by_year:
                result = True
                year = str(yearly_package[0].date.year)
                year_dir = os.path.join(temp_dir, entity_name, year)
                os.makedirs(year_dir, exist_ok=True)
                for item in yearly_package:
                    self.export_item(item, year_dir)

        # Additionally, create 'flat csv' containing all votes in a single file
        if votes:
            result = True
            filename = 'all_votes.csv'
            votes_dir = os.path.join(temp_dir, 'votes')
            os.makedirs(votes_dir, exist_ok=True)
            combined_path = os.path.join(votes_dir, filename)
            with open(combined_path, 'w') as f:
                votes_exports = self.get_all_rows_for_votes(votes)
                f.write(convert_list_of_dicts_to_csv(votes_exports))

        return result

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

    def group_by_year[T: Entity](
        self,
        entities: Iterable[T]
    ) -> list[list[T]]:
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

    def zip_dir(self, temp_dir: str) -> str:
        """Recursively zips a directory (base_dir).

        :param base_dir: is a directory in a temporary file system.
            Contains subdirectories 'votes' and 'elections', as well as various
            other files to include.

        :returns path to the zipfile or None if base_dir doesn't exist
            or is empty.
        """
        self.archive_dir.makedir('zip', recreate=True)
        make_archive(
            self.archive_system_path.removesuffix('.zip'),
            'zip',
            temp_dir,
            '.'
        )
        return self.archive_path

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

    def filter_by_final_results[T: Entity](
        self,
        all_entities: Iterable[T]
    ) -> list[T]:

        return [
            entity
            for entity in all_entities
            if entity.counted and entity.has_results
        ]

    @property
    def archive_path(self) -> str:
        return 'zip/archive.zip'

    @property
    def archive_system_path(self) -> str:
        return self.archive_dir.getsyspath(self.archive_path)

    def include_docs(self, temp_dir: str) -> None:
        api = module_path('onegov.election_day', 'static/docs/api')
        for path in iglob('**/open_data*.md', root_dir=api, recursive=True):
            dst = os.path.join(temp_dir, path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            copy2(os.path.join(api, path), dst)

    def export_item(self, item: Entity, dir: str) -> None:
        locales = sorted(self.app.locales)
        assert self.app.default_locale
        default_locale = self.app.default_locale

        # results
        filename = item.id[:self.MAX_FILENAME_LENGTH] + '.csv'
        combined_path = os.path.join(dir, filename)
        rows = export_internal(item, locales)
        with open(combined_path, 'w') as f:
            f.write(convert_list_of_dicts_to_csv(rows))

        # party results
        if getattr(item, 'has_party_results', False):
            assert isinstance(item, (ProporzElection, ElectionCompound))
            filename = item.id[:self.MAX_FILENAME_LENGTH + 8] + '-parties.csv'
            combined_path = os.path.join(dir, filename)
            rows = export_parties_internal(
                item,
                locales,
                default_locale=default_locale,
            )
            with open(combined_path, 'w') as f:
                f.write(convert_list_of_dicts_to_csv(rows))

    def generate_archive(self) -> str | None:
        with TemporaryDirectory() as temp_dir:
            if not self.generate_csv(temp_dir):
                return None
            self.include_docs(temp_dir)
            return self.zip_dir(temp_dir)
