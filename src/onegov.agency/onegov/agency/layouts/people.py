from cached_property import cached_property
from onegov.agency.collections import ExtendedPersonCollection
from onegov.org.layout import PersonCollectionLayout
from onegov.org.layout import PersonLayout
from onegov.agency.layouts.agency import AgencyLayout


class VisibilityMixin(object):

    public_fields = (
        'academic_title',
        'address',
        'direct_phone',
        'first_name',
        'last_name',
        'phone',
        'political_party',
        'profession',
        'year'
    )

    def field_visible(self, name, model=None):
        if not getattr(model or self.model, name, None):
            return False

        if name in self.public_fields:
            return True

        return self.request.is_logged_in


class AgencyPathMixin(object):

    def agency_path(self, agency):
        return ' > '.join((
            self.request.translate(bc.text)
            for bc in AgencyLayout(agency, self.request).breadcrumbs[2:]
        ))


class ExtendedPersonCollectionLayout(
    PersonCollectionLayout, VisibilityMixin, AgencyPathMixin
):
    pass


class ExtendedPersonLayout(PersonLayout, VisibilityMixin, AgencyPathMixin):

    @cached_property
    def collection(self):
        return ExtendedPersonCollection(self.request.session)
