""" The upload view. """
import transaction

from onegov.ballot import Vote
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_vote_default
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.formats import import_vote_wabsti
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.formats import import_vote_wabstim
from onegov.election_day.formats.common import BALLOT_TYPES
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.layouts import ManageVotesLayout
from onegov.election_day.views.upload import unsupported_year_error


@ElectionDayApp.manage_form(
    model=Vote,
    name='upload',
    template='upload_vote.pt',
    form=UploadVoteForm
)
def view_upload(self, request, form):

    """ Uploads votes results. """

    errors = []

    form.adjust(request.app.principal, self)

    status = 'open'
    map_available = True
    if form.submitted(request):
        session = request.session
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, False):
            errors = [unsupported_year_error(self.date.year)]
        else:
            map_available = principal.is_year_available(
                self.date.year, principal.use_maps
            )
            if form.file_format.data == 'internal':
                errors = import_vote_internal(
                    self,
                    principal,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype']
                )
            elif form.file_format.data == 'wabsti':
                errors = import_vote_wabsti(
                    self,
                    principal,
                    form.vote_number.data,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype']
                )
            elif form.file_format.data == 'wabsti_c':
                for source in self.data_sources:
                    errors.extend(
                        import_vote_wabstic(
                            self,
                            principal,
                            source.number,
                            source.district,
                            form.sg_geschaefte.raw_data[0].file,
                            form.sg_geschaefte.data['mimetype'],
                            form.sg_gemeinden.raw_data[0].file,
                            form.sg_gemeinden.data['mimetype']
                        )
                    )
            elif form.file_format.data == 'wabsti_m':
                errors = import_vote_wabstim(
                    self,
                    principal,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype']
                )
            elif form.file_format.data == 'default':
                ballot_types = ('proposal', )
                if self.type == 'complex':
                    ballot_types = BALLOT_TYPES

                for ballot_type in ballot_types:
                    field = getattr(form, ballot_type.replace('-', '_'))
                    errors.extend(
                        import_vote_default(
                            self,
                            principal,
                            ballot_type,
                            field.raw_data[0].file,
                            field.data['mimetype']
                        )
                    )
            else:
                raise NotImplementedError("Unsupported import format")
            archive = ArchivedResultCollection(session)
            archive.update(self, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            request.app.pages_cache.invalidate()
            request.app.send_zulip(
                request.app.principal.name,
                'New results available: [{}]({})'.format(
                    self.title, request.link(self)
                )
            )

    layout = ManageVotesLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'vote': self,
        'map_available': map_available
    }
