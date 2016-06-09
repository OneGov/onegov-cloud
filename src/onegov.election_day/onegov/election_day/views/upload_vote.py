""" The upload view. """
import transaction

from onegov.ballot import Vote
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.layout import ManageLayout
from onegov.election_day.models import Manage
from onegov.election_day.formats import FileImportError
from onegov.election_day.formats.vote import (
    BALLOT_TYPES, import_file as import_default_file
)
from onegov.election_day.formats.vote.onegov_ballot import (
    import_file as import_onegov_file
)


def get_form_class(vote, request):
    if not vote.ballots:
        return UploadVoteForm

    class LimitedUploadVoteForm(UploadVoteForm):
        pass

    if len(vote.ballots) == 1:
        LimitedUploadVoteForm.type.kwargs['default'] = 'simple'
        LimitedUploadVoteForm.type.kwargs['choices'] = [
            ('simple', _("Simple Vote"))
        ]
    else:
        LimitedUploadVoteForm.type.kwargs['default'] = 'complex'
        LimitedUploadVoteForm.type.kwargs['choices'] = [
            ('complex', _("Vote with Counter-Proposal"))
        ]

    return LimitedUploadVoteForm


@ElectionDayApp.form(model=Vote, name='upload', template='upload_vote.pt',
                     permission=Private, form=UploadVoteForm)
def view_upload(self, request, form):

    results = {}

    # if the vote already has results, do not give the user the choice to
    # switch between the different ballot types
    if self.counter_proposal:
        form.type.choices = form.type.choices[1:]
        form.type.data = 'complex'
    elif self.proposal:
        form.type.choices = form.type.choices[:1]
        form.type.data = 'simple'

    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year):
            results['proposal'] = {
                'status': 'error',
                'errors': [
                    FileImportError(
                        _(
                            "The year ${year} is not yet supported",
                            mapping={'year': self.date.year}
                        )
                    )
                ]
            }
        else:
            municipalities = principal.municipalities[self.date.year]
            if form.file_format.data == 'internal':
                results = import_onegov_file(
                    municipalities,
                    self,
                    form.proposal.raw_data[0].file,
                    form.proposal.data['mimetype']
                )
            else:
                if form.data['type'] == 'simple':
                    ballot_types = ('proposal', )
                else:
                    ballot_types = BALLOT_TYPES

                for ballot_type in ballot_types:
                    field = getattr(form, ballot_type.replace('-', '_'))

                    results[ballot_type] = import_default_file(
                        municipalities,
                        self,
                        ballot_type,
                        field.raw_data[0].file,
                        field.data['mimetype']
                    )

    if results:
        if all(r['status'] == 'ok' for r in results.values()):

            records = max(r['records'] for r in results.values())

            # make sure all imports have the same amount of records
            for result in results.values():
                if result['records'] < records:
                    result['status'] = 'error'
                    result['errors'].append(
                        FileImportError(
                            _("This ballot has fewer results than the others")
                        )
                    )
                    status = 'error'
                    break
            else:
                status = 'success'
        else:
            status = 'error'
    else:
        status = 'open'

    if status == 'error':
        transaction.abort()

    return {
        'layout': ManageLayout(self, request),
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Upload results"),
        'form': form,
        'cancel': request.link(Manage(request.app.session())),
        'results': results,
        'status': status,
        'vote': self
    }
