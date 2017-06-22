from onegov.activity import Period, PeriodCollection
from onegov.core.security import Secret
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.forms import PeriodForm
from onegov.feriennet.layout import PeriodCollectionLayout
from onegov.feriennet.layout import PeriodFormLayout
from onegov.org.new_elements import Link, Confirm, Intercooler, Block
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError


@FeriennetApp.html(
    model=PeriodCollection,
    template='periods.pt',
    permission=Secret)
def view_periods(self, request):

    layout = PeriodCollectionLayout(self, request)

    def links(period):
        if period.active:
            yield Link(
                text=_("Deactivate"),
                url=layout.csrf_protected_url(
                    request.link(period, name='deaktivieren')
                ),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to deactivate "${title}"?',
                            mapping={'title': period.title}
                        ),
                        _("This will hide all associated occasions"),
                        _("Deactivate Period")
                    ),
                    Intercooler(
                        request_method="POST",
                        redirect_after=request.link(self)
                    ),
                )
            )
        elif not period.archived:
            yield Link(
                text=_("Activate"),
                url=layout.csrf_protected_url(
                    request.link(period, name='aktivieren')
                ),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to activate "${title}"?',
                            mapping={'title': period.title}
                        ),
                        _(
                            "This will deactivate the currently active "
                            "period. All associated occasions will be made "
                            "public"
                        ),
                        _("Activate Period")
                    ),
                    Intercooler(
                        request_method="POST",
                        redirect_after=request.link(self)
                    ),
                )
            )

        yield Link(_("Edit"), request.link(period, 'bearbeiten'))

        if not period.archived:
            if period.confirmed and period.finalized:
                yield Link(
                    text=_("Archive"),
                    url=layout.csrf_protected_url(
                        request.link(period, name='archivieren')
                    ),
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to archive "${title}"?',
                                mapping={'title': period.title}
                            ),
                            _(
                                "This will archive all activities which do "
                                "not already have an occasion in a future "
                                "period. To publish archived activities again "
                                "a new publication request needs to be filed."
                            ),
                            _("Archive Period")
                        ),
                        Intercooler(
                            request_method="POST",
                            redirect_after=request.link(self)
                        ),
                    )
                )
            else:
                yield Link(
                    text=_("Archive"),
                    url='#',
                    traits=(
                        Block(
                            _(
                                '"${title}" cannot be archived yet',
                                mapping={'title': period.title}
                            ),
                            _(
                                "A period can only be archived once the "
                                "bookings have been made and the bills have "
                                "been compiled."
                            )
                        )
                    )
                )

        yield Link(
            text=_("Delete"),
            url=layout.csrf_protected_url(request.link(period)),
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete "${title}"?',
                        mapping={'title': period.title}
                    ),
                    _("This cannot be undone."),
                    _("Delete Period")
                ),
                Intercooler(
                    request_method="DELETE",
                    redirect_after=request.link(self)
                ),
            )
        )

    return {
        'layout': layout,
        'periods': self.query().order_by(desc(Period.execution_start)).all(),
        'title': _("Manage Periods"),
        'links': links
    }


@FeriennetApp.form(
    model=PeriodCollection,
    name='neu',
    form=PeriodForm,
    template='period_form.pt',
    permission=Secret)
def new_period(self, request, form):

    if form.submitted(request):
        period = self.add(
            title=form.title.data,
            prebooking=form.prebooking,
            execution=form.execution,
            minutes_between=form.minutes_between.data,
            active=False)

        form.populate_obj(period)
        request.success(_("The period was added successfully"))

        return request.redirect(request.link(self))

    return {
        'layout': PeriodFormLayout(self, request, _("New Period")),
        'form': form,
        'title': _("New Period")
    }


@FeriennetApp.form(
    model=Period,
    name='bearbeiten',
    form=PeriodForm,
    template='period_form.pt',
    permission=Secret)
def edit_period(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))

        return request.redirect(request.class_link(PeriodCollection))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': PeriodFormLayout(self, request, self.title),
        'form': form,
        'title': self.title
    }


@FeriennetApp.view(
    model=Period,
    request_method='DELETE',
    permission=Secret)
def delete_period(self, request):
    request.assert_valid_csrf_token()

    try:
        PeriodCollection(request.app.session()).delete(self)
    except IntegrityError:
        request.alert(
            _("The period could not be deleted as it is still in use"))
    else:
        request.success(
            _("The period was deleted successfully"))

    @request.after
    def redirect_intercooler(response):
        response.headers.add(
            'X-IC-Redirect', request.class_link(PeriodCollection))


@FeriennetApp.view(
    model=Period,
    request_method='POST',
    name='aktivieren',
    permission=Secret)
def activate_period(self, request):
    request.assert_valid_csrf_token()

    self.activate()
    request.success(_("The period was activated successfully"))

    @request.after
    def redirect_intercooler(response):
        response.headers.add(
            'X-IC-Redirect', request.class_link(PeriodCollection))


@FeriennetApp.view(
    model=Period,
    request_method='POST',
    name='deaktivieren',
    permission=Secret)
def deactivate_period(self, request):
    request.assert_valid_csrf_token()

    self.deactivate()
    request.success(_("The period was deactivated successfully"))

    @request.after
    def redirect_intercooler(response):
        response.headers.add(
            'X-IC-Redirect', request.class_link(PeriodCollection))


@FeriennetApp.view(
    model=Period,
    request_method='POST',
    name='archivieren',
    permission=Secret)
def archive_period(self, request):
    request.assert_valid_csrf_token()

    self.archive()
    request.success(_("The period was archived successfully"))

    @request.after
    def redirect_intercooler(response):
        response.headers.add(
            'X-IC-Redirect', request.class_link(PeriodCollection))
