from cached_property import cached_property
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


class VoteLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.title

    @cached_property
    def editbar_links(self):
        if not self.request.has_role('admin', 'editor'):
            return
        return [
            (
                _("Manage attachments"),
                self.request.link(self.model, name='upload'),
                'upload-icon'
            ),
            (
                _("Delete vote"),
                self.request.link(self.model, name='delete'),
                'delete-icon'
            )
        ]

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, ''),
            (self.title, '#', 'current'),
        ]


class VoteStrengthsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Voter strengths")

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, ''),
            (self.model.title, self.request.link(self.model), ''),
            (self.title, '#', 'current'),
        ]


class UploadVoteAttachemtsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Manage attachments")

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, ''),
            (self.model.title, self.request.link(self.model), ''),
            (self.title, '#', 'current'),
        ]


class DeleteVoteLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete vote")

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (_("Votes"), self.votes_link, ''),
            (self.model.title, self.request.link(self.model), ''),
            (self.title, '#', 'current'),
        ]
