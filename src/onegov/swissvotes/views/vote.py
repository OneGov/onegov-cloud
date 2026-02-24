from __future__ import annotations

from morepath import redirect
from onegov.core.crypto import random_token
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.static import StaticFile
from onegov.core.utils import normalize_for_url
from onegov.file.integration import render_depot_file
from onegov.file.utils import as_fileintent
from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.forms import AttachmentsForm
from onegov.swissvotes.forms import AttachmentsSearchForm
from onegov.swissvotes.layouts import DeleteVoteAttachmentLayout
from onegov.swissvotes.layouts import DeleteVoteLayout
from onegov.swissvotes.layouts import ManageCampaingMaterialLayout
from onegov.swissvotes.layouts import ManageCampaingMaterialNayLayout
from onegov.swissvotes.layouts import ManageCampaingMaterialYeaLayout
from onegov.swissvotes.layouts import UploadVoteAttachemtsLayout
from onegov.swissvotes.layouts import VoteCampaignMaterialLayout
from onegov.swissvotes.layouts import VoteLayout
from onegov.swissvotes.layouts import VoteStrengthsLayout
from onegov.swissvotes.models import Actor
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from webob.exc import HTTPBadRequest
from webob.exc import HTTPNotFound
from webob.exc import HTTPUnsupportedMediaType


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal
    from depot.io.interfaces import StoredFile
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.swissvotes.request import SwissvotesRequest
    from webob import Response


@SwissvotesApp.form(
    model=SwissVote,
    permission=Public,
    template='vote.pt',
    form=AttachmentsSearchForm
)
def view_vote(
    self: SwissVote,
    request: SwissvotesRequest,
    form: AttachmentsSearchForm
) -> RenderData:

    layout = VoteLayout(self, request)
    query = request.session.query(SwissVote)
    prev_vote = (
        query.order_by(SwissVote.bfs_number.desc())
        .filter(SwissVote.bfs_number < self.bfs_number).first()
    )
    next_vote = (
        query.order_by(SwissVote.bfs_number.asc())
        .filter(SwissVote.bfs_number > self.bfs_number).first()
    )

    if self.bfs_map_host:
        request.content_security_policy.default_src |= {self.bfs_map_host}

    form.action += '#search'
    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'prev': prev_vote,
        'next': next_vote,
        'map_preview': request.link(StaticFile('images/map-preview.png')),
        'posters': self.posters(request),
        'form': form,
        'search_results': layout.search_results
    }


