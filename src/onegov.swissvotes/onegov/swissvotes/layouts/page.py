from cached_property import cached_property
from onegov.core.elements import Link
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
        return result

    @cached_property
    def breadcrumbs(self):
        if self.model.id == 'home':
            return [Link(_("Homepage"), self.homepage_url)]

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
