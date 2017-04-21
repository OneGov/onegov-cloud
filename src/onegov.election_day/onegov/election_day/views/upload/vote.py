""" The upload view. """
import transaction

from onegov.ballot import Vote
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.layout import ManageVotesLayout
from onegov.election_day.formats import FileImportError
from onegov.election_day.formats.vote import BALLOT_TYPES
from onegov.election_day.formats.vote.default import (
    import_file as import_default_file
)
from onegov.election_day.formats.vote.internal import (
    import_file as import_internal_file
)
from onegov.election_day.formats.vote.wabsti import (
    import_file as import_wabsti_file,
    import_exporter_files
)


@ElectionDayApp.form(model=Vote, name='upload', template='upload_vote.pt',
                     permission=Private, form=UploadVoteForm)
def view_upload(self, request, form):

    errors = []

    form.adjust(request.app.principal, self)

    status = 'open'
    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, principal.use_maps):
            errors = [
                FileImportError(
                    _(
                        "The year ${year} is not yet supported",
                        mapping={'year': self.date.year}
                    )
                )
            ]
        else:
            entities = principal.entities.get(self.date.year, [])
            if form.file_format.data == 'internal':
                errors = import_internal_file(
                    entities,
                    self,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype']
                )
            elif form.file_format.data == 'wabsti':
                errors = import_wabsti_file(
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
                        import_exporter_files(
                            self,
                            source.district,
                            source.number,
                            entities,
                            form.proposal.raw_data[0].file,
                            form.proposal.data['mimetype']
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
                        import_default_file(
                            entities,
                            self,
                            ballot_type,
                            field.raw_data[0].file,
                            field.data['mimetype']
                        )
                    )
            else:
                raise NotImplementedError("Unsupported import format")
            archive = ArchivedResultCollection(request.app.session())
            archive.update(self, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
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
        'vote': self
    }
