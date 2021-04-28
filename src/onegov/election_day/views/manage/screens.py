""" The manage screen views. """

from morepath import redirect
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ScreenCollection
from onegov.election_day.forms import ScreenForm
from onegov.election_day.layouts import ManageScreensLayout
from onegov.election_day.models import Screen


@ElectionDayApp.manage_html(
    model=ScreenCollection,
    template='manage/screens.pt'
)
def view_screens(self, request):

    """ View all screens as a list. """

    return {
        'layout': ManageScreensLayout(self, request),
        'title': _('Screens'),
        'screens': self.batch,
        'new_screen': request.link(self, 'new-screen'),
    }


@ElectionDayApp.manage_form(
    model=ScreenCollection,
    name='new-screen',
    form=ScreenForm
)
def create_screen(self, request, form):

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
def edit_screen_item(self, request, form):

    """ Edit a screen. """

    layout = ManageScreensLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_('Screen modified.'), 'success')
        request.app.pages_cache.invalidate()
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': _(
            "Screen ${number}",
            mapping={'number': self.number}
        ),
        'subtitle': _('Edit screen'),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Screen,
    name='delete'
)
def delete_screen(self, request, form):

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
                'item': self.id
            }
        ),
        'layout': layout,
        'form': form,
        'title': _(
            "Screen ${number}",
            mapping={'number': self.number}
        ),
        'subtitle': _('Delete screen'),
        'button_text': _('Delete screen'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
