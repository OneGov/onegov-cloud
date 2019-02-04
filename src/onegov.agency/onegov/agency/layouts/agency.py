from cached_property import cached_property
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import AgencyMembershipMove
from onegov.agency.models import AgencyMove
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.org import _
from onegov.org.layout import AdjacencyListLayout
from onegov.org.layout import DefaultLayout


class MoveAgencyMixin(object):

    @cached_property
    def move_agency_url_template(self):
        return self.csrf_protected_url(
            self.request.link(AgencyMove.for_url_template())
        )


class AgencyCollectionLayout(DefaultLayout, MoveAgencyMixin):

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
                Link(
                    text=_("Create PDF"),
                    url=self.request.link(self.model, 'create-pdf'),
                    attrs={'class': 'create-pdf'}
                ),
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


class AgencyLayout(AdjacencyListLayout, MoveAgencyMixin):

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
                    text=_("Move"),
                    url=self.request.link(self.model.proxy(), 'move'),
                    attrs={'class': 'move'}
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
                            _("Delete agency"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                ),
                Link(
                    text=_("Create PDF"),
                    url=self.request.link(self.model.proxy(), 'create-pdf'),
                    attrs={'class': 'create-pdf'}
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
                LinkGroup(
                    title=_("Sort"),
                    links=[
                        Link(
                            text=_("Suborganizations"),
                            url=self.csrf_protected_url(
                                self.request.link(
                                    self.model.proxy(), 'sort-children'
                                )
                            ),
                            attrs={'class': 'sort-alphabetically'},
                            traits=(
                                Confirm(
                                    _(
                                        "Do you really want to sort the "
                                        "suborganizations alphabetically by "
                                        "title?"
                                    ),
                                    _("This cannot be undone."),
                                    _("Sort suborganizations"),
                                    _("Cancel")
                                ),
                                Intercooler(
                                    request_method='POST',
                                    redirect_after=self.request.link(
                                        self.model
                                    )
                                )
                            )
                        ),
                        Link(
                            text=_("Relationships"),
                            url=self.csrf_protected_url(
                                self.request.link(
                                    self.model.proxy(), 'sort-relationships'
                                )
                            ),
                            attrs={'class': 'sort-alphabetically'},
                            traits=(
                                Confirm(
                                    _(
                                        "Do you really want to sort the "
                                        "relationships alphabetically by "
                                        "last name and first name?"
                                    ),
                                    _("This cannot be undone."),
                                    _("Sort relationships"),
                                    _("Cancel")
                                ),
                                Intercooler(
                                    request_method='POST',
                                    redirect_after=self.request.link(
                                        self.model
                                    )
                                )
                            )
                        ),
                    ]
                ),
            ]

    @cached_property
    def move_membership_url_template(self):
        return self.csrf_protected_url(
            self.request.link(AgencyMembershipMove.for_url_template())
        )
