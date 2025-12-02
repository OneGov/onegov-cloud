from __future__ import annotations
import json

from functools import cached_property
from itertools import islice
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMembershipMoveWithinPerson
from onegov.agency.models import AgencyMove
from onegov.core.elements import Block
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.security import Private
from onegov.town6 import _
from onegov.town6.layout import AdjacencyListLayout
from onegov.town6.layout import DefaultLayout
from onegov.town6.layout import PageLayout as TownPageLayout
from onegov.town6.layout import PersonCollectionLayout
from onegov.town6.layout import PersonLayout as TownPersonLayout


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Iterator
    from collections.abc import Sequence
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.request import AgencyRequest
    from onegov.core.elements import Trait


class PageLayout(TownPageLayout):

    @cached_property
    def sidebar_links(self) -> None:  # type:ignore[override]
        return None


class PersonLayout(TownPersonLayout):
    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.has_model_permission(Private):
            traits: Sequence[Trait]
            if not self.model.deletable(self.request):
                traits = (
                    Block(
                        _("People with memberships can't be deleted"),
                        no=_('Cancel')
                    ),
                )
            else:
                traits = (
                    Confirm(
                        _('Do you really want to delete this person?'),
                        _('This cannot be undone.'),
                        _('Delete person'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.link(self.collection)
                    )
                )
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Sort'),
                    url=self.request.link(self.model, 'sort'),
                    attrs={'class': 'sort'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=traits
                )
            ]
        return None


class MoveAgencyMixin:

    if TYPE_CHECKING:
        request: AgencyRequest

        def csrf_protected_url(self, url: str) -> str: ...

    @cached_property
    def move_agency_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                AgencyMove,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )


class NavTreeMixin:

    if TYPE_CHECKING:
        model: Any
        request: AgencyRequest

    def nav_item_url(self, agency: ExtendedAgency) -> str:
        return self.request.link(agency.proxy(), 'as-nav-item')

    @cached_property
    def browsed_agency(self) -> ExtendedAgency | None:
        if (
            isinstance(self.model, ExtendedAgencyCollection)
            and self.model.browse
        ):
            return self.model.by_id(self.model.browse)  # type:ignore[arg-type]
        return None

    @cached_property
    def browsed_agency_parents(self) -> list[int]:
        return self.browsed_agency and [
            agency.id for agency in self.browsed_agency.ancestors
        ] or []

    def prerender_content(self, agency_id: int | str) -> bool:
        if not self.browsed_agency:
            return False
        agency_id = int(agency_id)
        return any((
            agency_id == self.browsed_agency.id,
            agency_id in self.browsed_agency_parents
        ))


class AgencyCollectionLayout(
    DefaultLayout,
    MoveAgencyMixin,
    NavTreeMixin
):

    request: AgencyRequest

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Agencies'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.has_model_permission(Private):
            return [
                Link(
                    text=_('Create PDF'),
                    url=self.request.link(self.model, 'create-pdf'),
                    attrs={'class': 'create-pdf'}
                ),
                Link(
                    text=_('Sort'),
                    url=self.request.link(self.model, 'sort'),
                    attrs={'class': 'sort'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Agency'),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-agency'}
                        )
                    ]
                ),
            ]
        return None


