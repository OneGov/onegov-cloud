from morepath import redirect
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.forms import DeleteMunicipalityDatesForm
from onegov.wtfs.forms import ImportMunicipalityDataForm
from onegov.wtfs.forms import MunicipalityForm
from onegov.wtfs.layouts import AddMunicipalityLayout
from onegov.wtfs.layouts import DeleteMunicipalityDatesLayout
from onegov.wtfs.layouts import EditMunicipalityLayout
from onegov.wtfs.layouts import ImportMunicipalityDataLayout
from onegov.wtfs.layouts import MunicipalitiesLayout
from onegov.wtfs.layouts import MunicipalityLayout
from onegov.wtfs.models import Municipality
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import ViewModel


@WtfsApp.html(
    model=MunicipalityCollection,
    template='municipalities.pt',
    permission=ViewModel
)
def view_municipalities(self, request):
    """ View the list of municipalities. """

    layout = MunicipalitiesLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=MunicipalityCollection,
    name='import-data',
    template='form.pt',
    permission=EditModel,
    form=ImportMunicipalityDataForm
)
def import_municipality_data(self, request, form):
    """ Import municipality data. """

    layout = ImportMunicipalityDataLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Municipality data imported."), 'success')
        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Import"),
        'cancel': layout.cancel_url
    }


@WtfsApp.form(
    model=MunicipalityCollection,
    name='add',
    template='form.pt',
    permission=AddModel,
    form=MunicipalityForm
)
def add_municipality(self, request, form):
    """ Create a new municipality. """

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
    permission=ViewModel
)
def view_municipality(self, request):
    """ View a single municipality. """

    layout = MunicipalityLayout(self, request)

    return {
        'layout': layout,
    }


@WtfsApp.form(
    model=Municipality,
    name='edit',
    template='form.pt',
    permission=EditModel,
    form=MunicipalityForm
)
def edit_municipality(self, request, form):
    """ Edit a municipality. """

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


@WtfsApp.form(
    model=Municipality,
    name='delete-dates',
    template='form.pt',
    permission=EditModel,
    form=DeleteMunicipalityDatesForm
)
def delete_municipality_dates(self, request, form):
    """ Delete a range of pick-up dates of a municipality. """

    layout = DeleteMunicipalityDatesLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Pick-up dates deleted."), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Delete"),
        'cancel': layout.cancel_url,
    }


@WtfsApp.view(
    model=Municipality,
    request_method='DELETE',
    permission=DeleteModel
)
def delete_municipality(self, request):
    """ Delete a municipality. """

    request.assert_valid_csrf_token()
    MunicipalityCollection(request.session).delete(self)
    request.message(_("Municipality deleted."), 'success')
