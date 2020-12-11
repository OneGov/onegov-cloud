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

    @cached_property
    def attachments(self):
        """ Returns a dictionary with static URLS for attachments.

        Note that not all file / locale combinations have a static URL!
        """

        view_names = {
            'voting_text': 'abstimmungstext-<lang>.pdf',
            'brief_description': 'kurzbeschreibung.pdf',
            'federal_council_message': 'botschaft-<lang>.pdf',
            'parliamentary_debate': 'parlamentsberatung.pdf',
            'voting_booklet': 'brochure-<lang>.pdf',
            'resolution': 'erwahrung-<lang>.pdf',
            'realization': 'zustandekommen-<lang>.pdf',
            'ad_analysis': 'inserateanalyse.pdf',
            'results_by_domain': 'staatsebenen.xlsx',
            'foeg_analysis': 'medienanalyse.pdf',
            'post_vote_poll': 'nachbefragung-<lang>.pdf',
            'post_vote_poll_methodology': 'nachbefragung-methode-<lang>.pdf',
            'post_vote_poll_codebook': 'nachbefragung-codebuch-<lang>.pdf',
            'post_vote_poll_dataset': 'nachbefragung.csv',
            'preliminary_examination': 'vorpruefung-<lang>.pdf',
        }

        result = {}
        for name in view_names:
            attachment = self.model.get_file(name, self.request)
            if attachment:
                lang = attachment.name.split('-')[1].split('_')[0]
                lang = lang if lang in ('de', 'fr') else 'de'
                view_name = view_names[name].replace('<lang>', lang)
                result[name] = self.request.link(self.model, name=view_name)
            else:
                result[name] = None

        return result


class VoteStrengthsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Voter strengths")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Votes"), self.votes_url),
            Link(self.model.short_title, self.request.link(self.model)),
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
            Link(self.model.short_title, self.request.link(self.model)),
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
            Link(self.model.short_title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]
