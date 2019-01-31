from morepath import redirect
from onegov.core.security import Secret
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.forms import MunicipalityForm
from onegov.wtfs.layouts import AddMunicipalityLayout
from onegov.wtfs.layouts import EditMunicipalityLayout
from onegov.wtfs.layouts import MunicipalitiesLayout
from onegov.wtfs.layouts import MunicipalityLayout
from onegov.wtfs.models import Municipality


@WtfsApp.html(
    model=MunicipalityCollection,
    template='municipalities.pt',
    permission=Secret
)
def view_municipalities(self, request):
    """ View the list of municipalities.

    This view is only visible by an admin.

    """
    layout = MunicipalitiesLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=MunicipalityCollection,
    name='add',
    template='form.pt',
    permission=Secret,
    form=MunicipalityForm
)
def add_municipality(self, request, form):
    """ Create a new municipality.

    This view is only visible by an admin.

    """
    layout = AddMunicipalityLayout(self, request)

    if form.submitted(request):
        municipality = Municipality()
        form.update_model(municipality)
        request.session.add(municipality)
        request.message(_("Municipality added."), 'success')
        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.html(
    model=Municipality,
    template='municipality.pt',
    permission=Secret
)
def view_municipality(self, request):
    """ View a single municipality.

    This view is only visible by an admin.

    """
    layout = MunicipalityLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=Municipality,
    name='edit',
    template='form.pt',
    permission=Secret,
    form=MunicipalityForm
)
def edit_municipality(self, request, form):
    """ Edit a municipality.

    This view is only visible by an admin.

    """

    layout = EditMunicipalityLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Municipality modified."), 'success')
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
    model=Municipality,
    request_method='DELETE',
    permission=Secret
)
def delete_municipality(self, request):
    """ Delete a municipality.

    This view is only visible by an admin.

    """

    request.assert_valid_csrf_token()
    MunicipalityCollection(request.session).delete(self)
    request.message(_("Municipality deleted."), 'success')
