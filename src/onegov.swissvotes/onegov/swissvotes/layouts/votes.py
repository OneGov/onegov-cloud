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

        result = [
            (
                _("Update dataset"),
                self.request.link(self.model, name='update'),
                'upload-icon'
            ),
            (
                _("Download dataset (CSV)"),
                self.request.link(self.model, name='csv'),
                'export-icon'
            ),
            (
                _("Download dataset (XLSX)"),
                self.request.link(self.model, name='xlsx'),
                'export-icon'
            )
        ]
        if self.request.has_role('admin'):
            result.append((
                _("Delete all votes"),
                self.request.link(self.model, name='delete'),
                'delete-icon'
            ))
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (self.title, self.votes_link, 'current'),
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
            (self.title, '#', 'current'),
        ]


class DeleteVotesLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete all votes")

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, ''),
            (self.title, '#', 'current'),
        ]
