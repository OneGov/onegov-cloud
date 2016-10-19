from cached_property import cached_property
from onegov.activity import Activity, PeriodCollection
from onegov.feriennet import _
from onegov.feriennet import security
from onegov.feriennet.collections import VacationActivityCollection
from onegov.org.elements import Link, ConfirmLink, DeleteLink
from onegov.org.layout import DefaultLayout as BaseLayout


class DefaultLayout(BaseLayout):

    @property
    def is_owner(self):
        return security.is_owner(self.request.current_username, self.model)


class VacationActivityCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.link(self.model))
        )

    @cached_property
    def editbar_links(self):
        links = []

        if self.request.is_organiser:
            links.append(
                Link(
                    text=_("Submit Activity"),
                    url=self.request.link(self.model, name='neu'),
                    classes=('new-activity', )
                )
            )

        if self.request.is_admin:
            links.append(
                Link(
                    text=_("Manage Periods"),
                    url=self.request.class_link(PeriodCollection),
                    classes=('manage-periods', )
                )
            )

        return links


class VacationActivityFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.include_editor()
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.link(self.model)),
            Link(self.title, '#')
        )

    @cached_property
    def editbar_links(self):
        return None


class OccasionFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        assert isinstance(model, Activity)

        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model)),
            Link(self.title, '#')
        )

    @cached_property
    def editbar_links(self):
        return None


class VacationActivityLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(_("Activities"), self.request.class_link(
                VacationActivityCollection)),
            Link(self.model.title, self.request.link(self.model))
        )

    @cached_property
    def editbar_links(self):
        if self.request.is_admin or self.is_owner:
            links = []

            if self.model.state == 'preview':
                links.append(ConfirmLink(
                    text=_("Request Publication"),
                    url=self.request.link(self.model, name='beantragen'),
                    confirm=_("Do you really want to request publication?"),
                    extra_information=_("This cannot be undone."),
                    classes=('confirm', 'request-publication'),
                    yes_button_text=_("Request Publication")
                ))
                links.append(DeleteLink(
                    text=_("Discard Activity"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    confirm=_(
                        'Do you really want to discrd "${title}"?', mapping={
                            'title': self.model.title
                        }
                    ),
                    extra_information=_("This cannot be undone."),
                    redirect_after=self.request.class_link(
                        VacationActivityCollection
                    ),
                    yes_button_text=_("Discard Activity"),
                    classes=('confirm', 'delete-link')
                ))

            links.append(Link(
                text=_("Edit Activity"),
                url=self.request.link(self.model, name='bearbeiten'),
                classes=('edit-link', )
            ))

            if not PeriodCollection(self.app.session()).query().first():
                links.append(ConfirmLink(
                    text=_("New Occasion"),
                    url='#',
                    confirm=_("Occasions cannot be created yet"),
                    extra_information=_(
                        "There are no periods defined yet. At least one "
                        "period needs to be defined before occasions can "
                        "be created"
                    ),
                    classes=('confirm', 'new-occasion', )
                ))
            else:
                links.append(Link(
                    text=_("New Occasion"),
                    url=self.request.link(self.model, 'neue-durchfuehrung'),
                    classes=('new-occasion', )
                ))

            return links


class PeriodCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(_("Manage Periods"), '#')
        )

    @cached_property
    def editbar_links(self):
        return (
            Link(
                _("New Period"),
                self.request.link(self.model, 'neu'),
                classes=('new-period', )
            ),
        )


class PeriodFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return (
            Link(_("Homepage"), self.homepage_url),
            Link(
                _("Activities"),
                self.request.class_link(VacationActivityCollection)
            ),
            Link(
                _("Manage Periods"),
                self.request.class_link(PeriodCollection)
            ),
            Link(self.title, '#')
        )

    @cached_property
    def editbar_links(self):
        return None
