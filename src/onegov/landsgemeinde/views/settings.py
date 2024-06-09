""" The settings view, defining things like the logo or color of the org. """
from onegov.core.security import Secret
from onegov.org import _
from onegov.org.models import Organisation
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.forms import OpenDataSettingsForm
from onegov.town6.layout import SettingsLayout
from onegov.org.views.settings import handle_generic_settings

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@LandsgemeindeApp.form(
    model=Organisation, name='open-data-settings', permission=Secret,
    template='form.pt', form=OpenDataSettingsForm,
    setting=_("Open Data"), icon='far fa-file-export', order=500
)
def town_handle_chat_settings(
    self: Organisation,
    request: 'TownRequest',
    form: OpenDataSettingsForm
) -> 'RenderData | Response':
    layout = SettingsLayout(self, request, _("Open Data"))
    return handle_generic_settings(self, request, form, _("Open Data"), layout)
