from morepath import redirect
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.forms import PaymentTypesForm
from onegov.wtfs.layouts import PaymentTypesLayout
from onegov.wtfs.security import EditModel


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from webob.response import Response


@WtfsApp.form(
    model=PaymentTypeCollection,
    template='form.pt',
    permission=EditModel,
    form=PaymentTypesForm.get_form_class
)
def manage_payments(
    self: PaymentTypeCollection,
    request: 'CoreRequest',
    form: PaymentTypesForm
) -> 'Response | RenderData':
    """ Manage payment types. """

    layout = PaymentTypesLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_('Payment types modified.'), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'button_text': _('Save'),
        'cancel': layout.cancel_url
    }
