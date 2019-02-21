from morepath import redirect
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import DailyListSelectionForm
from onegov.wtfs.layouts import DailyListBoxesLayout
from onegov.wtfs.layouts import DailyListBoxesAndFormsLayout
from onegov.wtfs.layouts import DailyListLayout
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from onegov.wtfs.security import ViewModel


@WtfsApp.form(
    model=DailyList,
    template='form.pt',
    permission=ViewModel,
    form=DailyListSelectionForm
)
def view_select_report(self, request, form):
    layout = DailyListLayout(self, request)

    if form.submitted(request):
        return redirect(request.link(form.get_model()))

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Show")
    }


@WtfsApp.html(
    model=DailyListBoxes,
    template='daily_list_boxes.pt',
    permission=ViewModel
)
def view_daily_list_boxes(self, request):
    return {'layout': DailyListBoxesLayout(self, request)}


@WtfsApp.html(
    model=DailyListBoxesAndForms,
    template='daily_list_boxes_and_forms.pt',
    permission=ViewModel
)
def view_daily_list_boxes_and_forms(self, request):
    return {'layout': DailyListBoxesAndFormsLayout(self, request)}
