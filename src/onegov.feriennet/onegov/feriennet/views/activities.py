import morepath

from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.forms import VacationActivityForm
from onegov.feriennet.layout import VacationActivityCollectionLayout
from onegov.feriennet.layout import VacationActivityFormLayout
from onegov.feriennet.layout import VacationActivityLayout
from onegov.feriennet.models import VacationActivity
from onegov.org.mail import send_html_mail
from onegov.ticket import TicketCollection
from purl import URL


def get_activity_form_class(model, request):
    if isinstance(model, VacationActivityCollection):
        model = VacationActivity()

    return model.with_content_extensions(VacationActivityForm, request)


@FeriennetApp.html(
    model=VacationActivityCollection,
    template='activities.pt',
    permission=Public)
def view_activities(self, request):

    return {
        'activities': self.batch,
        'layout': VacationActivityCollectionLayout(self, request),
        'title': _("Activities")
    }


@FeriennetApp.html(
    model=VacationActivity,
    template='activity.pt',
    permission=Public)
def view_activity(self, request):

    ticket = TicketCollection(request.app.session()).by_handler_id(self.id.hex)

    return {
        'layout': VacationActivityLayout(self, request),
        'title': self.title,
        'activity': self,
        'ticket': ticket
    }


@FeriennetApp.form(
    model=VacationActivityCollection,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='neu')
def new_activity(self, request, form):

    if form.submitted(request):
        activity = self.add(
            title=form.title.data,
            username=request.current_username)

        form.populate_obj(activity)

        return morepath.redirect(request.link(activity))

    return {
        'layout': VacationActivityFormLayout(self, request, _("New Activity")),
        'title': _("New Activity"),
        'form': form
    }


@FeriennetApp.form(
    model=VacationActivity,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='bearbeiten')
def edit_activity(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))

        if 'return-to' in request.params:
            return morepath.redirect(request.params['return-to'])

        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    if 'return-to' in request.GET:
        form.action = URL(form.action)\
            .query_param('return-to', request.GET['return-to'])\
            .as_string()

    return {
        'layout': VacationActivityFormLayout(self, request, self.title),
        'title': self.title,
        'form': form
    }


@FeriennetApp.view(
    model=VacationActivity,
    permission=Private,
    name='beantragen',
    request_method='POST')
def propose_activity(self, request):

    session = request.app.session()

    with session.no_autoflush:
        self.propose()
        ticket = TicketCollection(session).open_ticket(
            handler_code='FER', handler_id=self.id.hex
        )

    send_html_mail(
        request=request,
        template='mail_ticket_opened.pt',
        subject=_("A ticket has been opened"),
        receivers=(request.current_username, ),
        content={
            'model': ticket
        }
    )

    request.success(_("Thank you for your proposal!"))
    request.app.update_ticket_count()

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(ticket, 'status'))

    # do not redirect here, intercooler doesn't deal well with that...
    return


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='annehmen',
    request_method='POST')
def accept_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='accept',
        template='mail_activity_accepted.pt',
        subject=_("Your activity has been accepted")
    )


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='ablehnen',
    request_method='POST')
def reject_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='deny',
        template='mail_activity_rejected.pt',
        subject=_("Your activity has been rejected")
    )


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='archivieren',
    request_method='POST')
def archive_activity(self, request):

    return administer_activity(
        model=self,
        request=request,
        action='archive',
        template='mail_activity_archived.pt',
        subject=_("Your activity has been archived")
    )


def administer_activity(model, request, action, template, subject):
    session = request.app.session()
    ticket = TicketCollection(session).by_handler_id(model.id.hex)

    # execute state change
    getattr(model, action)()

    send_html_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=(request.current_username, ),
        content={
            'model': model,
            'ticket': ticket
        }
    )

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(ticket))

    # do not redirect here, intercooler doesn't deal well with that...
    return