@SwissvotesApp.json(
    model=SwissVote,
    permission=Public,
    name='percentages'
)
def view_vote_percentages(
    self: SwissVote,
    request: SwissvotesRequest
) -> JSON_ro:

    def create(
        text: str,
        text_label: str | None = None,
        percentage: Decimal | None = None,
        yeas_p: Decimal | None = None,
        nays_p: Decimal | None = None,
        yeas: Decimal | int | None = None,
        nays: Decimal | int | None = None,
        code: str | None = None,
        yea_label: str | None = None,
        nay_label: str | None = None,
        none_label: str | None = None,
        empty: bool = False
    ) -> dict[str, JSON_ro]:

        translate = request.translate
        result: dict[str, JSON_ro] = {
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

        default_yea_label = _('${x}% yea')
        default_nay_label = _('${x}% nay')
        yea_label_no_perc = _('${x} yea')
        nay_label_no_per = _('${x} nay')
        if self._legal_form == 5:
            default_yea_label = _('${x}% for the popular initiative')
            default_nay_label = _('${x}% for the counter-proposal')
            yea_label_no_perc = _('${x} for the popular initiative')
            nay_label_no_per = _('${x} for the counter-proposal')

        if percentage is not None:
            yea = round(float(percentage), 1)
            nay = round(float(100 - percentage), 1)

            yea_label = yea_label or default_yea_label
            nay_label = nay_label or default_nay_label
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
            yea_label = yea_label or default_yea_label
            nay_label = nay_label or default_nay_label
            none_label = none_label or _('${x}% none')
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
            yea_label = yea_label or yea_label_no_perc
            nay_label = nay_label or nay_label_no_per
            result.update({
                'yea': yea,
                'nay': nay,
                'yea_label': translate(_(yea_label, mapping={'x': yeas})),
                'nay_label': translate(_(nay_label, mapping={'x': nays})),
            })

        elif code is not None:
            value = getattr(self, f'_{code}')
            label = getattr(self, code)
            if value in (1, 9):
                result.update({
                    'yea': True,
                    'yea_label': translate(label)
                })
            if value in (0, 2, 8):
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
            _('People'),
            percentage=self.result_people_yeas_p,
            code='result_people_accepted'
        ),
        create(
            _('Cantons'),
            yeas=self.result_cantons_yeas,
            nays=self.result_cantons_nays,
            code='result_cantons_accepted'
        ),
        create('', empty=True),
        create(
            _('Federal Council'),
            text_label=_('Position of the Federal Council'),
            code='position_federal_council'
        ),
        create(
            _('National Council'),
            yeas=self.position_national_council_yeas,
            nays=self.position_national_council_nays,
            code='position_national_council'
        ),
        create(
            _('Council of States'),
            yeas=self.position_council_of_states_yeas,
            nays=self.position_council_of_states_nays,
            code='position_council_of_states'
        ),
        create(
            _('Party slogans'),
            text_label=_('Recommendations by political parties'),
            yeas_p=self.national_council_share_yeas,
            nays_p=self.national_council_share_nays,
            yea_label=_(
                'Electoral shares of parties: '
                'Parties recommending Yes ${x}%'
            ) if self._legal_form != 5 else _(
                'Electoral shares of parties: '
                'Parties preferring the initiative ${x}%'
            ),
            nay_label=_(
                'Electoral shares of parties: '
                'Parties recommending No ${x}%'
            ) if self._legal_form != 5 else _(
                'Electoral shares of parties: '
                'Parties preferring the counter-proposal ${x}%'
            ),
            none_label=_(
                'Electoral shares of parties: neutral/unknown ${x}%'
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
def view_vote_strengths(
    self: SwissVote,
    request: SwissvotesRequest
) -> RenderData:
    return {
        'layout': VoteStrengthsLayout(self, request),
        'Actor': Actor
    }


@SwissvotesApp.html(
    model=SwissVote,
    permission=Public,
    template='campaign_material.pt',
    name='campaign-material'
)
def view_vote_campaign_material(
    self: SwissVote,
    request: SwissvotesRequest
) -> RenderData:

    layout = VoteCampaignMaterialLayout(self, request)
    files = sorted(
        (
            (file, layout.metadata(file.filename))
            for file in self.campaign_material_other
        ),
        key=lambda it: (it[1].get('order', 999), it[1].get('title', ''))
    )

    return {
        'layout': layout,
        'files': files
    }


@SwissvotesApp.form(
    model=SwissVote,
    permission=Private,
    form=AttachmentsForm,
    template='form.pt',
    name='upload'
)
def upload_vote_attachments(
    self: SwissVote,
    request: SwissvotesRequest,
    form: AttachmentsForm
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model(self)
        request.message(_('Attachments updated'), 'success')
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = UploadVoteAttachemtsLayout(self, request)
    return {
        'layout': layout,
        'form': form,
        'button_text': _('Upload'),
        'cancel': request.link(self)
    }


@SwissvotesApp.form(
    model=SwissVote,
    permission=Private,
    form=Form,
    template='form.pt',
    name='delete'
)
def delete_vote(
    self: SwissVote,
    request: SwissvotesRequest,
    form: Form
) -> RenderData | Response:

    layout = DeleteVoteLayout(self, request)

    if form.submitted(request):
        request.session.delete(self)
        request.message(_('Vote deleted'), 'success')
        return request.redirect(layout.votes_url)

    return {
        'layout': layout,
        'form': form,
        'subtitle': self.title,
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'button_text': _('Delete'),
        'button_class': 'alert',
        'cancel': request.link(self)
    }


@SwissvotesApp.view(
    model=SwissVoteFile,
    render=render_depot_file,
    permission=Public
)
def view_file(
    self: SwissVoteFile,
    request: SwissvotesRequest
) -> StoredFile:

    @request.after
    def set_filename(response: Response) -> None:
        attribute = SwissVote.localized_files().get(self.name.split('-')[0])
        if attribute:
            bfs_number = self.linked_swissvotes[0].bfs_number
            extension = attribute.extension
            title = normalize_for_url(request.translate(attribute.label))
            response.headers['Content-Disposition'] = (
                f'inline; filename={bfs_number}-{title}.{extension}'
            )

    return self.reference.file


def create_static_file_view(
    attribute: str,
    locale: str
) -> Callable[[SwissVote, SwissvotesRequest], Response]:

    def static_view(
        self: SwissVote,
        request: SwissvotesRequest
    ) -> Response:
        file = self.get_file(attribute, locale=locale, fallback=False)
        if not file:
            raise HTTPNotFound()
        return request.redirect(request.link(file))

    return static_view


for attribute_name, attribute in SwissVote.localized_files().items():
    for locale, view_name in attribute.static_views.items():
        SwissvotesApp.view(
            model=SwissVote,
            permission=Public,
            name=view_name
        )(create_static_file_view(attribute_name, locale))


@SwissvotesApp.html(
    model=SwissVote,
    template='attachments.pt',
    name='manage-campaign-material',
    permission=Private
)
def view_manage_campaign_material(
    self: SwissVote,
    request: SwissvotesRequest
) -> RenderData:

    layout = ManageCampaingMaterialLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'upload_url': layout.csrf_protected_url(
            request.link(self, name='upload-campaign-material')
        ),
        'files': self.campaign_material_other,
        'notice': self,
    }


@SwissvotesApp.view(
    model=SwissVote,
    name='upload-campaign-material',
    permission=Private,
    request_method='POST'
)
def upload_manage_campaign_material(
    self: SwissVote,
    request: SwissvotesRequest
) -> None:

    request.assert_valid_csrf_token()

    fs = request.params.get('file', '')
    if isinstance(fs, str):
        # malformed formdata
        raise HTTPBadRequest()

    attachment = SwissVoteFile(id=random_token())
    attachment.name = f'campaign_material_other-{fs.filename}'
    attachment.reference = as_fileintent(fs.file, fs.filename)

    if attachment.reference.content_type != 'application/pdf':
        raise HTTPUnsupportedMediaType()

    self.files.append(attachment)


@SwissvotesApp.html(
    model=SwissVote,
    template='attachments.pt',
    name='manage-campaign-material-yea',
    permission=Private
)
def view_manage_campaign_material_yea(
    self: SwissVote,
    request: SwissvotesRequest
) -> RenderData:

    layout = ManageCampaingMaterialYeaLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'upload_url': layout.csrf_protected_url(
            request.link(self, name='upload-campaign-material-yea')
        ),
        'files': self.campaign_material_yea,
        'notice': self,
    }


@SwissvotesApp.view(
    model=SwissVote,
    name='upload-campaign-material-yea',
    permission=Private,
    request_method='POST'
)
def upload_manage_campaign_material_yea(
    self: SwissVote,
    request: SwissvotesRequest
) -> None:

    request.assert_valid_csrf_token()

    fs = request.params.get('file', '')
    if isinstance(fs, str):
        # malformed formdata
        raise HTTPBadRequest()

    attachment = SwissVoteFile(id=random_token())
    attachment.name = f'campaign_material_yea-{fs.filename}'
    attachment.reference = as_fileintent(fs.file, fs.filename)

    if attachment.reference.content_type not in ('image/jpeg', 'image/png'):
        raise HTTPUnsupportedMediaType()

    self.files.append(attachment)


@SwissvotesApp.html(
    model=SwissVote,
    template='attachments.pt',
    name='manage-campaign-material-nay',
    permission=Private
)
def view_manage_campaign_material_nay(
    self: SwissVote,
    request: SwissvotesRequest
) -> RenderData:

    layout = ManageCampaingMaterialNayLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'upload_url': layout.csrf_protected_url(
            request.link(self, name='upload-campaign-material-nay')
        ),
        'files': self.campaign_material_nay,
        'notice': self,
    }


