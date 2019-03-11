from morepath import redirect
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import ReportSelectionForm
from onegov.wtfs.layouts import ReportBoxesAndFormsByDeliveryLayout
from onegov.wtfs.layouts import ReportBoxesAndFormsLayout
from onegov.wtfs.layouts import ReportBoxesLayout
from onegov.wtfs.layouts import ReportFormsByMunicipalityLayout
from onegov.wtfs.layouts import ReportLayout
from onegov.wtfs.models import Report
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportBoxesAndFormsByDelivery
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.security import ViewModel


@WtfsApp.form(
    model=Report,
    template='form.pt',
    permission=ViewModel,
    form=ReportSelectionForm
)
def view_select_report(self, request, form):
    layout = ReportLayout(self, request)

    if form.submitted(request):
        return redirect(request.link(form.get_model()))

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Show")
    }


@WtfsApp.html(
    model=ReportBoxes,
    template='report_boxes.pt',
    permission=ViewModel
)
def view_report_boxes(self, request):
    return {'layout': ReportBoxesLayout(self, request)}


@WtfsApp.html(
    model=ReportBoxesAndForms,
    template='report_boxes_and_forms.pt',
    permission=ViewModel
)
def view_report_boxes_and_forms(self, request):
    return {'layout': ReportBoxesAndFormsLayout(self, request)}


@WtfsApp.html(
    model=ReportFormsByMunicipality,
    template='report_forms.pt',
    permission=ViewModel
)
def view_report_forms(self, request):
    return {'layout': ReportFormsByMunicipalityLayout(self, request)}


@WtfsApp.html(
    model=ReportBoxesAndFormsByDelivery,
    template='report_delivery.pt',
    permission=ViewModel
)
def view_report_delivery(self, request):
    return {'layout': ReportBoxesAndFormsByDeliveryLayout(self, request)}
