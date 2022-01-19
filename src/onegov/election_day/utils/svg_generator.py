from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
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
        """ Safely removes the given files from the directory. """
        if not files:
            return

        fs = self.app.filestorage
        for file in files:
            path = '{}/{}'.format(directory, file)
            if fs.exists(path) and not fs.isdir(path):
                fs.remove(path)

    def generate_svg(self, item, type_, filename, locale=None):
        """ Creates the requested SVG.

        Returns the number of created files.

        """

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
            path = '{}/{}'.format(self.svg_dir, filename)
            with self.app.filestorage.open(path, 'w') as f:
                copyfileobj(chart, f)
            log.info("{} created".format(filename))
            return 1

        return 0

    def create_svgs(self):
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
                'party-strengths', 'parties-panachage',
            ),
            'ballot': (
                'entities-map', 'districts-map'
            ) if principal.has_districts else ('entities-map')
        }

        # Read existing SVGs
        fs = self.app.filestorage
        if not fs.exists(self.svg_dir):
            fs.makedir(self.svg_dir)
        existing = fs.listdir(self.svg_dir)

        # Generate the SVGs
        created = 0
        filenames = []
        for election in self.session.query(Election):
            last_modified = election.last_modified
            for type_ in types[election.type]:
                filename = svg_filename(election, type_, None, last_modified)
                filenames.append(filename)
                if filename not in existing:
                    created += self.generate_svg(election, type_, filename)

        for compound in self.session.query(ElectionCompound):
            last_modified = compound.last_modified
            for type_ in types['compound']:
                filename = svg_filename(compound, type_, None, last_modified)
                filenames.append(filename)
                if filename not in existing:
                    created += self.generate_svg(compound, type_, filename)

        if principal.use_maps:
            for ballot in self.session.query(Ballot):
                if principal.is_year_available(ballot.vote.date.year):
                    for locale in self.app.locales:
                        last_modified = ballot.vote.last_modified
                        for type_ in types['ballot']:
                            filename = svg_filename(
                                ballot, type_, locale, last_modified
                            )
                            filenames.append(filename)
                            if filename not in existing:
                                created += self.generate_svg(
                                    ballot, type_, filename, locale
                                )

        # Delete obsolete SVGs
        obsolete = set(existing) - set(filenames)
        self.remove(self.svg_dir, obsolete)

        return created, len(obsolete)
