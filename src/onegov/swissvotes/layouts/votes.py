from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.collections import SwissVoteCollection
    from onegov.swissvotes.request import SwissvotesRequest


class VotesLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: SwissVoteCollection

        def __init__(
            self,
            model: SwissVoteCollection,
            request: SwissvotesRequest
        ) -> None: ...

    @cached_property
    def title(self) -> str:
        return _('Votes')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        result: list[Link | LinkGroup] = []
        if self.request.has_role('admin', 'editor'):
            result.append(
                Link(
                    text=_('Update dataset on the votes'),
                    url=self.request.link(self.model.default(), name='update'),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Update metadata on the campaign material'),
                    url=self.request.link(
                        self.model.default(), name='update-metadata'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Update external sources for images'),
                    url=self.request.link(
                        self.model.default(),
                        name='update-external-resources'
                    ),
                    attrs={'class': 'update-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Download dataset (CSV)'),
                    url=self.request.link(self.model.default(), name='csv'),
                    attrs={'class': 'export-icon'}
                )
            )
            result.append(
                Link(
                    text=_('Download dataset (XLSX)'),
                    url=self.request.link(self.model.default(), name='xlsx'),
                    attrs={'class': 'export-icon'}
                )
            )
        if self.request.has_role('admin'):
            result.append(
                Link(
                    text=_('Delete all votes'),
                    url=self.request.link(self.model.default(), name='delete'),
                    attrs={'class': 'delete-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, self.votes_url),
        ]


class VotesActionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        raise NotImplementedError()

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Votes'), self.votes_url),
            Link(self.title, '#'),
        ]


class UpdateVotesLayout(VotesActionLayout):

    @cached_property
    def title(self) -> str:
        return _('Update dataset on the votes')


class UpdateMetadataLayout(VotesActionLayout):

    @cached_property
    def title(self) -> str:
        return _('Update metadata on the campaign material')


class UpdateExternalResourcesLayout(VotesActionLayout):

    @cached_property
    def title(self) -> str:
        return _('Update external sources for images')


class DeleteVotesLayout(VotesActionLayout):

    @cached_property
    def title(self) -> str:
        return _('Delete all votes')
