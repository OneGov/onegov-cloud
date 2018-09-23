from morepath.request import Response
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.forms import SearchForm
from onegov.swissvotes.forms import UpdateDatasetForm
from onegov.swissvotes.layouts import DeleteVotesLayout
from onegov.swissvotes.layouts import UpdateVotesLayout
from onegov.swissvotes.layouts import VotesLayout
from translationstring import TranslationString


@SwissvotesApp.form(
    model=SwissVoteCollection,
    permission=Public,
    form=SearchForm,
    template='votes.pt'
)
def view_votes(self, request, form):
    if not form.errors:
        form.apply_model(self)

    return {
        'layout': VotesLayout(self, request),
        'form': form
    }


@SwissvotesApp.form(
    model=SwissVoteCollection,
    permission=Private,
    form=UpdateDatasetForm,
    template='form.pt',
    name='update'
)
def update_votes(self, request, form):
    layout = UpdateVotesLayout(self, request)

    if form.submitted(request):
        added, updated = self.update(form.dataset.data)
        request.message(
            _(
                "Dataset updated (${added} added, ${updated} updated)",
                mapping={'added': added, 'updated': updated}
            ),
            'success'
        )

        # Warn if descriptor labels are missing
        missing = set()
        for vote in self.query():
            for policy_area in vote.policy_areas:
                missing |= set(
                    path for path in policy_area.label_path
                    if not isinstance(path, TranslationString)
                )
        if missing:
            request.message(
                _(
                    "The dataset contains unknown descriptors: ${items}.",
                    mapping={'items': ', '.join(sorted(missing))}
                ),
                'warning'
            )

        return request.redirect(layout.votes_link)

    return {
        'layout': layout,
        'form': form,
        'cancel': request.link(self)
    }


@SwissvotesApp.view(
    model=SwissVoteCollection,
    permission=Public,
    name='csv'
)
def export_votes_csv(self, request):
    response = Response(
        content_type='text/csv',
        content_disposition='inline; filename=dataset.csv'
    )
    self.export_csv(response.body_file)
    return response


@SwissvotesApp.view(
    model=SwissVoteCollection,
    permission=Public,
    name='xlsx'
)
def export_votes_xlsx(self, request):
    response = Response(
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename=dataset.xlsx'
    )
    self.export_xlsx(response.body_file)
    return response


@SwissvotesApp.form(
    model=SwissVoteCollection,
    permission=Secret,
    form=Form,
    template='form.pt',
    name='delete'
)
def delete_vote(self, request, form):
    layout = DeleteVotesLayout(self, request)

    if form.submitted(request):
        for vote in self.query():
            request.session.delete(vote)
        request.message(_("All votes deleted"), 'success')
        return request.redirect(layout.votes_link)

    return {
        'layout': layout,
        'form': form,
        'message': _("Do you really want to delete all votes?!"),
        'button_text': _("Delete all votes"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }
