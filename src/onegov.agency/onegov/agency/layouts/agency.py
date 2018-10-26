from cached_property import cached_property
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.org import _
from onegov.org.layout import AdjacencyListLayout
from onegov.org.layout import DefaultLayout
from onegov.org.new_elements import Confirm
from onegov.org.new_elements import Intercooler
from onegov.org.new_elements import Link
from onegov.org.new_elements import LinkGroup


class AgencyCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Agencies"), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Agency"),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-agency'}
                        )
                    ]
                ),
            ]


class AgencyLayout(AdjacencyListLayout):

    @cached_property
    def collection(self):
        return ExtendedAgencyCollection(self.request.session)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Agencies"), self.request.link(self.collection)),
        ] + list(self.get_breadcrumbs(self.model))[1:]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model.proxy(), 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Create PDF"),
                    url=self.request.link(self.model.proxy(), 'create-pdf'),
                    attrs={'class': 'create-pdf'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this agency?"),
                            _("This cannot be undone."),
                            _("Delete agency")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                ),
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Agency"),
                            url=self.request.link(
                                self.model.proxy(),
                                name='new'
                            ),
                            attrs={'class': 'new-agency'}
                        ),
                        Link(
                            text=_("Membership"),
                            url=self.request.link(
                                self.model.proxy(),
                                name='new-membership'
                            ),
                            attrs={'class': 'new-person'}
                        ),
                    ]
                ),
            ]
