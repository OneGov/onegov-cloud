""" The upload view. """
import transaction

from onegov.ballot import Vote
from onegov.core.security import Private
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_vote_default
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.formats import import_vote_wabsti
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.formats.common import BALLOT_TYPES
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.layout import ManageVotesLayout
from onegov.election_day.views.upload import unsupported_year_error


@ElectionDayApp.form(model=Vote, name='upload', template='upload_vote.pt',
                     permission=Private, form=UploadVoteForm)
def view_upload(self, request, form):

    errors = []

    form.adjust(request.app.principal, self)

    status = 'open'
    map_available = True
    if form.submitted(request):
        session = request.app.session()
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, False):
            errors = [unsupported_year_error(self.date.year)]
        else:
            map_available = principal.is_year_available(
                self.date.year, principal.use_maps
            )
            entities = principal.entities.get(self.date.year, [])
            if form.file_format.data == 'internal':
                errors = import_vote_internal(
                    entities,
                    self,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype']
                )
            elif form.file_format.data == 'wabsti':
                errors = import_vote_wabsti(
                    entities,
                    self,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype'],
                    form.vote_number.data,
                    form.data['type'] == 'complex'
                )
            elif form.file_format.data == 'wabsti_c':
                for source in self.data_sources:
                    errors.extend(
                        import_vote_wabstic(
                            self,
                            source.district,
                            source.number,
                            entities,
                            form.sg_geschaefte.raw_data[0].file,
                            form.sg_geschaefte.data['mimetype'],
                            form.sg_gemeinden.raw_data[0].file,
                            form.sg_gemeinden.data['mimetype']
                        )
                    )
            elif form.file_format.data == 'default':
                if form.data['type'] == 'simple':
                    ballot_types = ('proposal', )
                else:
                    ballot_types = BALLOT_TYPES

                for ballot_type in ballot_types:
                    field = getattr(form, ballot_type.replace('-', '_'))
                    errors.extend(
                        import_vote_default(
                            entities,
                            self,
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
            if form.file_format.data == 'default':
                if form.data['type'] == 'simple':
                    # Clear the unused ballots
                    if self.counter_proposal:
                        session.delete(self.counter_proposal)
                    if self.tie_breaker:
                        session.delete(self.counter_proposal)
            elif (
                form.file_format.data == 'internal' or
                form.file_format.data == 'wabsti_c'
            ):
                # It might be that the vote type setting stored in the meta
                # is overridden by the import (internal, wabsti c)
                if not self.meta:
                    self.meta = {}
                self.meta['vote_type'] = 'simple'
                if self.counter_proposal:
                    self.meta['vote_type'] = 'complex'

            status = 'success'
            request.app.pages_cache.invalidate()
            request.app.send_hipchat(
                request.app.principal.name,
                'New results available: <a href="{}">{}</a>'.format(
                    request.link(self), self.title
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
