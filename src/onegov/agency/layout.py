from cached_property import cached_property
from onegov.agency.collections import ExtendedAgencyCollection, \
    ExtendedPersonCollection
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMove
from onegov.agency.models.move import AgencyMembershipMoveWithinPerson
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.org import _
from onegov.org.layout import AdjacencyListLayout, PersonLayout, \
    PersonCollectionLayout

from onegov.org.layout import DefaultLayout as OrgDefaultLayout


class DefaultLayout(OrgDefaultLayout):
    pass


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
                Link(
                    text=_("Sort root agencies"),
                    url=self.request.link(self.model, 'sort'),
                    attrs={'class': 'sort'}
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

    def nav_item_url(self, agency):
        return self.request.link(agency.proxy(), 'as-nav-item')


class AgencyLayout(AdjacencyListLayout, MoveAgencyMixin):

    def include_editor(self):
        self.request.include('redactor')
        self.request.include('editor')

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
    def move_membership_within_agency_url_template(self):
        return self.csrf_protected_url(
            self.request.link(
                AgencyMembershipMoveWithinAgency.for_url_template())
        )


class AgencyPathMixin(object):

    def get_ancestors(
            self, item, with_item=True, levels=None, exclude_invisible=False):

        for ix, ancestor in enumerate(item.ancestors, 1):
            if not exclude_invisible:
                if not levels:
                    yield Link(ancestor.title, self.request.link(ancestor))
                elif ix in levels:
                    yield Link(ancestor.title, self.request.link(ancestor))

            elif self.request.is_visible(ancestor):
                if not levels:
                    yield Link(ancestor.title, self.request.link(ancestor))
                elif ix in levels:
                    yield Link(ancestor.title, self.request.link(ancestor))
        if with_item:
            if not exclude_invisible:
                yield Link(item.title, self.request.link(item))
            elif self.request.is_visible(item):
                yield Link(item.title, self.request.link(item))

    def agency_path(self, agency, sep=' > ', with_item=True, levels=None):
        return sep.join((
            ln.text for ln in self.get_ancestors(agency, with_item, levels)
        ))


class MembershipLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return AgencyLayout(self.model.agency, self.request).breadcrumbs + [
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this membership?"),
                            _("This cannot be undone."),
                            _("Delete membership"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.model.agency)
                        )
                    )
                )
            ]


class ExtendedPersonCollectionLayout(PersonCollectionLayout, AgencyPathMixin):

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Create Excel"),
                    url=self.request.link(
                        self.model, name='create-people-xlsx'),
                    attrs={'class': 'create-excel'}
                ),
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Person"),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-person'}
                        )
                    ]
                ),
            ]


class ExtendedPersonLayout(PersonLayout, AgencyPathMixin):

    @cached_property
    def collection(self):
        return ExtendedPersonCollection(self.request.session)

    @cached_property
    def move_membership_within_person_url_template(self):
        return self.csrf_protected_url(
            self.request.link(
                AgencyMembershipMoveWithinPerson.for_url_template())
        )


class AgencySearchLayout(DefaultLayout, AgencyPathMixin):
    pass
