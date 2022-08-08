import base64

from onegov.core.security import Public
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation
from onegov.winterthur import WinterthurApp, _


@WinterthurApp.html(
    model=Organisation,
    name='shift-schedule',
    permission=Public,
    template='shift_schedule.pt'
)
def view_shift_schedule(self, request):

    image = request.app.get_shift_schedule_image()
    if image:
        image = base64.b64encode(image.getvalue()).decode()
        image = f'data:image/png;base64,{image}'

    return {
        'title': _('Shift schedule'),
        'layout': DefaultLayout(self, request),
        'image': image,
        'model': self
    }
