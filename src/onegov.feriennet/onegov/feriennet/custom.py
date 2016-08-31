from onegov.org.models import BuiltinFormDefinition
from onegov.feriennet import _, FeriennetApp
from onegov.org.elements import Link
from onegov.page import Page, PageCollection


@FeriennetApp.template_variables()
def get_template_variables(request):
    return {
        'top_navigation': get_top_navigation(request)
    }


def get_top_navigation(request):

    pages = PageCollection(request.app.session())
    pages = pages.query().filter(
        Page.name.in_(('teilnahmebedingungen', 'sponsoren', 'ueber-uns'))
    )

    pages = {page.name: page for page in pages.all()}

    return (
        Link(_("Activities"), '#'),
        Link(
            pages['teilnahmebedingungen'].title,
            request.link(pages['teilnahmebedingungen'])
        ),
        Link(
            "Kontakt",
            request.class_link(BuiltinFormDefinition, {'name': 'kontakt'})
        ),
        Link(
            pages['sponsoren'].title,
            request.link(pages['sponsoren'])
        ),
        Link(
            pages['ueber-uns'].title,
            request.link(pages['ueber-uns'])
        )
    )
