from cached_property import cached_property
from onegov.core.elements import Link
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


class VoteLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.short_title

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_role('admin', 'editor'):
            result.append(
                Link(
                    text=_("Manage attachments"),
                    url=self.request.link(self.model, name='upload'),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Delete vote"),
                    url=self.request.link(self.model, name='delete'),
                    attrs={'class': 'delete-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.title, '#'),
        ]


class VoteStrengthsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Voter strengths")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class UploadVoteAttachemtsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Manage attachments")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class DeleteVoteLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete vote")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]
