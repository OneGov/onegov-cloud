import os

from onegov.ballot import Vote
from onegov.election_day.formats.vote.wabsti import import_exporter
from onegov.election_day import log


class WabstiImporter():

    def __init__(self, app):
        self.app = app
        self.session = self.app.session()
        self.dir = app.configuration.get('wabsti_import_dir')
        assert self.dir

    def process(self):
        """ Tries to import all votes which defined the according fields
        for auto import. Returns the results as it is used in the web interface
        for each such vote.

        """

        if not os.path.exists(self.dir):
            return

        existing = os.listdir(self.dir)
        if not existing:
            return

        for vote in self.session.query(Vote):
            if not (vote.meta or {}).get('upload_type') == 'wabsti':
                continue

            principal = self.app.principal
            if not principal.is_year_available(vote.date.year,
                                               principal.use_maps):
                log.warning(
                    'The year {} is not yet supported'.format(self.date.year)
                )
                continue

            district = vote.meta.get('upload_wabsti_district')
            number = vote.meta.get('upload_wabsti_number')
            folder = vote.meta.get('upload_wabsti_folder', '')
            folder = os.path.join(self.dir, folder)
            if not district or not number or not os.path.exists(folder):
                log.warning('The vote is note configured properly')
                continue

            fn_vs = os.path.join(folder, 'SGStatic_Geschaefte.csv')
            fn_es = os.path.join(folder, 'SGStatic_Gemeinden.csv')
            fn_e = os.path.join(folder, 'SG_Gemeinden.csv')
            files_exist = (
                os.path.exists(fn_vs) and
                os.path.exists(fn_es) and
                os.path.exists(fn_e)
            )
            if not files_exist:
                continue

            with open(fn_vs, 'rb') as f_vs, open(fn_es, 'rb') as f_es,  \
                    open(fn_e, 'rb') as f_e:

                entities = principal.entities.get(vote.date.year, {})
                results = import_exporter(
                    vote, district, number, entities,
                    f_vs, 'text/plain',
                    f_es, 'text/plain',
                    f_e, 'text/plain'
                )

                errors = []
                for result in results.values():
                    errors.extend(result['errors'])

                yield errors
