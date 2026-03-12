""" The manage screen views. """
from __future__ import annotations

from morepath import redirect
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ScreenCollection
from onegov.election_day.forms import ScreenForm
from onegov.election_day.layouts import ManageScreensLayout
from onegov.election_day.models import Screen


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.forms import EmptyForm
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.manage_html(
    model=ScreenCollection,
    template='manage/screens.pt'
)
def view_screens(
    self: ScreenCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ View all screens as a list. """

    return {
        'layout': ManageScreensLayout(self, request),
        'title': _('Screens'),
        'screens': self.batch,
        'new_screen': request.link(self, 'new-screen'),
        'export': request.link(self, 'export'),
    }


@ElectionDayApp.csv_file(
    model=ScreenCollection,
    name='export',
    permission=Private
)
def export_screens(
    self: ScreenCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ Export all screens as a CSV file. """

    return {
        'data': self.export(),
        'name': 'screens'
    }


@ElectionDayApp.manage_form(
    model=ScreenCollection,
    name='new-screen',
    form=ScreenForm
)
def create_screen(
    self: ScreenCollection,
    request: ElectionDayRequest,
    form: ScreenForm
) -> RenderData | Response:
    """ Create a new screen. """

    layout = ManageScreensLayout(self, request)

    if form.submitted(request):
        screen = Screen()
        form.update_model(screen)
        self.add(screen)
        layout = ManageScreensLayout(screen, request)
        request.message(_('Screen added.'), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _('New screen'),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Screen,
    name='edit',
    form=ScreenForm
)
def edit_screen_item(
    self: Screen,
    request: ElectionDayRequest,
    form: ScreenForm
) -> RenderData | Response:
    """ Edit a screen. """

    layout = ManageScreensLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_('Screen modified.'), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': _(
            'Screen ${number}',
            mapping={'number': self.number}
        ),
        'subtitle': _('Edit screen'),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Screen,
    name='delete'
)
def delete_screen(
    self: Screen,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:
    """ Delete a screen. """

    layout = ManageScreensLayout(self, request)

    if form.submitted(request):
        screens = ScreenCollection(request.session)
        screens.delete(self)
        request.message(_('Screen deleted.'), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.number
            }
        ),
        'layout': layout,
        'form': form,
        'title': _(
            'Screen ${number}',
            mapping={'number': self.number}
        ),
        'subtitle': _('Delete screen'),
        'button_text': _('Delete screen'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
