import morepath

from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection, FormDefinition
from onegov.org import _, OrgApp
from onegov.org.cli import close_ticket
from onegov.org.elements import Link
from onegov.org.forms import FormDefinitionForm
from onegov.org.forms.form_definition import FormDefinitionUrlForm
from onegov.org.layout import FormEditorLayout, FormSubmissionLayout
from onegov.org.models import CustomFormDefinition
from webob import exc

from onegov.org.models.form import submission_deletable


def get_form_class(model, request):

    if isinstance(model, FormCollection):
        model = CustomFormDefinition()

    form_classes = {
        'builtin': FormDefinitionForm,
        'custom': FormDefinitionForm
    }

    return model.with_content_extensions(form_classes[model.type], request)


def get_hints(layout, window):
    if not window:
        return

    if window.in_the_past:
        yield 'stop', _("The registration has ended")
    elif not window.enabled:
        yield 'stop', _("The registration is closed")

    if window.enabled and window.in_the_future:
        yield 'date', _("The registration opens on ${day}, ${date}", mapping={
            'day': layout.format_date(window.start, 'weekday_long'),
            'date': layout.format_date(window.start, 'date_long')
        })

    if window.enabled and window.in_the_present:
        yield 'date', _("The registration closes on ${day}, ${date}", mapping={
            'day': layout.format_date(window.end, 'weekday_long'),
            'date': layout.format_date(window.end, 'date_long')
        })

        if window.limit and window.overflow:
            yield 'count', _("There's a limit of ${count} attendees", mapping={
                'count': window.limit
            })

        if window.limit and not window.overflow:
            spots = window.available_spots

            if spots == 0:
                yield 'stop', _("There are no spots left")
            elif spots == 1:
                yield 'count', _("There is one spot left")
            else:
                yield 'count', _("There are ${count} spots left", mapping={
                    'count': spots
                })


def handle_form_change_name(form, session, new_name):
    new_form = form.for_new_name(new_name)
    session.add(new_form)
    session.flush()

    submissions = form.submissions
    windows = form.registration_windows

    with session.no_autoflush:
        # This placed elsewhere will not work
        form.submissions = []
        form.registration_windows = []

        # assigning the whole list directly will not work
        for s in submissions:
            s.name = new_name
            new_form.submissions.append(s)
        for w in windows:
            w.name = new_name
            new_form.registration_windows.append(w)

    session.flush()

    assert not form.submissions
    assert not form.registration_windows
    return new_form


@OrgApp.form(
    model=FormDefinition, form=FormDefinitionUrlForm,
    template='form.pt', permission=Private,
    name='change-url'
)
def handle_change_form_name(self, request, form, layout=None):
    """Since the name used for the url is the primary key, we create a new
    FormDefinition to make our live easier """
    site_title = _('Change Url')
    if form.submitted(request):
        new_form = handle_form_change_name(
            self, request.session, form.name.data
        )
        request.session.delete(self)
        return request.redirect(request.link(new_form))
    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': layout or FormEditorLayout(self, request),
        'form': form,
        'title': site_title,
    }


@OrgApp.form(
    model=FormDefinition,
    template='form.pt', permission=Public,
    form=lambda self, request: self.form_class
)
def handle_defined_form(self, request, form, layout=None):
    """ Renders the empty form and takes input, even if it's not valid, stores
    it as a pending submission and redirects the user to the view that handles
    pending submissions.

    """

    collection = FormCollection(request.session)

    if not self.current_registration_window:
        spots = 0
        enabled = True
    else:
        spots = 1
        enabled = self.current_registration_window.accepts_submissions(spots)

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form, state='pending', spots=spots)

        return morepath.redirect(request.link(submission))

    layout = layout or FormSubmissionLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'form': enabled and form,
        'definition': self,
        'form_width': 'small',
        'lead': layout.linkify(self.meta.get('lead')),
        'text': self.content.get('text'),
        'people': self.people,
        'contact': self.contact_html,
        'coordinates': self.coordinates,
        'hints': tuple(get_hints(layout, self.current_registration_window)),
        'hints_callout': not enabled,
        'button_text': _('Continue')
    }


@OrgApp.form(model=FormCollection, name='new', template='form.pt',
             permission=Private, form=get_form_class)
def handle_new_definition(self, request, form, layout=None):

    if form.submitted(request):

        if self.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_("A form with this name already exists"))
        else:
            definition = self.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
                type='custom'
            )
            form.populate_obj(definition)

            request.success(_("Added a new form"))
            return morepath.redirect(request.link(definition))

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(self)),
        Link(_("New Form"), request.link(self, name='new'))
    ]

    return {
        'layout': layout,
        'title': _("New Form"),
        'form': form,
        'form_width': 'large',
    }


@OrgApp.form(model=FormDefinition, template='form.pt', permission=Private,
             form=get_form_class, name='edit')
def handle_edit_definition(self, request, form, layout=None):

    if form.submitted(request):
        form.populate_obj(self, exclude={'definition'})
        self.definition = form.definition.data

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    collection = FormCollection(request.session)

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Forms"), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(_("Edit"), request.link(self, name='edit'))
    ]

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large',
    }


@OrgApp.view(model=FormDefinition, request_method='DELETE',
             permission=Private)
def delete_form_definition(self, request):
    """
    With introduction of cancelling submissions over the registration window,
    we encourage the user to use this functionality to cancel all form
    submissions through the ticket system.

    This ensures all submissions are cancelled/denied and the tickets are
    closed.In that case the ticket itself attached to the submission is
    deletable.

    If the customer wants to delete the form directly, we allow it now even
    when there are completed submissions. In each case there is a ticket
    associated with it we might take a snapshot before deleting it.
    """

    request.assert_valid_csrf_token()

    if self.type != 'custom':
        raise exc.HTTPMethodNotAllowed()

    def handle_ticket(submission):
        ticket = submission_deletable(submission, request.session)
        if ticket is False:
            raise exc.HTTPMethodNotAllowed()
        if ticket is not True:
            close_ticket(ticket, request.current_user, request)
            ticket.create_snapshot(request)

    def handle_submissions(submissions):
        for s in submissions:
            handle_ticket(s)

    FormCollection(request.session).definitions.delete(
        self.name,
        with_submissions=True,
        with_registration_windows=True,
        handle_submissions=handle_submissions
    )