class AgencyLayout(
    AdjacencyListLayout,
    MoveAgencyMixin
):

    request: AgencyRequest

    def include_editor(self) -> None:
        self.request.include('redactor')
        self.request.include('editor')

    @cached_property
    def collection(self) -> ExtendedAgencyCollection:
        return ExtendedAgencyCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Agencies'), self.request.link(self.collection)),
            *islice(self.get_breadcrumbs(self.model), 1, None)
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.has_model_permission(Private):
            if self.model.deletable(self.request):
                def get_all_children_titles_json(
                        agency: ExtendedAgency) -> list[dict[str, Any]]:
                    return [
                        {
                            'title': child.title,
                            'children': get_all_children_titles_json(child)
                        }
                        for child in agency.children
                    ]

                children = json.dumps(get_all_children_titles_json(self.model))
                if children != '[]':
                    confirm_text = _('This cannot be undone. Following '
                        'agencies will be deleted as well:')
                else:
                    confirm_text = _('This cannot be undone.')

                delete_traits: Sequence[Trait] = (
                    Confirm(
                        _('Do you really want to delete this agency?'),
                        confirm_text,
                        _('Delete agency'),
                        _('Cancel'),
                        children,
                        _('Please scroll to the bottom to enable the confirm '
                          'button.')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.link(self.collection)
                    )
                )
            else:
                delete_traits = (
                    Block(
                        _(
                            "Agency with memberships or suborganizations "
                            "can't be deleted"
                        ),
                        no=_('Cancel')
                    ),
                )
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model.proxy(), 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Move'),
                    url=self.request.link(self.model.proxy(), 'move'),
                    attrs={'class': 'move'}
                ),
                Link(
                    text=_('Sort'),
                    url=self.request.link(self.model.proxy(), 'sort'),
                    attrs={'class': 'sort'}
                ),
                Link(
                    text=_('Change URL'),
                    url=self.request.link(self.model.proxy(), 'change-url'),
                    attrs={'class': 'change-url'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=delete_traits
                ),
                Link(
                    text=_('Create PDF'),
                    url=self.request.link(self.model.proxy(), 'create-pdf'),
                    attrs={'class': 'create-pdf'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Agency'),
                            url=self.request.link(
                                self.model.proxy(),
                                name='new'
                            ),
                            attrs={'class': 'new-agency'}
                        ),
                        Link(
                            text=_('Membership'),
                            url=self.request.link(
                                self.model.proxy(),
                                name='new-membership'
                            ),
                            attrs={'class': 'new-person'}
                        ),
                    ]
                ),
                LinkGroup(
                    title=_('Sort'),
                    links=[
                        Link(
                            text=_('Suborganizations'),
                            url=self.csrf_protected_url(
                                self.request.link(
                                    self.model.proxy(), 'sort-children'
                                )
                            ),
                            attrs={'class': 'sort-alphabetically'},
                            traits=(
                                Confirm(
                                    _(
                                        'Do you really want to sort the '
                                        'suborganizations alphabetically by '
                                        'title?'
                                    ),
                                    _('This cannot be undone.'),
                                    _('Sort suborganizations'),
                                    _('Cancel')
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
                            text=_('Relationships'),
                            url=self.csrf_protected_url(
                                self.request.link(
                                    self.model.proxy(), 'sort-relationships'
                                )
                            ),
                            attrs={'class': 'sort-alphabetically'},
                            traits=(
                                Confirm(
                                    _(
                                        'Do you really want to sort the '
                                        'relationships alphabetically by '
                                        'last name and first name?'
                                    ),
                                    _('This cannot be undone.'),
                                    _('Sort relationships'),
                                    _('Cancel')
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
        return None

    @cached_property
    def move_membership_within_agency_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                AgencyMembershipMoveWithinAgency,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )


class AgencyPathMixin:

    if TYPE_CHECKING:
        request: AgencyRequest

    def get_ancestors(
        self,
        item: ExtendedAgency,
        with_item: bool = True,
        levels: Collection[int] | None = None
    ) -> Iterator[Link]:

        for ix, ancestor in enumerate(item.ancestors, 1):
            if levels is None or ix in levels:
                yield Link(ancestor.title, self.request.link(ancestor))

        if with_item:
            yield Link(item.title, self.request.link(item))

    def parent_path(self, agency: ExtendedAgency) -> str:
        levels = self.request.app.org.agency_display_levels
        return ' > '.join(
            ln.text or ln.title
            for ln in self.get_ancestors(agency, False, levels)
        )

    def agency_path(self, agency: ExtendedAgency) -> str:
        return ' > '.join(
            ln.text or ln.title
            for ln in self.get_ancestors(agency)
        )


class MembershipLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            *AgencyLayout(self.model.agency, self.request).breadcrumbs,
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.has_model_permission(Private):
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this membership?'),
                            _('This cannot be undone.'),
                            _('Delete membership'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.model.agency)
                        )
                    )
                )
            ]
        return None


class ExtendedPersonCollectionLayout(
    PersonCollectionLayout,
    AgencyPathMixin
):

    request: AgencyRequest

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Create Excel'),
                    url=self.request.link(
                        self.model, name='create-people-xlsx'),
                    attrs={'class': 'create-excel'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Person'),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-person'}
                        )
                    ]
                ),
            ]
        return None


class ExtendedPersonLayout(PersonLayout, AgencyPathMixin):

    request: AgencyRequest

    @cached_property
    def collection(self) -> ExtendedPersonCollection:  # type:ignore
        return ExtendedPersonCollection(self.request.session)

    @cached_property
    def move_membership_within_person_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                AgencyMembershipMoveWithinPerson,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )

    @property
    def default_membership_title(self) -> str:
        return self.request.translate(_('Member'))


class AgencySearchLayout(DefaultLayout, AgencyPathMixin):
    request: AgencyRequest
