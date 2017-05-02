from cached_property import cached_property
from onegov.activity import Activity, ActivityCollection
from onegov.activity.models import DAYS
from onegov.core.templates import render_macro
from onegov.feriennet import _
from onegov.org.elements import Link, ConfirmLink
from onegov.org.models.extensions import CoordinatesExtension
from onegov.search import ORMSearchable
from onegov.ticket import handlers, Handler, Ticket


class VacationActivity(Activity, CoordinatesExtension, ORMSearchable):

    __mapper_args__ = {'polymorphic_identity': 'vacation'}

    es_type_name = 'vacation'

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'text': {'type': 'localized_html'},
        'organiser': {'type': 'text'}
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

    @property
    def organiser(self):
        organiser = [
            self.user.username,
            self.user.realname
        ]

        userprofile_keys = (
            'organisation',
            'address',
            'zip_code',
            'place',
            'email',
            'phone',
            'emergency',
            'website',
            'bank_account',
            'bank_beneficiary',
        )

        for key in userprofile_keys:
            if not self.user.data:
                continue
            if self.user.data.get(key):
                organiser.append(self.user.data[key])

        return organiser

    def ordered_tags(self, request):
        tags = [request.translate(_(tag)) for tag in self.tags]

        if DAYS.has(self.durations, DAYS.half):
            tags.append(request.translate(_("Half day")))
        if DAYS.has(self.durations, DAYS.full):
            tags.append(request.translate(_("Full day")))
        if DAYS.has(self.durations, DAYS.many):
            tags.append(request.translate(_("Multiple days")))

        return sorted(tags)


class ActivityTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FER'}
    es_type_name = 'activity_tickets'


@handlers.registered_handler('FER')
class VacationActivityHandler(Handler):

    handler_title = _("Activities")

    @cached_property
    def collection(self):
        # use the base class here, because the VacationActivityCollection
        # enforces the query policy for which we need the current request's
        # identity -> we're too far down the stack to care for this here
        return ActivityCollection(self.session, type='vacation')

    @cached_property
    def activity(self):
        return self.collection.by_id(self.id)

    @property
    def deleted(self):
        return self.activity is None

    @property
    def email(self):
        return self.activity.reporter

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
        from onegov.feriennet.layout import DefaultLayout
        layout = DefaultLayout(self.activity, request)

        a = ActivityCollection(request.app.session())
        a = a.by_username(self.activity.username)

        return render_macro(
            layout.macros['activity_ticket_summary'], request, {
                'activity': self.activity,
                'layout': layout,
                'show_ticket_panel': False,
                'ticket': self.ticket,
                'is_first': a.count() == 1
            }
        )

    def get_links(self, request):

        links = []

        if self.activity.state in ('proposed', 'archived'):
            links.append(ConfirmLink(
                text=_("Publish"),
                url=request.link(self.activity, name='annehmen'),
                confirm=_("Do you really want to publish this activity?"),
                extra_information=_("This cannot be undone."),
                classes=('confirm', 'accept-activity'),
                yes_button_text=_("Publish Activity")
            ))

        if self.activity.state == 'accepted':
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

        links.append(Link(
            text=_('Show activity'),
            url=request.return_here(request.link(self.activity)),
            classes=('show-activity', )
        ))

        return links
