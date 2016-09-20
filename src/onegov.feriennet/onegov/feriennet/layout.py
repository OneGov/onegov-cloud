import morepath

from cached_property import cached_property
from onegov.feriennet import _
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.security import ActivityOwnerPolicy
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout as BaseLayout


class DefaultLayout(BaseLayout):

    @morepath.reify
    def is_owner(self):
        return ActivityOwnerPolicy.for_layout(self).is_owner


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
