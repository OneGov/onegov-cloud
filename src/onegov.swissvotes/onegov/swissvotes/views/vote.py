from onegov.core.security import Private
from onegov.core.security import Public
from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.forms import AttachmentsForm
from onegov.swissvotes.layouts import DeleteVoteLayout
from onegov.swissvotes.layouts import UploadVoteAttachemtsLayout
from onegov.swissvotes.layouts import VoteLayout
from onegov.swissvotes.layouts import VoteStrengthsLayout
from onegov.swissvotes.models import SwissVote


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
