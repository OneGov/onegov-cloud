from cached_property import cached_property
from onegov.activity import Activity
from onegov.core.templates import render_macro
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.models.extensions import CoordinatesExtension
from onegov.ticket import handlers, Handler


class VacationActivity(Activity, CoordinatesExtension):

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


@handlers.registered_handler('FER')
class VacationActivityHandler(Handler):

    @cached_property
    def collection(self):
        return VacationActivityCollection(self.session)

    @cached_property
    def activity(self):
        return self.collection.by_id(self.id)

    @property
    def deleted(self):
        return self.activity is None

    @property
    def email(self):
        return self.activity.user.username

    @property
    def title(self):
        return self.activity.title

    @property
    def subtitle(self):
        return None

    @property
    def group(self):
        return self.submission.form.title

    @property
    def extra_data(self):
        return None

    def get_summary(self, request):
        layout = DefaultLayout(self.submission, request)

        return render_macro(layout.macros['activity_detailed'], request, {
            'activity': self.activity,
            'layout': layout
        })

    def get_links(self, request):
        return []
