from cached_property import cached_property
from datetime import date
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
                    text=_("Campaign material"),
                    url=self.request.link(
                        self.model, name='manage-campaign-material'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Graphical campaign material for a Yes"),
                    url=self.request.link(
                        self.model, name='manage-campaign-material-yea'
                    ),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Graphical campaign material for a No"),
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

        result = {}
        for name, file in self.model.localized_files().items():
            result[name] = None
            attachment = self.model.get_file(name)
            if attachment:
                result[name] = self.request.link(
                    self.model,
                    file.static_views.get(
                        attachment.locale,
                        file.static_views['de_CH']
                    )
                )

        return result


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


class VoteCampaignMaterialLayout(VoteDetailLayout):

    date_month_format = 'MM.yyyy'
    date_year_format = 'yyyy'

    @cached_property
    def title(self):
        return _("Documents from the campaign")

    @cached_property
    def codes(self):
        return {
            key: self.model.codes(f'campaign_material_metadata_{key}')
            for key in ('position', 'language', 'doctype')
        }

    def format_code(self, metadata, key):
        values = metadata.get(key)
        if not values:
            return ''
        if isinstance(values, str):
            values = [values]
        codes = self.codes.get(key, {})
        return ', '.join((
            self.request.translate(codes.get(value, '')) for value in values
        ))

    def format_partial_date(self, metadata):
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

    def format_sortable_date(self, metadata):
        year = metadata.get('date_year')
        month = metadata.get('date_month') or 1
        day = metadata.get('date_day') or 1
        return date(year, month, day).strftime('%Y%m%d') if year else ''

    def metadata(self, filename):
        filename = filename.replace('.pdf', '')
        metadata = self.model.campaign_material_metadata.get(filename, {})
        if not metadata:
            return {}

        return {
            'title': metadata.get('title', '') or filename,
            'author': metadata.get('author', ''),
            'editor': metadata.get('editor', ''),
            'date': self.format_partial_date(metadata),
            'date_sortable': self.format_sortable_date(metadata),
            'position': self.format_code(metadata, 'position'),
            'language': self.format_code(metadata, 'language'),
            'doctype': self.format_code(metadata, 'doctype'),
        }


class UploadVoteAttachemtsLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Manage attachments")


class ManageCampaingMaterialLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Campaign material")


class ManageCampaingMaterialYeaLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Graphical campaign material for a Yes")


class ManageCampaingMaterialNayLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Graphical campaign material for a No")


class DeleteVoteLayout(VoteDetailLayout):

    @cached_property
    def title(self):
        return _("Delete vote")


class DeleteVoteAttachmentLayout(DefaultLayout):

    @cached_property
    def parent(self):
        return self.model.linked_swissvotes[0]

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.parent.short_title, self.request.link(self.parent)),
            Link(self.title, '#'),
        ]

    @cached_property
    def title(self):
        return _("Delete attachment")
