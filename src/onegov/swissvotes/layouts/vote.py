from __future__ import annotations

from functools import cached_property
from datetime import date
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.swissvotes.models import SwissVote
    from onegov.swissvotes.models import SwissVoteFile
    from onegov.swissvotes.request import SwissvotesRequest


class VoteLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: SwissVote

        def __init__(
            self,
            model: SwissVote,
            request: SwissvotesRequest
        ) -> None: ...

    @cached_property
    def title(self) -> str:
        return self.model.short_title

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        result: list[Link | LinkGroup] = []
        if self.request.has_role('admin', 'editor'):
            result.append(
                Link(
                    text=_('Manage attachments'),
                    url=self.request.link(self.model, name='upload'),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Campaign material'),
                    url=self.request.link(
                        self.model, name='manage-campaign-material'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Graphical campaign material for a Yes'),
                    url=self.request.link(
                        self.model, name='manage-campaign-material-yea'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Graphical campaign material for a No'),
                    url=self.request.link(
                        self.model, name='manage-campaign-material-nay'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Delete vote'),
                    url=self.request.link(self.model, name='delete'),
                    attrs={'class': 'delete-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Votes'), self.votes_url),
            Link(self.title, '#'),
        ]

    @cached_property
    def attachments(self) -> RenderData:
        """ Returns a dictionary with static URLS and locale for attachments.

        Note that only file / locale combinations with a file_name
        definition have a static URL!
        """

        result: RenderData = {}
        for name, file in self.model.localized_files().items():
            attachment = self.model.get_file(name)
            result[name] = {
                'url': self.request.link(
                    self.model,
                    file.static_views.get(
                        attachment.locale,
                        file.static_views['de_CH']
                    )
                ),
                'locale': attachment.locale
            } if attachment else {}

        return result

    @cached_property
    def search_results(
        self
    ) -> list[tuple[int, str, str, bool, SwissVoteFile]]:

        result = []
        metadata = self.model.campaign_material_metadata or {}
        labels = {
            name: file.label
            for name, file in self.model.localized_files().items()
        }
        codes = self.model.metadata_codes('language')
        for file in self.model.search():
            name = file.name.split('-')[0]
            protected = False
            if name in labels:
                order = 0
                title = self.request.translate(labels[name])
                language = self.request.translate(
                    _((file.language or '').capitalize())
                )
            elif name == 'campaign_material_other':
                data = metadata.get(file.filename.replace('.pdf', ''), {})
                order = 1
                title = data.get('title') or file.filename
                language = ', '.join([
                    self.request.translate(codes[lang])
                    for lang in data.get('language', [])
                    if lang in codes
                ])
                protected = 'article' in data.get('doctype', ['article'])
            else:
                order = 3
                title = file.filename
                language = ''
            result.append((order, title, language, protected, file))
        result.sort(key=lambda x: (x[0], (x[1] or '').lower()))
        return result


class VoteDetailLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: SwissVote

        def __init__(
            self,
            model: SwissVote,
            request: SwissvotesRequest
        ) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Votes'), self.votes_url),
            Link(self.model.short_title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class VoteStrengthsLayout(VoteDetailLayout):

    @cached_property
    def title(self) -> str:
        return _('Voter strengths')


class VoteCampaignMaterialLayout(VoteDetailLayout):

    date_month_format = 'MM.yyyy'
    date_year_format = 'yyyy'

    @cached_property
    def title(self) -> str:
        return _('Documents from the campaign')

    @cached_property
    def codes(self) -> dict[str, dict[str, str]]:
        return {
            key: self.model.metadata_codes(key)
            for key in ('position', 'language', 'doctype')
        }

    def format_code(self, metadata: dict[str, Any] | None, key: str) -> str:
        metadata = metadata or {}
        values = metadata.get(key)
        if not values:
            return ''

        if isinstance(values, str):
            values = [values]
        codes = self.codes.get(key, {})
        return ', '.join(
            self.request.translate(decoded)
            for value in values
            if (decoded := codes.get(value)) is not None
        )

    def format_partial_date(self, metadata: dict[str, Any] | None) -> str:
        metadata = metadata or {}
        year = metadata.get('date_year')
        month = metadata.get('date_month')
        day = metadata.get('date_day')
        if year and month and day:
            return self.format_date(date(year, month, day), 'date')
        if year and month:
            return self.format_date(date(year, month, 1), 'date_month')
        if year:
            return self.format_date(date(year, 1, 1), 'date_year')
        return ''

    def format_sortable_date(self, metadata: dict[str, Any] | None) -> str:
        metadata = metadata or {}
        year = metadata.get('date_year')
        month = metadata.get('date_month') or 1
        day = metadata.get('date_day') or 1
        return date(year, month, day).strftime('%Y%m%d') if year else ''

    def metadata(self, filename: str | None) -> dict[str, Any]:
        filename = (filename or '').removesuffix('.pdf')
        metadata = self.model.campaign_material_metadata or {}
        metadata = metadata.get(filename, {})
        if not metadata:
            return {}

        order = {v: i for i, v in enumerate(self.codes['position'])}
        return {
            'title': metadata.get('title', '') or filename,
            'author': metadata.get('author', ''),
            'editor': metadata.get('editor', ''),
            'date': self.format_partial_date(metadata),
            'date_sortable': self.format_sortable_date(metadata),
            'position': self.format_code(metadata, 'position'),
            'order': order.get(metadata.get('position', ''), 999),
            'language': self.format_code(metadata, 'language'),
            'doctype': self.format_code(metadata, 'doctype'),
            'protected': 'article' in metadata.get('doctype', [])
        }


class UploadVoteAttachemtsLayout(VoteDetailLayout):

    @cached_property
    def title(self) -> str:
        return _('Manage attachments')


class ManageCampaingMaterialLayout(VoteDetailLayout):

    @cached_property
    def title(self) -> str:
        return _('Campaign material')


class ManageCampaingMaterialYeaLayout(VoteDetailLayout):

    @cached_property
    def title(self) -> str:
        return _('Graphical campaign material for a Yes')


class ManageCampaingMaterialNayLayout(VoteDetailLayout):

    @cached_property
    def title(self) -> str:
        return _('Graphical campaign material for a No')


class DeleteVoteLayout(VoteDetailLayout):

    @cached_property
    def title(self) -> str:
        return _('Delete vote')


class DeleteVoteAttachmentLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: SwissVoteFile

        def __init__(
            self,
            model: SwissVoteFile,
            request: SwissvotesRequest
        ) -> None: ...

    @cached_property
    def parent(self) -> SwissVote:
        return self.model.linked_swissvotes[0]

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Votes'), self.votes_url),
            Link(self.parent.short_title, self.request.link(self.parent)),
            Link(self.title, '#'),
        ]

    @cached_property
    def title(self) -> str:
        return _('Delete attachment')
