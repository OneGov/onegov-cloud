from onegov.activity import Period, PeriodCollection
from onegov.core.security import Secret
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.forms import PeriodForm
from onegov.feriennet.layout import PeriodCollectionLayout
from onegov.feriennet.layout import PeriodFormLayout


@FeriennetApp.html(
    model=PeriodCollection,
    template='periods.pt',
    permission=Secret)
def view_periods(self, request):
    return {
        'layout': PeriodCollectionLayout(self, request),
        'periods': self.query().order_by(Period.execution_start).all(),
        'title': _("Manage Periods")
    }


@FeriennetApp.form(
    model=PeriodCollection,
    name='neu',
    form=PeriodForm,
    template='form.pt',
    permission=Secret)
def new_period(self, request, form):

    if form.submitted(request):
        period = self.add(
            title=form.title.data,
            prebooking=form.prebooking,
            execution=form.execution,
            active=False)

        form.populate_obj(period)

        return request.redirect(request.link(self))

    return {
        'layout': PeriodFormLayout(self, request, _("New Period")),
        'form': form,
        'title': _("New Period")
    }


@FeriennetApp.form(
    model=Period,
    name='bearbeiten',
    form=PeriodForm,
    template='form.pt',
    permission=Secret)
def edit_period(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))

        return request.redirect(request.class_link(PeriodCollection))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': PeriodFormLayout(self, request, self.title),
        'form': form,
        'title': self.title
    }
