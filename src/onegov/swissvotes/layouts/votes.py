from cached_property import cached_property
from onegov.core.elements import Link
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


class VotesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Votes")

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_role('admin', 'editor'):
            result.append(
                Link(
                    text=_("Update dataset"),
                    url=self.request.link(self.model.default(), name='update'),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Download dataset (CSV)"),
                    url=self.request.link(self.model.default(), name='csv'),
                    attrs={'class': 'export-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Download dataset (XLSX)"),
                    url=self.request.link(self.model.default(), name='xlsx'),
                    attrs={'class': 'export-icon'}
                )
            )
        if self.request.has_role('admin'):
            result.append(
                Link(
                    text=_("Delete all votes"),
                    url=self.request.link(self.model.default(), name='delete'),
                    attrs={'class': 'delete-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.votes_url),
        ]


class UpdateVotesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Update dataset")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.title, '#'),
        ]


class DeleteVotesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete all votes")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.title, '#'),
        ]
