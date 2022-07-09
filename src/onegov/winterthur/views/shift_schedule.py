import base64

from onegov.core.orm.types import JSON
from onegov.core.security import Public
from onegov.org.layout import GeneralFileCollectionLayout
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.winterthur import WinterthurApp
from sqlalchemy import cast


@WinterthurApp.html(
    model=GeneralFileCollection,
    name='shift-schedule',
    permission=Public,
    template='shift_schedule.pt'
)
def view_shift_schedule(self, request):

    query = self.query().filter(
        GeneralFile.published.is_(True),
        cast(GeneralFile.reference, JSON)['content_type'] == 'application/pdf'
    )
    query = query.order_by(GeneralFile.created.desc())
    file = query.first()

    image = ''
    if file:
        image = request.app.get_shift_schedule_image(file)
        image = base64.b64encode(image.getvalue()).decode()
        image = f'data:image/png;base64,{image}'

    return {
        'title': "Schichtplan",
        'layout': GeneralFileCollectionLayout(self, request),
        'image': image,
        'model': self
    }
