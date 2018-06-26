from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.core.utils import groupbylist
from onegov.election_day import log
from onegov.election_day.utils import svg_filename
from onegov.election_day.utils.d3_renderer import D3Renderer
from shutil import copyfileobj


class SvgGenerator():

    def __init__(self, app, renderer=None):
        self.app = app
        self.svg_dir = 'svg'
        self.session = self.app.session()
        self.renderer = renderer or D3Renderer(app)

    def remove(self, directory, files):
        """ Safely removes the given files from the directory. Allows to use
        wildcards.

        """
        if not files:
            return

        fs = self.app.filestorage
        for file in fs.filterdir(directory, files=files):
            path = '{}/{}'.format(directory, file.name)
            if fs.exists(path) and not file.is_dir:
                fs.remove(path)

    def generate_svg(self, item, type_, last_modified, locale=None):
        """ Creates the requested SVG. """

        if not self.app.filestorage.exists(self.svg_dir):
            self.app.filestorage.makedir(self.svg_dir)

        existing = self.app.filestorage.listdir(self.svg_dir)
        filename = svg_filename(
            item, type_, locale, last_modified=last_modified
        )

        if filename in existing:
            return None

        path = '{}/{}'.format(self.svg_dir, filename)
        if self.app.filestorage.exists(path):
            self.app.filestorage.remove(path)

        chart = None
        if type_ == 'candidates':
            chart = self.renderer.get_candidates_chart(item, 'svg')
        if type_ == 'connections':
            chart = self.renderer.get_connections_chart(item, 'svg')
        if type_ == 'lists':
            chart = self.renderer.get_lists_chart(item, 'svg')
        if type_ == 'lists-panachage':
            chart = self.renderer.get_lists_panachage_chart(item, 'svg')
        if type_ == 'party-strengths':
            chart = self.renderer.get_party_strengths_chart(item, 'svg')
        if type_ == 'parties-panachage':
            chart = self.renderer.get_parties_panachage_chart(item, 'svg')
        if type_ == 'entities-map':
            chart = self.renderer.get_entities_map(item, 'svg', locale)
        if type_ == 'districts-map':
            chart = self.renderer.get_districts_map(item, 'svg', locale)
        if chart:
            with self.app.filestorage.open(path, 'w') as f:
                copyfileobj(chart, f)
            log.info("{} created".format(filename))

    def create_svgs(self):
        """ Generates all SVGs for the given application.

        Only generates SVGs if not already generated since the last change of
        the election or vote.

        Optionally cleans up unused SVGs.

        """

        # Read existing SVGs
        fs = self.app.filestorage
        if not fs.exists(self.svg_dir):
            fs.makedir(self.svg_dir)

        # Generate the SVGs
        created = []
        principal = self.app.principal
        for election in self.session.query(Election):
            last_modified = election.last_modified
            created.append(
                svg_filename(election, '', '', last_modified=last_modified)
            )
            self.generate_svg(election, 'candidates', last_modified)
            if election.type == 'proporz':
                self.generate_svg(election, 'lists', last_modified)
                self.generate_svg(election, 'connections', last_modified)
                self.generate_svg(election, 'party-strengths', last_modified)
                self.generate_svg(election, 'parties-panachage', last_modified)
                self.generate_svg(election, 'lists-panachage', last_modified)
        for compound in self.session.query(ElectionCompound):
            last_modified = compound.last_modified
            created.append(
                svg_filename(compound, '', '', last_modified=last_modified)
            )
            self.generate_svg(compound, 'party-strengths', last_modified)
            self.generate_svg(compound, 'parties-panachage', last_modified)
        if principal.use_maps:
            for ballot in self.session.query(Ballot):
                last_modified = ballot.vote.last_modified
                created.append(
                    svg_filename(ballot, '', '', last_modified=last_modified)
                )
                if principal.is_year_available(ballot.vote.date.year):
                    for locale in self.app.locales:
                        self.generate_svg(
                            ballot, 'entities-map', last_modified, locale
                        )
                        if principal.has_districts:
                            self.generate_svg(
                                ballot, 'districts-map', last_modified, locale
                            )

        # Delete old SVGs
        existing = fs.listdir(self.svg_dir)
        existing = dict(groupbylist(
            sorted(existing),
            key=lambda a: a.split('.')[0]
        ))

        # ... orphaned files
        created = [name.split('.')[0] for name in created]
        diff = set(existing.keys()) - set(created)
        files = ['{}*'.format(file) for file in diff if file]
        self.remove(self.svg_dir, files)
        if '' in existing:
            self.remove(self.svg_dir, existing[''])

        # ... old files
        for files in existing.values():
            if len(files):
                files = sorted(files, reverse=True)
                try:
                    ts = str(int(files[0].split('.')[1]))
                except (IndexError, ValueError):
                    pass
                else:
                    files = [f for f in files if ts not in f]
                    self.remove(self.svg_dir, files)
