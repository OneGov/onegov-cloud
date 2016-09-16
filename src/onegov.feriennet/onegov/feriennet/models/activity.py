from onegov.activity import Activity
from onegov.org.models.extensions import (
    ContactExtension,
    CoordinatesExtension,
    PersonLinkExtension,
)


class VacationActivity(Activity, ContactExtension, PersonLinkExtension,
                       CoordinatesExtension):

    __mapper_args__ = {'polymorphic_identity': 'vacation'}

    es_type_name = 'vacation'

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'text': {'type': 'localized_html'}
    }

    @property
    def es_public(self):
        return self.state == 'accepted'

    @property
    def es_language(self):
        return 'de'

    @property
    def es_sugggestions(self):
        return {
            'input': (self.title.lower(), )
        }
