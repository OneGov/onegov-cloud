from cached_property import cached_property
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


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


class EditPageLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Edit page")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class DeletePageLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete page")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class PageAttachmentsLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Manage attachments")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#'),
        ]


class DeletePageAttachmentLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Delete attachment")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.model.filename, self.request.link(self.model)),
            Link(self.title, '#'),
        ]
