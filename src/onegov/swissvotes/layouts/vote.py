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
                    text=_("Campaign material for a Yes"),
                    url=self.request.link(
                        self.model, name='manage-campaign-material-yea'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Campaign material for a No"),
                    url=self.request.link(
                        self.model, name='manage-campaign-material-nay'
                    ),
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

    @cached_property
    def attachments(self):
        """ Returns a dictionary with static URLS for attachments.

        Note that not ony file / locale combinations with a file_name
        definition have a static URL!
        """

        return {
            name: (
                self.request.link(
                    self.model,
                    file.static_views.get(
                        self.request.locale,
                        file.static_views['de_CH']
                    )
                )
                if self.model.get_file(name) else None
            )
            for name, file in self.model.localized_files().items()
        }


class VoteDetailLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.model.short_title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class VoteStrengthsLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Voter strengths")


class UploadVoteAttachemtsLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Manage attachments")


class ManageCampaingMaterialYeaLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Campaign material for a Yes")


class ManageCampaingMaterialNayLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Campaign material for a No")


class DeleteVoteLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Delete vote")


class DeleteVoteAttachmentLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        model = self.model.linked_swissvotes[0]
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(model.short_title, self.request.link(model)),
            Link(self.title, '#'),
        ]

    @cached_property
    def title(self):
        return _("Delete attachment")
