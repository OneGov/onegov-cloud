from cached_property import cached_property
from libres.db.models import Reservation
from onegov.core.templates import render_macro
from onegov.form import FormSubmissionCollection
from onegov.libres import Resource
from onegov.ticket import Ticket, Handler, handlers
from onegov.town import _
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from purl import URL


class FormSubmissionTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FRM'}


class ReservationTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'RSV'}


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

    @cached_property
    def collection(self):
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self):
        return self.collection.by_id(self.id)

    @cached_property
    def form(self):
        return self.submission.form_class(data=self.submission.data)

    @property
    def email(self):
        return self.submission.email

    @property
    def title(self):
        return self.submission.title

    @property
    def group(self):
        return self.submission.form.title

    def get_summary(self, request):
        layout = DefaultLayout(self.submission, request)
        return render_macro(layout.macros['display_form'], request, {
            'form': self.form,
            'layout': layout
        })

    def get_links(self, request):

        edit_link = URL(request.link(self.submission))
        edit_link = edit_link.query_param('edit', '')
        edit_link = edit_link.query_param('return-to', request.url)

        return [
            Link(
                text=_('Edit submission'),
                url=edit_link.as_string(),
                classes=('edit-link', )
            )
        ]


@handlers.registered_handler('RSV')
class ReservationHandler(Handler):

    @cached_property
    def resource(self):
        query = self.session.query(Resource)
        query = query.filter(Resource.id == self.reservations[0].resource)

        return query.one()

    @cached_property
    def reservations(self):
        # libres allows for multiple reservations with a single request (token)
        # for now we don't really have that case in onegov.town, but we
        # try to be aware of it as much as possible
        query = self.session.query(Reservation)
        query = query.filter(Reservation.token == self.id)

        return query.all()

    @property
    def email(self):
        # the e-mail is the same over all reservations
        return self.reservations[0].email

    @property
    def title(self):
        if self.resource.type == 'daypass':
            template = '{start:%d.%m.%Y} ({quota})'
        elif self.resource.type == 'room':
            template = '{start:%d.%m.%Y} {start:%H:%M} - {end:%H:%M}'
        else:
            raise NotImplementedError

        parts = []

        for reservation in self.reservations:
            parts.append(
                template.format(
                    start=reservation.display_start(),
                    end=reservation.display_end(),
                    quota=reservation.quota
                )
            )

        return ', '.join(parts)

    @property
    def group(self):
        return self.resource.title
