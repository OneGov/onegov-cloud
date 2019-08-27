from morepath import redirect
from onegov.core.templates import render_template
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.forms import AddScanJobForm
from onegov.wtfs.forms import EditScanJobForm
from onegov.wtfs.forms import ScanJobsForm
from onegov.wtfs.forms import UnrestrictedScanJobForm
from onegov.wtfs.forms import UnrestrictedScanJobsForm
from onegov.wtfs.layouts import AddScanJobLayout
from onegov.wtfs.layouts import DeliveryNoteLayout
from onegov.wtfs.layouts import EditScanJobLayout
from onegov.wtfs.layouts import MailLayout
from onegov.wtfs.layouts import ScanJobLayout
from onegov.wtfs.layouts import ScanJobsLayout
from onegov.wtfs.models import ScanJob
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted
from onegov.wtfs.security import ViewModel
from onegov.wtfs.security import ViewModelUnrestricted


@WtfsApp.form(
    model=ScanJobCollection,
    permission=ViewModel,
    form=ScanJobsForm,
    template='scan_jobs.pt'
)
def view_scan_jobs(self, request, form):
    if request.has_permission(self, ViewModelUnrestricted):
        return redirect(request.link(self, 'unrestricted'))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': ScanJobsLayout(self, request),
        'form': form,
        'button_text': _("Apply filter"),
        'reset_text': _("Reset filter"),
        'permission': ViewModel
    }


@WtfsApp.form(
    model=ScanJobCollection,
    name='unrestricted',
    permission=ViewModelUnrestricted,
    form=UnrestrictedScanJobsForm,
    template='scan_jobs_unrestricted.pt'
)
def view_scan_jobs_unrestricted(self, request, form):
    if not form.errors:
        form.apply_model(self)

    return {
        'layout': ScanJobsLayout(self, request),
        'form': form,
        'button_text': _("Apply filter"),
        'reset_text': _("Reset filter"),
        'permission': ViewModel
    }


@WtfsApp.form(
    model=ScanJobCollection,
    name='add-unrestricted',
    template='form.pt',
    permission=AddModelUnrestricted,
    form=UnrestrictedScanJobForm
)
def add_scan_job_unrestricted(self, request, form):
    """ Create a new scan job. """
    layout = AddScanJobLayout(self, request)

    if form.submitted(request):
        scan_job = ScanJob()
        form.update_model(scan_job)
        scan_job.delivery_number = self.next_delivery_number(
            scan_job.municipality_id
        )
        request.session.add(scan_job)
        request.session.flush()
        request.message(_("Scan job added."), 'success')

        receivers = scan_job.municipality.contacts
        if receivers:
            subject = request.translate(
                _("Order confirmation for scanning your tax returns")
            )
            request.app.send_transactional_email(
                subject=subject,
                receivers=receivers,
                reply_to=request.app.mail['transactional']['sender'],
                content=render_template(
                    'mail_confirm.pt',
                    request,
                    {
                        'title': subject,
                        'model': scan_job,
                        'layout': MailLayout(scan_job, request)
                    }
                ),
            )

        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.form(
    model=ScanJobCollection,
    name='add',
    template='form.pt',
    permission=AddModel,
    form=AddScanJobForm
)
def add_scan_job(self, request, form):
    """ Create a new scan job. """

    if request.has_permission(self, AddModelUnrestricted):
        return redirect(request.link(self, name='add-unrestricted'))

    layout = AddScanJobLayout(self, request)

    if form.submitted(request):
        scan_job = ScanJob()
        form.update_model(scan_job)
        scan_job.delivery_number = self.next_delivery_number(
            scan_job.municipality_id
        )
        request.session.add(scan_job)
        request.message(_("Scan job added."), 'success')

        subject = request.translate(
            _("Order confirmation for scanning your tax returns")
        )
        request.app.send_transactional_email(
            subject=subject,
            receivers=(request.identity.userid, ),
            reply_to=request.app.mail['transactional']['sender'],
            content=render_template(
                'mail_confirm.pt',
                request,
                {
                    'title': subject,
                    'model': scan_job,
                    'layout': MailLayout(scan_job, request)
                }
            ),
        )

        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.html(
    model=ScanJob,
    template='scan_job.pt',
    permission=ViewModel
)
def view_scan_job(self, request):
    """ View a single scan job. """
    layout = ScanJobLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=ScanJob,
    name='edit-unrestricted',
    template='form.pt',
    permission=EditModelUnrestricted,
    form=UnrestrictedScanJobForm
)
def edit_scan_job_unrestricted(self, request, form):
    """ Edit a scan job. """

    layout = EditScanJobLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Scan job modified."), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url,
    }


@WtfsApp.form(
    model=ScanJob,
    name='edit',
    template='form.pt',
    permission=EditModel,
    form=EditScanJobForm
)
def edit_scan_job(self, request, form):
    """ Edit a scan job. """

    if request.has_permission(self, EditModelUnrestricted):
        return redirect(request.link(self, name='edit-unrestricted'))

    layout = EditScanJobLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Scan job modified."), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'subtitle': layout.format_date(self.dispatch_date, 'date'),
        'button_text': _("Save"),
        'cancel': layout.cancel_url,
    }


@WtfsApp.view(
    model=ScanJob,
    request_method='DELETE',
    permission=DeleteModel
)
def delete_scan_job(self, request):
    """ Delete a scan job. """

    request.assert_valid_csrf_token()
    ScanJobCollection(request.session).delete(self)
    request.message(_("Scan job deleted."), 'success')


@WtfsApp.html(
    model=ScanJob,
    template='delivery_note.pt',
    name='delivery-note',
    permission=ViewModel
)
def view_scan_job_delivery_note(self, request):
    """ View a single scan job. """
    layout = DeliveryNoteLayout(self, request)

    return {
        'layout': layout,
    }
