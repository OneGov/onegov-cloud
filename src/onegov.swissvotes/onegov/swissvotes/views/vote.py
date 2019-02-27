from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.file.integration import render_depot_file
from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.forms import AttachmentsForm
from onegov.swissvotes.layouts import DeleteVoteLayout
from onegov.swissvotes.layouts import UploadVoteAttachemtsLayout
from onegov.swissvotes.layouts import VoteLayout
from onegov.swissvotes.layouts import VoteStrengthsLayout
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile


@SwissvotesApp.html(
    model=SwissVote,
    permission=Public,
    template='vote.pt'
)
def view_vote(self, request):
    query = request.session.query(SwissVote)
    prev = query.order_by(SwissVote.bfs_number.desc())
    prev = prev.filter(SwissVote.bfs_number < self.bfs_number).first()
    next = query.order_by(SwissVote.bfs_number.asc())
    next = next.filter(SwissVote.bfs_number > self.bfs_number).first()

    return {
        'layout': VoteLayout(self, request),
        'voting_text': self.get_file('voting_text'),
        'federal_council_message': self.get_file('federal_council_message'),
        'parliamentary_debate': self.get_file('parliamentary_debate'),
        'voting_booklet': self.get_file('voting_booklet'),
        'resolution': self.get_file('resolution'),
        'realization': self.get_file('realization'),
        'ad_analysis': self.get_file('ad_analysis'),
        'results_by_domain': self.get_file('results_by_domain'),
        'prev': prev,
        'next': next,
    }


@SwissvotesApp.json(
    model=SwissVote,
    permission=Public,
    name='percentages'
)
def view_vote_percentages(self, request):
    return {
        'results': [
            {'text': request.translate(text), 'value': value}
            for text, value in self.percentages.items() if value is not None
        ],
        'title': self.title
    }


@SwissvotesApp.html(
    model=SwissVote,
    permission=Public,
    template='strengths.pt',
    name='strengths'
)
def view_vote_strengths(self, request):
    return {
        'layout': VoteStrengthsLayout(self, request)
    }


@SwissvotesApp.form(
    model=SwissVote,
    permission=Private,
    form=AttachmentsForm,
    template='form.pt',
    name='upload'
)
def upload_vote_attachments(self, request, form):
    layout = UploadVoteAttachemtsLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Attachments updated"), 'success')
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'cancel': request.link(self)
    }


@SwissvotesApp.form(
    model=SwissVote,
    permission=Private,
    form=Form,
    template='form.pt',
    name='delete'
)
def delete_vote(self, request, form):
    layout = DeleteVoteLayout(self, request)

    if form.submitted(request):
        request.session.delete(self)
        request.message(_("Vote deleted"), 'success')
        return request.redirect(layout.votes_url)

    return {
        'layout': layout,
        'form': form,
        'subtitle': self.title,
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'button_text': _("Delete"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }


@SwissvotesApp.view(
    model=SwissVoteFile,
    render=render_depot_file,
    permission=Public
)
def view_file(self, request):
    @request.after
    def set_filename(response):
        bfs_number = self.linked_swissvotes[0].bfs_number
        name = self.name.split('-')[0]
        extension = {'results_by_domain': 'xlsx'}.get(name, 'pdf')
        title = {
            'voting_text': _("Voting text"),
            'realization': _("Realization"),
            'federal_council_message': _("Federal council message"),
            'parliamentary_debate': _("Parliamentary debate"),
            'voting_booklet': _("Voting booklet"),
            'ad_analysis': _("Analysis of the advertising campaign"),
            'resolution': _("Resolution"),
            'results_by_domain': _(
                "Result by canton, district and municipality"
            )
        }.get(name, '')
        title = normalize_for_url(request.translate(title))
        response.headers['Content-Disposition'] = (
            f'inline; filename={bfs_number}-{title}.{extension}'
        )

    return self.reference.file
