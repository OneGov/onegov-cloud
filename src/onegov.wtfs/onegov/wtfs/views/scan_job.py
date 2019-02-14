from morepath import redirect
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.forms import AddScanJobForm
from onegov.wtfs.forms import EditScanJobForm
from onegov.wtfs.forms import UnrestrictedAddScanJobForm
from onegov.wtfs.forms import UnrestrictedEditScanJobForm
from onegov.wtfs.layouts import AddScanJobLayout
from onegov.wtfs.layouts import EditScanJobLayout
from onegov.wtfs.layouts import ScanJobLayout
from onegov.wtfs.layouts import ScanJobsLayout
from onegov.wtfs.layouts import MailLayout
from onegov.wtfs.models import ScanJob
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted
from onegov.wtfs.security import ViewModel
from onegov.core.templates import render_template


@WtfsApp.html(
    model=ScanJobCollection,
    template='scan_jobs.pt',
    permission=ViewModel
)
def view_scan_jobs(self, request):
    """ View the list of scan jobs. """
    layout = ScanJobsLayout(self, request)

    return {
        'layout': layout,
        'permission': ViewModel
    }


@WtfsApp.form(
    model=ScanJobCollection,
    name='add-unrestricted',
    template='form.pt',
    permission=AddModelUnrestricted,
    form=UnrestrictedAddScanJobForm
)
def add_scan_job_unrestricted(self, request, form):
    """ Create a new scan job. """
    layout = AddScanJobLayout(self, request)

    if form.submitted(request):
        scan_job = ScanJob()
        form.update_model(scan_job)
        request.session.add(scan_job)
        request.message(_("Scan job added."), 'success')
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
    layout = AddScanJobLayout(self, request)

    if form.submitted(request):
        scan_job = ScanJob()
        form.update_model(scan_job)
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
    form=UnrestrictedEditScanJobForm
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
