from cached_property import cached_property
from onegov.agency.collections import ExtendedPersonCollection
from onegov.org.layout import PersonCollectionLayout
from onegov.org.layout import PersonLayout
from onegov.agency.layouts.agency import AgencyLayout


class AgencyPathMixin(object):

    def agency_path(self, agency):
        return ' > '.join((
            self.request.translate(bc.text)
            for bc in AgencyLayout(agency, self.request).breadcrumbs[2:]
        ))


class ExtendedPersonCollectionLayout(PersonCollectionLayout, AgencyPathMixin):
    pass


class ExtendedPersonLayout(PersonLayout, AgencyPathMixin):

    @cached_property
    def collection(self):
        return ExtendedPersonCollection(self.request.session)
