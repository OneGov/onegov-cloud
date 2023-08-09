from functools import cached_property
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.utils import Bunch
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.layouts.default import DefaultLayout
from pathlib import Path


class PageLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.title

    @cached_property
    def editbar_links(self):
        result = []
        if self.request.has_role('admin', 'editor'):
            result.append(
                Link(
                    text=_("Edit page"),
                    url=self.request.link(self.model, name='edit'),
                    attrs={'class': 'edit-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Manage attachments"),
                    url=self.request.link(self.model, name='attachments'),
                    attrs={'class': 'upload-icon'}
                )
            )
            result.append(
                Link(
                    text=_("Manage slider images"),
                    url=self.request.link(self.model, name='slider-images'),
                    attrs={'class': 'upload-icon'}
                )
            )
            if self.model.id not in self.app.static_content_pages:
                result.append(
                    Link(
                        text=_("Delete page"),
                        url=self.request.link(self.model, name='delete'),
                        attrs={'class': 'delete-icon'}
                    )
                )
            result.append(
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Page"),
                            url=self.request.link(self.pages, name='add'),
                            attrs={'class': 'page-icon'}
                        )
                    ]
                ),
            )
        return result

    @cached_property
    def breadcrumbs(self):
        if self.model.id == 'home':
            return [Link(_("Homepage"), self.homepage_url)]

        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, '#'),
        ]

    def get_file_url(self, file):

        lang = file.locale.split('_')[0]

        if 'QUELLEN' in file.filename or 'REFERENCES' in file.filename:
            return self.request.link(
                self.model, name=f'kurzbeschreibung-{lang}.pdf')
        if 'CODEBOOK' in file.filename:
            return self.request.link(self.model, name=f'codebook-{lang}.pdf')
        if 'DATASET CSV' in file.filename:
            return self.request.link(self.model, name='swissvotes_dataset.csv')
        if 'DATASET XLSX' in file.filename:
            return self.request.link(
                self.model, name='swissvotes_dataset.xlsx')
        return self.request.link(file)

    @cached_property
    def slides(self):
        votes = SwissVoteCollection(self.app)
        result = []
        for image in self.model.slider_images:
            bfs_number = Path(image.filename).stem.split('-')[0]
            vote = votes.by_bfs_number(bfs_number)
            result.append(
                Bunch(
                    image=self.request.link(image),
                    label=vote.title if vote else image.filename,
                    url=self.request.link(vote) if vote else ''
                )
            )
        return result


class AddPageLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Add page")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, '#'),
        ]


class PageDetailLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class EditPageLayout(PageDetailLayout):

    @cached_property
    def title(self):
        return _("Edit page")


class DeletePageLayout(PageDetailLayout):

    @cached_property
    def title(self):
        return _("Delete page")


class ManagePageAttachmentsLayout(PageDetailLayout):

    @cached_property
    def title(self):
        return _("Manage attachments")


class ManagePageSliderImagesLayout(PageDetailLayout):

    @cached_property
    def title(self):
        return _("Manage slider images")


class DeletePageAttachmentLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete attachment")

    @cached_property
    def parent(self):
        return self.model.linked_swissvotes_page[0]

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.parent.title, self.request.link(self.parent)),
            Link(self.title, '#'),
        ]
