from cached_property import cached_property
from onegov.agency.collections import ExtendedPersonCollection
from onegov.org.layout import PersonCollectionLayout
from onegov.org.layout import PersonLayout


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


class ExtendedPersonCollectionLayout(PersonCollectionLayout, VisibilityMixin):

    pass


class ExtendedPersonLayout(PersonLayout, VisibilityMixin):

    @cached_property
    def collection(self):
        return ExtendedPersonCollection(self.request.session)

    pass
