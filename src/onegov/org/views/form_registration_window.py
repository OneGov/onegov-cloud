from collections import defaultdict
from onegov.core.security import Private
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.form import FormSubmission
from onegov.org import OrgApp, _
from onegov.org.forms import FormRegistrationWindowForm
from onegov.org.layout import FormSubmissionLayout
from onegov.core.elements import Link, Confirm, Intercooler
from sqlalchemy import desc


@OrgApp.form(
    model=FormDefinition,
    name='new-registration-window',
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt')
def handle_new_registration_form(self, request, form):

    title = _("New Registration Window")

    layout = FormSubmissionLayout(self, request)
    layout.editbar_links = None
    layout.breadcrumbs.append(Link(title, '#'))

    if form.submitted(request):

        form.populate_obj(self.add_registration_window(
            form.start.data,
            form.end.data
        ))

        request.success(_("The registration window was added successfully"))
        return request.redirect(request.link(self))

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'helptext': _(
            "Registration windows limit forms to a set number of submissions "
            "and a specific time-range."
        )
    }


@OrgApp.html(
    model=FormRegistrationWindow,
    permission=Private,
    template='registration_window.pt')
def view_registration_window(self, request):

    layout = FormSubmissionLayout(self.form, request)
    title = layout.format_date_range(self.start, self.end)

    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = [
        Link(
            text=_("Edit"),
            url=request.link(self, 'edit'),
            attrs={'class': 'edit-link'}
        ),
        Link(
            text=_("Delete"),
            url=layout.csrf_protected_url(request.link(self)),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _(
                        "Do you really want to delete "
                        "this registration window?"
                    ),
                    _("Existing submissions will be disassociated."),
                    _("Delete registration window"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.link(self.form)
                )
            )
        )
    ]

    registrations = defaultdict(list)

    q = request.session.query(FormSubmission)
    q = q.filter_by(registration_window_id=self.id)
    q = q.filter_by(state='complete')
    q = q.order_by(desc(FormSubmission.received))

    for submission in q:
        if not submission.registration_state:
            continue

        registrations[submission.registration_state].append(submission)

    return {
        'layout': layout,
        'title': title,
        'model': self,
        'registrations': registrations,
        'groups': (
            (_("Open"), 'open'),
            (_("Confirmed"), 'confirmed'),
            (_("Cancelled"), 'cancelled'),
        )
    }


@OrgApp.form(
    model=FormRegistrationWindow,
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt',
    name='edit')
def handle_edit_registration_form(self, request, form):

    title = _("Edit Registration Window")

    layout = FormSubmissionLayout(self.form, request)
    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = []

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.form))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': layout,
        'title': title,
        'form': form
    }


@OrgApp.view(
    model=FormRegistrationWindow,
    permission=Private,
    request_method='DELETE')
def delete_registration_window(self, request):
    request.assert_valid_csrf_token()

    self.disassociate()
    request.session.delete(self)

    request.success(_("The registration window was deleted"))
