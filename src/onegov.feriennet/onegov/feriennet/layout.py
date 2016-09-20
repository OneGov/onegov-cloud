from cached_property import cached_property
from onegov.feriennet import _
from onegov.feriennet.collections import VacationActivityCollection
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout as BaseLayout


class DefaultLayout(BaseLayout):

    @cached_property
    def is_owner(self):
        """ Returns true if the curent user owns the current model. """

        if not self.request.current_username:
            return False

        if not hasattr(self.model, 'username'):
            return False

        return self.request.current_username == self.model.username


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


class VacationActivityFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.include_editor()
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.link(self.model)),
            Link(_("New"), self.title)
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
        if self.request.is_admin or self.is_owner:
            return (
                Link(
                    text=_("Request Publication"),
                    url=self.request.link(self.model, name='einreichen'),
                    classes=('request-publication', )
                ),
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, name='bearbeiten'),
                    classes=('edit-link', )
                )
            )
