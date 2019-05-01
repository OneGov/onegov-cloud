from humanize import naturalsize
from morepath import redirect
from morepath import Response
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import UserManualForm
from onegov.wtfs.layouts import EditUserManualLayout
from onegov.wtfs.layouts import UserManualLayout
from onegov.wtfs.models import UserManual
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import ViewModel


@WtfsApp.html(
    model=UserManual,
    template='user_manual.pt',
    permission=ViewModel
)
def view_user_manual(self, request):
    """ View the user manual. """
    layout = UserManualLayout(self, request)
    filesize = naturalsize(self.content_length or 0)

    return {
        'layout': layout,
        'filesize': filesize
    }


@WtfsApp.form(
    model=UserManual,
    name='edit',
    template='form.pt',
    permission=EditModel,
    form=UserManualForm
)
def edit_user_manual(self, request, form):
    """ Edit the user manual """

    layout = EditUserManualLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("User manual modified."), 'success')
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
    model=UserManual,
    permission=ViewModel,
    name='pdf'
)
def user_manual_pdf(self, request):
    if not self.pdf:
        return Response(status='503 Service Unavailable')

    return Response(
        self.pdf,
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            request.translate(_("User manual"))
        )
    )
