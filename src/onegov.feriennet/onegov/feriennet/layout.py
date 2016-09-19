from cached_property import cached_property
from onegov.feriennet import _
from onegov.feriennet.collections import VacationActivityCollection
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout


class VacationActivityCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.link(self.model))
        )

    @cached_property
    def editbar_links(self):
        if self.request.is_organiser:
            return (
                Link(
                    text=_("Submit Activity"),
                    url=self.request.link(self.model, name='neu'),
                    classes=('new-activity', )
                ),
            )


class NewVacationActivityLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.include_editor()

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.link(self.model)),
            Link(_("New"), '#')
        )

    @cached_property
    def editbar_links(self):
        return None


class EditVacationActivityLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.include_editor()

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title,
                 self.request.link(self.model, name='bearbeiten'))
        )

    @cached_property
    def editbar_links(self):
        return None


class VacationActivityLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model))
        )

    @cached_property
    def editbar_links(self):
        if self.request.is_admin or self.request.is_owner:
            return (
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, name='bearbeiten'),
                    classes=('edit-link', )
                ),
            )
