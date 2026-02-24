from __future__ import annotations

import os.path
from onegov.election_day import log
from onegov.election_day.models import Ballot
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.utils import svg_filename
from onegov.election_day.utils.d3_renderer import D3Renderer
from shutil import copyfileobj


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.election_day.app import ElectionDayApp


class SvgGenerator:

    def __init__(
        self,
        app: ElectionDayApp,
        renderer: D3Renderer | None = None
    ):
        self.app = app
        self.svg_dir = 'svg'
        self.session = self.app.session()
        self.renderer = renderer or D3Renderer(app)

    def remove(self, directory: str, files: Collection[str]) -> None:
        """ Safely removes the given files from the directory. """
        if not files:
            return

        fs = self.app.filestorage
        assert fs is not None

        for file in files:
            path = os.path.join(directory, file)
            if fs.exists(path) and not fs.isdir(path):
                fs.remove(path)

    def generate_svg(
        self,
        item: Election | ElectionCompound | ElectionCompoundPart | Ballot,
        type_: str,
        filename: str,
        locale: str
    ) -> int:
        """ Creates the requested SVG.

        Returns the number of created files.

        """

        assert item.session_manager is not None
        old_locale = item.session_manager.current_locale
        item.session_manager.current_locale = locale

        chart = None
        if type_ == 'candidates':
            chart = self.renderer.get_candidates_chart(item, 'svg')
        if type_ == 'connections':
            chart = self.renderer.get_connections_chart(item, 'svg')
        if type_ == 'list-groups':
            chart = self.renderer.get_list_groups_chart(item, 'svg')
        if type_ == 'lists':
            chart = self.renderer.get_lists_chart(item, 'svg')
        if type_ == 'lists-panachage':
            chart = self.renderer.get_lists_panachage_chart(item, 'svg')
        if type_ == 'seat-allocation':
            chart = self.renderer.get_seat_allocation_chart(item, 'svg')
        if type_ == 'party-strengths':
            chart = self.renderer.get_party_strengths_chart(item, 'svg')
        if type_ == 'parties-panachage':
            chart = self.renderer.get_parties_panachage_chart(item, 'svg')
        if type_ == 'entities-map':
            chart = self.renderer.get_entities_map(item, 'svg', locale)
        if type_ == 'districts-map':
            chart = self.renderer.get_districts_map(item, 'svg', locale)

        item.session_manager.current_locale = old_locale

        if chart:
            path = os.path.join(self.svg_dir, filename)
            fs = self.app.filestorage
            assert fs is not None
            with fs.open(path, 'w') as f:
                copyfileobj(chart, f)
            log.info(f'{filename} created')
            return 1

        return 0

    def create_svgs(self) -> tuple[int, int]:
        """ Generates all SVGs for the given application.

        Only generates SVGs if not already generated since the last change of
        the election, election compound or vote.

        Cleans up unused SVGs.

        """

        principal = self.app.principal
        types = {
            'majorz': (
                'candidates',
            ),
            'proporz': (
                'candidates', 'lists', 'connections', 'lists-panachage',
                'party-strengths', 'parties-panachage',
            ),
            'compound': (
                'seat-allocation', 'list-groups', 'party-strengths',
                'parties-panachage',
            ),
            'compound-part': (
                'party-strengths',
            ),
            'ballot': (
                'entities-map', 'districts-map'
            ) if principal.has_districts else ('entities-map',)
        }

        # Read existing SVGs
        fs = self.app.filestorage
        assert fs is not None
        if not fs.exists(self.svg_dir):
            fs.makedir(self.svg_dir)
        existing = set(fs.listdir(self.svg_dir))

        # Generate the SVGs
        created = 0
        filenames = set()
        for election in self.session.query(Election):
            assert election.type is not None

            last_modified = election.last_modified
            for locale in self.app.locales:
                for type_ in types[election.type]:
                    filename = svg_filename(
                        election, type_, locale, last_modified
                    )
                    filenames.add(filename)
                    if filename not in existing:
                        created += self.generate_svg(
                            election, type_, filename, locale
                        )

        for compound in self.session.query(ElectionCompound):
            last_modified = compound.last_modified
            for locale in self.app.locales:
                for type_ in types['compound']:
                    filename = svg_filename(
                        compound, type_, locale, last_modified
                    )
                    filenames.add(filename)
                    if filename not in existing:
                        created += self.generate_svg(
                            compound, type_, filename, locale
                        )
                for segment in principal.get_superregions(compound.date.year):
                    compound_part = ElectionCompoundPart(
                        compound, 'superregion', segment
                    )
                    for type_ in types['compound-part']:
                        filename = svg_filename(
                            compound_part, type_, locale, last_modified
                        )
                        filenames.add(filename)
                        if filename not in existing:
                            created += self.generate_svg(
                                compound_part, type_, filename, locale
                            )

        if principal.use_maps:
            for ballot in self.session.query(Ballot):
                if principal.is_year_available(ballot.vote.date.year):
                    last_modified = ballot.vote.last_modified
                    for locale in self.app.locales:
                        for type_ in types['ballot']:
                            filename = svg_filename(
                                ballot, type_, locale, last_modified
                            )
                            filenames.add(filename)
                            if filename not in existing:
                                created += self.generate_svg(
                                    ballot, type_, filename, locale
                                )

        # Delete obsolete SVGs
        obsolete = existing - filenames
        self.remove(self.svg_dir, obsolete)

        return created, len(obsolete)
