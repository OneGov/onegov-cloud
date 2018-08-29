from cached_property import cached_property
from onegov.swissvotes import _
from onegov.swissvotes.layouts.default import DefaultLayout


class PageLayout(DefaultLayout):

    @cached_property
    def title(self):
        return self.model.title

    @cached_property
    def editbar_links(self):
        if not self.request.has_role('admin', 'editor'):
            return
        return [
            (
                _("Edit page"),
                self.request.link(self.model, name='edit'),
                'edit-icon'
            )
        ]

    @cached_property
    def breadcrumbs(self):
        if self.model.id == 'home':
            return [(_("Homepage"), self.homepage_link, 'current')]

        return [
            (_("Homepage"), self.homepage_link, ''),
            (self.title, '#', 'current'),
        ]


class EditPageLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Edit page")

    @cached_property
    def breadcrumbs(self):
        return [
            (_("Homepage"), self.homepage_link, ''),
            (self.model.title, self.request.link(self.model), ''),
            (self.title, '#', 'current'),
        ]
