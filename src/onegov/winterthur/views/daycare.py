from __future__ import annotations

from onegov.core.security import Public
from onegov.winterthur import WinterthurApp, _
from onegov.winterthur.daycare import DaycareSubsidyCalculator
from onegov.winterthur.daycare import DaycareSubsidyCalculatorForm
from onegov.winterthur.layout import DaycareSubsidyCalculatorLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.winterthur.request import WinterthurRequest


@WinterthurApp.form(
    model=DaycareSubsidyCalculator,
    form=DaycareSubsidyCalculatorForm,
    permission=Public,
    template='daycare.pt')
def view_daycare_subsidy_calculator(
    self: DaycareSubsidyCalculator,
    request: WinterthurRequest,
    form: DaycareSubsidyCalculatorForm
) -> RenderData:

    calculation = None
    if form.submitted(request):
        assert form.selected_daycare is not None
        assert form.income.data is not None
        assert form.wealth.data is not None
        calculation = self.calculate(
            daycare=form.selected_daycare,
            services=form.services.services,
            income=form.income.data,
            wealth=form.wealth.data,
            rebate=form.rebate.data
        )

    return {
        'title': _('Daycare Subsidy Calculator'),
        'layout': DaycareSubsidyCalculatorLayout(self, request),
        'form': form,
        'calculation': calculation,
        'button_text': _('Calculate'),
        'settings': self.settings,
        'eligible': (
            calculation and calculation.city_share_per_month != '0.00'
        )
    }
