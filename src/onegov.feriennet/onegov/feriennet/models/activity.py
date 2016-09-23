from cached_property import cached_property
from onegov.activity import Activity
from onegov.core.templates import render_macro
from onegov.feriennet import _
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.elements import Link, ConfirmLink
from onegov.org.models.extensions import CoordinatesExtension
from onegov.search import ORMSearchable
from onegov.ticket import handlers, Handler, Ticket
from purl import URL


class VacationActivity(Activity, CoordinatesExtension, ORMSearchable):

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
    def es_skip(self):
        return self.state == 'preview'

    @property
    def es_language(self):
        return 'de'

    @property
    def es_sugggestions(self):
        return {
            'input': (self.title.lower(), )
        }

    def ordered_tags(self, request):
        return sorted([request.translate(_(tag)) for tag in self.tags])


class ActivityTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FER'}
    es_type_name = 'activity_tickets'


@handlers.registered_handler('FER')
class VacationActivityHandler(Handler):

    handler_title = _("Activities")

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
        return self.activity.username

    @property
    def title(self):
        return self.activity.title

    @property
    def subtitle(self):
        return None

    @property
    def group(self):
        return _("Activity")

    @property
    def extra_data(self):
        return None

    def get_summary(self, request):
        layout = DefaultLayout(self.activity, request)

        return render_macro(
            layout.macros['activity_ticket_summary'], request, {
                'activity': self.activity,
                'layout': layout,
                'show_ticket_panel': False
            }
        )

    def get_links(self, request):

        links = []

        if self.activity.state == 'proposed':
            links.append(ConfirmLink(
                text=_("Approve"),
                url=request.link(self.activity, name='annehmen'),
                confirm=_("Do you really want to approve this activity?"),
                extra_information=_(
                    "This cannot be undone. "
                    "The activity will be made public as a result."
                ),
                classes=('confirm', 'accept-activity'),
                yes_button_text=_("Approve Activity")
            ))
            links.append(ConfirmLink(
                text=_("Reject"),
                url=request.link(self.activity, name='ablehnen'),
                confirm=_("Do you really want to reject this activity?"),
                extra_information=_("This cannot be undone. "),
                classes=('confirm', 'reject-activity'),
                yes_button_text=_("Approve Activity")
            ))
        elif self.activity.state == 'accepted':
            links.append(ConfirmLink(
                text=_("Archive"),
                url=request.link(self.activity, name='archivieren'),
                confirm=_("Do you really want to archive this activity?"),
                extra_information=_(
                    "This cannot be undone. "
                    "The activity will be made private as a result."
                ),
                classes=('confirm', 'archive-activity'),
                yes_button_text=_("Archive Activity")
            ))

        edit_link = URL(request.link(self.activity, 'bearbeiten'))
        edit_link = edit_link.query_param('return-to', request.url)

        links.append(Link(
            text=_('Edit activity'),
            url=edit_link.as_string(),
            classes=('edit-link', )
        ))

        return links
