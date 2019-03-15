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
from onegov.swissvotes.models import Actor
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

    bfs_map = self.bfs_map(request.locale)
    bfs_map_host = self.bfs_map_host(request.locale)
    if bfs_map_host:
        request.content_security_policy.default_src |= {bfs_map_host}

    return {
        'layout': VoteLayout(self, request),
        'brief_description': self.get_file('brief_description'),
        'voting_text': self.get_file('voting_text'),
        'federal_council_message': self.get_file('federal_council_message'),
        'parliamentary_debate': self.get_file('parliamentary_debate'),
        'voting_booklet': self.get_file('voting_booklet'),
        'resolution': self.get_file('resolution'),
        'realization': self.get_file('realization'),
        'ad_analysis': self.get_file('ad_analysis'),
        'results_by_domain': self.get_file('results_by_domain'),
        'bfs_map': bfs_map,
        'prev': prev,
        'next': next,
    }


@SwissvotesApp.json(
    model=SwissVote,
    permission=Public,
    name='percentages'
)
def view_vote_percentages(self, request):
    def create(text, text_label=None, percentage=None,
               yeas_p=None, nays_p=None, yeas=None, nays=None, code=None,
               yea_label=None, nay_label=None, none_label=None,
               empty=False):

        translate = request.translate
        result = {
            'text': translate(text),
            'text_label': translate(text_label) if text_label else '',
            'yea': 0.0,
            'nay': 0.0,
            'none': 0.0,
            'yea_label': '',
            'nay_label': '',
            'none_label': '',
            'empty': empty
        }

        if percentage is not None:
            yea = round(float(percentage), 1)
            nay = round(float(100 - percentage), 1)
            yea_label = yea_label or _("${x}% yea")
            nay_label = nay_label or _("${x}% nay")
            result.update({
                'yea': yea,
                'nay': nay,
                'yea_label': translate(_(yea_label, mapping={'x': yea})),
                'nay_label': translate(_(nay_label, mapping={'x': nay})),
            })

        elif yeas_p is not None and nays_p is not None:
            yea = round(float(yeas_p), 1)
            nay = round(float(nays_p), 1)
            none = round(float(100 - yeas_p - nays_p), 1)
            yea_label = yea_label or _("${x}% yea")
            nay_label = nay_label or _("${x}% nay")
            none_label = none_label or _("${x}% none")
            result.update({
                'yea': yea,
                'nay': nay,
                'none': none,
                'yea_label': translate(_(yea_label, mapping={'x': yea})),
                'nay_label': translate(_(nay_label, mapping={'x': nay})),
                'none_label': translate(_(none_label, mapping={'x': none}))
            })

        elif yeas is not None and nays is not None:
            yea = round(float(100 * (yeas / (yeas + nays))), 1)
            nay = round(float(100 * (nays / (yeas + nays))), 1)
            yea_label = yea_label or _("${x} yea")
            nay_label = nay_label or _("${x} nay")
            result.update({
                'yea': yea,
                'nay': nay,
                'yea_label': translate(_(yea_label, mapping={'x': yeas})),
                'nay_label': translate(_(nay_label, mapping={'x': nays})),
            })

        elif code is not None:
            value = getattr(self, f'_{code}')
            label = getattr(self, code)
            if value == 1:
                result.update({
                    'yea': True,
                    'yea_label': translate(label)
                })
            if value == 0 or value == 2:
                result.update({
                    'nay': True,
                    'nay_label': translate(label)
                })
            if value == 3:
                result.update({
                    'none': True,
                    'none_label': translate(label)
                })

        return result

    results = [
        create(
            _("People"),
            percentage=self.result_people_yeas_p,
            code='result_people_accepted'
        ),
        create(
            _("Cantons"),
            yeas=self.result_cantons_yeas,
            nays=self.result_cantons_nays,
            code='result_cantons_accepted'
        ),
        create("", empty=True),
        create(
            _("Federal Council"),
            text_label=_("Position of the Federal Council"),
            code='position_federal_council'
        ),
        create(
            _("National Council"),
            yeas=self.position_national_council_yeas,
            nays=self.position_national_council_nays,
            code='position_national_council'
        ),
        create(
            _("Council of States"),
            yeas=self.position_council_of_states_yeas,
            nays=self.position_council_of_states_nays,
            code='position_council_of_states'
        ),
        create(
            _("Party slogans"),
            text_label=_("Recommendations by political parties"),
            yeas_p=self.national_council_share_yeas,
            nays_p=self.national_council_share_nays,
            yea_label=_(
                "Electoral shares of parties: "
                "Parties recommending Yes ${x}%"
            ),
            nay_label=_(
                "Electoral shares of parties: "
                "Parties recommending No ${x}%"
            ),
            none_label=_(
                "Electoral shares of parties: neutral/unknown ${x}%"
            )
        )
    ]
    results = [
        result for result in results if any((
            result['yea'], result['nay'], result['none'], result['empty']
        ))
    ]

    return {
        'results': results,
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
        'layout': VoteStrengthsLayout(self, request),
        'Actor': Actor
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
            'brief_description': _("Brief description Swissvotes"),
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
