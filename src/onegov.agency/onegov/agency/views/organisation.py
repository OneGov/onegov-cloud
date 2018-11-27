from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.org.layout import DefaultLayout
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from onegov.core.security import Private
from onegov.org.elements import Link
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection
from onegov.org.models import Organisation


@AgencyApp.html(
    model=Organisation,
    name='view-hidden',
    template='hidden.pt',
    permission=Private
)
def view_hidden_agencies(self, request):
    session = request.session

    agencies = ExtendedAgencyCollection(session).query()
    agencies = agencies.filter(
        ExtendedAgency.meta['is_hidden_from_public'] == True
    )
    agencies = agencies.order_by(None).order_by(ExtendedAgency.title)
    agencies = agencies.all()

    memberships = AgencyMembershipCollection(session).query()
    memberships = memberships.filter(
        AgencyMembership.meta['is_hidden_from_public'] == True
    )
    memberships = memberships.order_by(None).order_by(AgencyMembership.title)
    memberships = memberships.all()

    people = ExtendedPersonCollection(session).query()
    people = people.filter(
        ExtendedPerson.meta['is_hidden_from_public'] == True
    )
    people = people.order_by(None).order_by(
        ExtendedPerson.last_name,
        ExtendedPerson.first_name
    )
    people = people.all()

    layout = DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Hidden contents"), '#'))

    return {
        'title': _("Hidden contents"),
        'agencies': agencies,
        'memberships': memberships,
        'people': people,
        'layout': layout
    }
