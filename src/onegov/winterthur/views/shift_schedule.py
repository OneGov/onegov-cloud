from __future__ import annotations

import base64

from onegov.core.security import Public
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation
from onegov.winterthur import WinterthurApp, _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.winterthur.request import WinterthurRequest


@WinterthurApp.html(
    model=Organisation,
    name='shift-schedule',
    permission=Public,
    template='shift_schedule.pt'
)
def view_shift_schedule(
    self: Organisation,
    request: WinterthurRequest
) -> RenderData:

    image_buffer = request.app.get_shift_schedule_image()
    if image_buffer:
        image = base64.b64encode(image_buffer.getvalue()).decode()
        image = f'data:image/png;base64,{image}'
    else:
        image = None

    return {
        'title': _('Shift schedule'),
        'layout': DefaultLayout(self, request),
        'image': image,
        'model': self
    }
