from onegov.form import FormCollection
from onegov.reservation import ResourceCollection
from onegov.org.elements import Link, LinkGroup
from onegov.org.models import AtoZPages, ImageSetCollection
from onegov.people import PersonCollection
from onegov.town import TownApp, _


@TownApp.homepage_widget(tag='services')
class ServicesWidget(object):
    template = """
        <xsl:template match="services">
            <h2 tal:content="services_panel.title"></h2>

            <metal:block use-macro="layout.macros['panel-links']"
                tal:define="panel services_panel"
            />
        </xsl:template>
    """

    def get_service_links(self, layout):
        yield Link(
            text=_("Online Counter"),
            url=layout.request.class_link(FormCollection),
            subtitle=(
                layout.org.meta.get('online_counter_label') or
                _("Forms and applications")
            )
        )

        yield Link(
            text=_("Reservations"),
            url=layout.request.class_link(ResourceCollection),
            subtitle=(
                layout.org.meta.get('reservations_label') or
                _("Daypasses and rooms")
            )
        )

        resources = ResourceCollection(layout.app.libres_context)

        # ga-tageskarte is the legacy name
        sbb_daypass = resources.by_name('sbb-tageskarte') \
            or resources.by_name('ga-tageskarte')

        if sbb_daypass:
            yield Link(
                text=_("SBB Daypass"),
                url=layout.request.link(sbb_daypass),
                subtitle=(
                    layout.org.meta.get('daypass_label') or
                    _("Generalabonnement for Towns")
                )
            )

    def get_variables(self, layout):
        return {
            'services_panel': LinkGroup(_("Services"), links=tuple(
                self.get_service_links(layout)
            ))
        }


@TownApp.homepage_widget(tag='directories')
class DirectoriesWidget(object):

    template = """
        <xsl:template match="directories">
            <h2 tal:content="directories_panel.title"></h2>

            <metal:block use-macro="layout.macros['panel-links']"
                tal:define="panel directories_panel"
            />
        </xsl:template>
    """

    def get_variables(self, layout):
        request = layout.request

        return {
            'directories_panel': LinkGroup(
                title=_("Directories"),
                links=[
                    Link(
                        text=_("People"),
                        url=request.class_link(PersonCollection),
                        subtitle=_("All contacts")
                    ),
                    Link(
                        text=_("Photo Albums"),
                        url=request.class_link(ImageSetCollection),
                        subtitle=_("Impressions")
                    ),
                    Link(
                        text=_("Topics"),
                        url=request.class_link(AtoZPages),
                        subtitle=_("Catalog A-Z")
                    )
                ]
            )
        }
