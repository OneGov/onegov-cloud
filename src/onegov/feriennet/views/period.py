from __future__ import annotations

from datetime import date
from onegov.activity import BookingPeriod, BookingPeriodCollection
from onegov.core.security import Secret
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.forms import PeriodForm
from onegov.feriennet.layout import PeriodCollectionLayout
from onegov.feriennet.layout import PeriodFormLayout
from onegov.core.elements import BackLink, Link, Confirm, Intercooler, Block
from onegov.feriennet.models import PeriodMessage
from sqlalchemy.exc import IntegrityError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from typing_extensions import TypeIs
    from webob import Response


@FeriennetApp.html(
    model=BookingPeriodCollection,
    template='periods.pt',
    permission=Secret)
def view_periods(
    self: BookingPeriodCollection,
    request: FeriennetRequest
) -> RenderData:

    layout = PeriodCollectionLayout(self, request)

    def links(period: BookingPeriod) -> Iterator[Link]:
        if period.active:
            yield Link(
                text=_('Deactivate'),
                url=layout.csrf_protected_url(
                    request.link(period, name='deactivate')
                ),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to deactivate "${title}"?',
                            mapping={'title': period.title}
                        ),
                        _('This will hide all associated occasions'),
                        _('Deactivate Period'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    ),
                )
            )
        elif not period.archived:
            yield Link(
                text=_('Activate'),
                url=layout.csrf_protected_url(
                    request.link(period, name='activate')
                ),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to activate "${title}"?',
                            mapping={'title': period.title}
                        ),
                        _(
                            'This will deactivate the currently active '
                            'period. All associated occasions will be made '
                            'public'
                        ),
                        _('Activate Period'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    ),
                )
            )

        yield Link(_('Edit'), request.link(period, 'edit'))

        if not period.archived:
            if period.confirmed and period.finalized or not period.finalizable:
                yield Link(
                    text=_('Archive'),
                    url=layout.csrf_protected_url(
                        request.link(period, name='archive')
                    ),
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to archive "${title}"?',
                                mapping={'title': period.title}
                            ),
                            _(
                                'This will archive all activities which do '
                                'not already have an occasion in a future '
                                'period. To publish archived activities again '
                                'a new publication request needs to be filed.'
                            ),
                            _('Archive Period'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='POST',
                            redirect_after=request.link(self)
                        ),
                    )
                )
            else:
                yield Link(
                    text=_('Archive'),
                    url='#',
                    traits=(
                        Block(
                            _(
                                '"${title}" cannot be archived yet',
                                mapping={'title': period.title}
                            ),
                            _(
                                'A period can only be archived once the '
                                'bookings have been made and the bills have '
                                'been compiled.'
                            ),
                            _('Cancel')
                        )
                    )
                )

        yield Link(
            text=_('Delete'),
            url=layout.csrf_protected_url(request.link(period)),
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete "${title}"?',
                        mapping={'title': period.title}
                    ),
                    _('This cannot be undone.'),
                    _('Delete Period'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.link(self)
                ),
            )
        )

    return {
        'layout': layout,
        'periods': self.query().order_by(
            BookingPeriod.execution_start.desc()).all(),
        'title': _('Manage Periods'),
        'links': links
    }


def is_date_range(
    range: tuple[date | None, date | None]
) -> TypeIs[tuple[date, date]]:
    return isinstance(range[0], date) and isinstance(range[1], date)


@FeriennetApp.form(
    model=BookingPeriodCollection,
    name='new',
    form=PeriodForm,
    template='period_form.pt',
    permission=Secret)
def new_period(
    self: BookingPeriodCollection,
    request: FeriennetRequest,
    form: PeriodForm
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        # NOTE: We can't put these assertions into the properties, because
        #       they need to be optional for the tests to pass
        if form.prebooking != (None, None):
            assert is_date_range(form.prebooking)
        assert is_date_range(form.booking)
        assert is_date_range(form.execution)
        period = self.add(
            title=form.title.data,
            prebooking=form.prebooking,
            booking=form.booking,
            execution=form.execution,
            minutes_between=form.minutes_between.data,
            confirmable=form.confirmable.data,
            finalizable=form.finalizable.data,
            active=False)

        form.populate_obj(period)
        request.success(_('The period was added successfully'))

        return request.redirect(request.link(self))

    layout = PeriodFormLayout(self, request, _('New Period'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'form': form,
        'title': _('New Period')
    }


@FeriennetApp.form(
    model=BookingPeriod,
    name='edit',
    form=PeriodForm,
    template='period_form.pt',
    permission=Secret)
def edit_period(
    self: BookingPeriod,
    request: FeriennetRequest,
    form: PeriodForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_('Your changes were saved'))

        return request.redirect(request.class_link(BookingPeriodCollection))

    elif not request.POST:
        form.process(obj=self)

    layout = PeriodFormLayout(self, request, self.title)
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(
        attrs={'class': 'cancel-link'},
    )

    return {
        'layout': layout,
        'form': form,
        'title': self.title
    }


@FeriennetApp.view(
    model=BookingPeriod,
    request_method='DELETE',
    permission=Secret)
def delete_period(self: BookingPeriod, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    try:
        BookingPeriodCollection(request.session).delete(self)
    except IntegrityError:
        request.alert(
            _('The period could not be deleted as it is still in use'))
    else:
        PeriodMessage.create(self, request, 'deleted')
        request.success(
            _('The period was deleted successfully'))

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add(
            'X-IC-Redirect', request.class_link(BookingPeriodCollection))


@FeriennetApp.view(
    model=BookingPeriod,
    request_method='POST',
    name='activate',
    permission=Secret)
def activate_period(self: BookingPeriod, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    self.activate()
    PeriodMessage.create(self, request, 'activated')
    request.success(_('The period was activated successfully'))

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add(
            'X-IC-Redirect', request.class_link(BookingPeriodCollection))


@FeriennetApp.view(
    model=BookingPeriod,
    request_method='POST',
    name='deactivate',
    permission=Secret)
def deactivate_period(self: BookingPeriod, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    self.deactivate()
    PeriodMessage.create(self, request, 'deactivated')
    request.success(_('The period was deactivated successfully'))

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add(
            'X-IC-Redirect', request.class_link(BookingPeriodCollection))


@FeriennetApp.view(
    model=BookingPeriod,
    request_method='POST',
    name='archive',
    permission=Secret)
def archive_period(self: BookingPeriod, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    self.archive()
    PeriodMessage.create(self, request, 'archived')
    request.success(_('The period was archived successfully'))

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add(
            'X-IC-Redirect', request.class_link(BookingPeriodCollection))
