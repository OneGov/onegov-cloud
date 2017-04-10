import os

from onegov.ballot import Election, Vote
from onegov.election_day.formats.vote.wabsti import \
    import_exporter_files as import_vote
from onegov.election_day.formats.election.wabsti.majorz import \
    import_exporter_files as import_majorz
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
                log.warning(
                    'The vote {} is note configured properly'.format(vote.id)
                )
                continue

            fn_vs = os.path.join(folder, 'SGStatic_Geschaefte.csv')
            fn_es = os.path.join(folder, 'SGStatic_Gemeinden.csv')
            fn_e = os.path.join(folder, 'SG_Gemeinden.csv')
            files_exist = [
                os.path.exists(fn_vs),
                os.path.exists(fn_es),
                os.path.exists(fn_e)
            ]
            if not all(files_exist):
                if any(files_exist):
                    log.warning(
                        'Not all expected files present in {}'.format(folder)
                    )
                continue

            with open(fn_vs, 'rb') as f_vs, open(fn_es, 'rb') as f_es,  \
                    open(fn_e, 'rb') as f_e:

                entities = principal.entities.get(vote.date.year, {})
                results = import_vote(
                    vote, district, number, entities,
                    f_vs, 'text/plain',
                    f_es, 'text/plain',
                    f_e, 'text/plain'
                )

                errors = []
                for result in results.values():
                    errors.extend(result['errors'])

                yield errors

        for election in self.session.query(Election).filter_by(type='majorz'):
            if not (election.meta or {}).get('upload_type') == 'wabsti':
                continue

            principal = self.app.principal
            if not principal.is_year_available(election.date.year,
                                               map_required=False):
                log.warning(
                    'The year {} is not yet supported'.format(self.date.year)
                )
                continue

            district = election.meta.get('upload_wabsti_district')
            number = election.meta.get('upload_wabsti_number')
            folder = election.meta.get('upload_wabsti_folder', '')
            folder = os.path.join(self.dir, folder)
            if not district or not number or not os.path.exists(folder):
                log.warning(
                    'The election {} is note configured properly'.format(
                        election.id
                    )
                )
                continue

            fn_es = os.path.join(folder, 'WMStatic_Gemeinden.csv')
            fn_e = os.path.join(folder, 'WM_Gemeinden.csv')
            fn_c = os.path.join(folder, 'WM_Kandidaten.csv')
            fn_cr = os.path.join(folder, 'WM_KandidatenGde.csv')
            files_exist = [
                os.path.exists(fn_es),
                os.path.exists(fn_e),
                os.path.exists(fn_c),
                os.path.exists(fn_cr)
            ]
            if not all(files_exist):
                if any(files_exist):
                    log.warning(
                        'Not all expected files present in {}'.format(folder)
                    )
                continue

            with open(fn_es, 'rb') as f_es, open(fn_e, 'rb') as f_e, \
                    open(fn_c, 'rb') as f_c, open(fn_cr, 'rb') as f_cr:

                entities = principal.entities.get(election.date.year, {})
                results = import_majorz(
                    election, district, number, entities,
                    f_es, 'text/plain',
                    f_e, 'text/plain',
                    f_c, 'text/plain',
                    f_cr, 'text/plain'
                )

                yield results['errors']
