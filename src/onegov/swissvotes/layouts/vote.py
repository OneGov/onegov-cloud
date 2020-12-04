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

    @property
    def voto_static_url(self):
        if self.request.html_lang == 'fr-CH':
            return 'https://www.voto.swiss/fr/voto'
        return 'https://www.voto.swiss/voto'

    def get_file_url(self, name):

        mapping = {
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
            'preliminary_examination': 'vorpruefung-<lang>.pdf',
        }

        if name not in mapping:
            return None

        attachment = self.model.get_file(name, self.request)
        if not attachment:
            return None

        attachment_locale = attachment.name.split('-')[1]
        viewname = mapping[name].replace(
            '<lang>', attachment_locale.split('_')[0])

        return self.request.link(self.model, name=viewname)


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
