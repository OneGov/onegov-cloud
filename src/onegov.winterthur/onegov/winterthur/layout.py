from cached_property import cached_property
from onegov.org.layout import DefaultLayout
from onegov.core.elements import Link, LinkGroup, Intercooler, Confirm, Block
from onegov.winterthur import _
from onegov.winterthur.collections import AddressCollection
from onegov.winterthur.collections import MissionReportCollection
from onegov.winterthur.collections import MissionReportFileCollection
from onegov.winterthur.collections import MissionReportVehicleCollection
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.roadwork import RoadworkCollection


class AddressLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Addresses"), '#'),
        ]

    @cached_property
    def editbar_links(self):
        if not self.request.is_manager:
            return

        return [
            Link(
                text=_("Update"),
                url=self.csrf_protected_url(
                    self.request.link(self.model, '+update')
                ),
                attrs={'class': 'sync'},
                traits=Intercooler(
                    request_method='POST',
                    redirect_after=self.request.url
                )
            )
        ]


class AddressSubsetLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Addresses"), self.request.class_link(AddressCollection)),
            Link(_(self.model.street), '#')
        ]


class RoadworkCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Roadworks"), '#'),
        ]


class RoadworkLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Roadworks"), self.request.class_link(RoadworkCollection)),
            Link(self.model.title, self.request.link(self.model))
        ]


class MissionReportLayout(DefaultLayout):

    def __init__(self, model, request, *suffixes):
        self.suffixes = suffixes
        super().__init__(model, request)
        request.include('iframe-enhancements')

    def breadcrumbs_iter(self):
        yield Link(
            _("Homepage"),
            self.homepage_url)

        yield Link(
            _("Mission Reports"),
            self.request.class_link(MissionReportCollection))

        yield from self.suffixes

    @cached_property
    def breadcrumbs(self):
        return list(self.breadcrumbs_iter())

    @cached_property
    def image_upload_url(self):

        if not hasattr(self.model, 'report'):
            return super().image_upload_url

        url = self.request.link(
            MissionReportFileCollection(
                self.request.session, self.model.report), name='upload')

        return self.csrf_protected_url(url)

    @cached_property
    def image_upload_json_url(self):

        if not hasattr(self.model, 'report'):
            return super().image_upload_json_url

        url = self.request.link(
            MissionReportFileCollection(
                self.request.session, self.model.report), name='upload.json')

        return self.csrf_protected_url(url)

    @cached_property
    def editbar_links(self):

        # this is a bit different then usual, trying out some things as part
        # of this project - probably not a good idea to copy this elsewhere
        if not self.request.is_manager:
            return

        if self.suffixes and not getattr(self.suffixes[-1], 'editbar', True):
            return

        if isinstance(self.model, MissionReportCollection):
            return [
                Link(
                    _("Vehicles"), self.request.class_link(
                        MissionReportVehicleCollection
                    ), attrs={'class': 'vehicles'}
                ),
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Mission Report"),
                            url=self.request.link(
                                self.model,
                                name='+new'
                            ),
                            attrs={'class': 'new-report'}
                        )
                    ]
                ),
            ]

        if isinstance(self.model, MissionReportVehicleCollection):
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Vehicle"),
                            url=self.request.link(
                                self.model,
                                name='+new'
                            ),
                            attrs={'class': 'new-vehicle'}
                        )
                    ]
                ),
            ]

        if isinstance(self.model, MissionReport):
            return [
                Link(
                    _("Images"),
                    self.request.link(self.model, name='images'),
                    attrs={'class': 'upload-images'}
                ),
                Link(
                    _("Edit"),
                    self.request.link(self.model, name='edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    _("Delete"),
                    self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                "Do you really want to delete "
                                "this mission report?"
                            ),
                            _("This cannot be undone."),
                            _("Delete mission report"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                MissionReportCollection
                            )
                        )
                    )
                )
            ]

        if isinstance(self.model, MissionReportVehicle):
            if self.model.uses:
                return [
                    Link(
                        _("Delete"),
                        '#',
                        attrs={'class': 'delete-link'},
                        traits=(
                            Block(
                                _("This vehicle can't be deleted."),
                                _(
                                    "There are mission reports associated "
                                    "with this vehicle."
                                ),
                                _("Cancel")
                            ),
                        )
                    )
                ]
            else:
                return [
                    Link(
                        _("Delete"),
                        self.csrf_protected_url(
                            self.request.link(self.model)
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(
                                _(
                                    "Do you really want to delete "
                                    "this vehicle?"
                                ),
                                _("This cannot be undone."),
                                _("Delete vehicle"),
                                _("Cancel")
                            ),
                            Intercooler(
                                request_method='DELETE',
                                redirect_after=self.request.class_link(
                                    MissionReportVehicleCollection
                                )
                            )
                        )
                    )
                ]