@SwissvotesApp.view(
    model=SwissVote,
    name='upload-campaign-material-nay',
    permission=Private,
    request_method='POST'
)
def upload_manage_campaign_material_nay(
    self: SwissVote,
    request: SwissvotesRequest
) -> None:

    request.assert_valid_csrf_token()

    fs = request.params.get('file', '')
    if isinstance(fs, str):
        # malformed formdata
        raise HTTPBadRequest()

    attachment = SwissVoteFile(id=random_token())
    attachment.name = f'campaign_material_nay-{fs.filename}'
    attachment.reference = as_fileintent(fs.file, fs.filename)

    if attachment.reference.content_type not in ('image/jpeg', 'image/png'):
        raise HTTPUnsupportedMediaType()

    self.files.append(attachment)


@SwissvotesApp.form(
    model=SwissVoteFile,
    name='delete',
    template='form.pt',
    permission=Private,
    form=Form
)
def delete_vote_attachment(
    self: SwissVoteFile,
    request: SwissvotesRequest,
    form: Form
) -> RenderData | Response:

    layout = DeleteVoteAttachmentLayout(self, request)
    name = 'manage-campaign-material'
    if 'yea' in self.name:
        name += '-yea'
    if 'nay' in self.name:
        name += '-nay'
    url = request.link(layout.parent, name)

    if form.submitted(request):
        request.session.delete(self)
        request.message(_('Attachment deleted.'), 'success')
        return redirect(url)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.filename}
        ),
        'layout': layout,
        'form': form,
        'title': self.filename,
        'subtitle': _('Delete'),
        'button_text': _('Delete'),
        'button_class': 'alert',
        'cancel': url
    }
