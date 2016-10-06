from itertools import chain
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.elements import Link


@FeriennetApp.template_variables()
def get_template_variables(request):

    # inject an activites link in front of all top navigation links
    activities = Link(
        text=_("Activities"),
        url=request.class_link(VacationActivityCollection)
    )

    layout = DefaultLayout(request.app.org, request)
    links = chain((activities, ), layout.top_navigation)

    return {
        'top_navigation': links
    }
