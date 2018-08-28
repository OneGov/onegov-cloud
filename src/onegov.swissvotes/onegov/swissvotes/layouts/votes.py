from cached_property import cached_property
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


class VotesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Votes")

    @cached_property
    def editbar_links(self):
        if not self.request.has_role('admin', 'editor'):
            return
        return [
            (
                _("Update dataset"),
                self.request.link(self.model, name='update'),
                'upload'
            ),
            (
                _("Download dataset"),
                self.request.link(self.model, name='csv'),
                'export-link'
            )
        ]

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, 'current'),
        ]


class UpdateVotesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Update dataset")

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, ''),
            (_("Update dataset"), '#', 'current'),
        ]
