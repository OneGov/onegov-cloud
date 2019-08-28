from cached_property import cached_property
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models.move import AgencyMembershipMoveWithinPerson
from onegov.core.elements import Link
from onegov.org.elements import LinkGroup
from onegov.org.layout import PersonCollectionLayout
from onegov.org.layout import PersonLayout
from onegov.agency.layouts.agency import AgencyLayout
from onegov.org import _

class AgencyPathMixin(object):

    def agency_path(self, agency):
        return ' > '.join((
            self.request.translate(bc.text)
            for bc in AgencyLayout(agency, self.request).breadcrumbs[2:]
        ))


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
