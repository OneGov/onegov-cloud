from __future__ import annotations

from morepath import redirect
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.collections import VoteCollection
from onegov.election_day.forms import ClearResultsForm
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.forms import VoteForm
from onegov.election_day.layouts import MailLayout
from onegov.election_day.layouts import ManageVotesLayout
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.forms import EmptyForm
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.manage_html(
    model=VoteCollection,
    template='manage/votes.pt',
)
def view_votes(
    self: VoteCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ View a list of all votes. """

    years = [
        (
            year if year else _('All'),
            year == self.year,
            request.link(self.for_year(year))
        )
        for year in [None, *self.get_years()]
    ]

    return {
        'layout': ManageVotesLayout(self, request),
        'title': _('Votes'),
        'groups': groupbylist(self.batch, key=lambda vote: vote.date),
        'new_vote': request.link(self, 'new-vote'),
        'redirect_filters': {_('Year'): years},
    }


@ElectionDayApp.manage_form(
    model=VoteCollection,
    name='new-vote',
    form=VoteForm
)
def create_vote(
    self: VoteCollection,
    request: ElectionDayRequest,
    form: VoteForm
) -> RenderData | Response:
    """ Create a new vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    form.delete_field('id')
    form.delete_field('id_hint')

    if form.submitted(request):
        vote = Vote.get_polymorphic_class(form.type.data, Vote)()
        form.update_model(vote)
        archive.add(vote, request)
        request.message(_('Vote added.'), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _('New vote'),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='edit',
    form=VoteForm
)
def edit_vote(
    self: Vote,
    request: ElectionDayRequest,
    form: VoteForm
) -> RenderData | Response:
    """ Edit an existing vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        old = request.link(self)
        form.update_model(self)
        archive.update(self, request, old=old)
        request.message(_('Vote modified.'), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _('Edit vote'),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='clear',
    form=ClearResultsForm
)
def clear_vote(
    self: Vote,
    request: ElectionDayRequest,
    form: ClearResultsForm
) -> RenderData | Response:
    """ Clear the results of a vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.clear_results(self, request, form.clear_all.data)
        request.message(_('Results deleted.'), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to clear all results of "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _('Clear results'),
        'button_text': _('Clear results'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='clear-media'
)
def clear_election_media(
    self: Vote,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:
    """ Deletes alls SVGs and PDFs of this vote. """

    layout = ManageVotesLayout(self, request)

    if form.submitted(request):
        count = layout.clear_media()
        request.message(
            _('${count} files deleted.', mapping={'count': count}),
            'success'
        )
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    return {
        'callout': _(
            'Deletes all automatically generated media items (PDFs and SVG '
            'images). They are regenerated in the background and are '
            'available again in a few minutes.'
        ),
        'message': _(
            'Do you really want to clear all media of "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _('Clear media'),
        'button_text': _('Clear media'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='delete'
)
def delete_vote(
    self: Vote,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:
    """ Delete an existing vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.delete(self, request)
        request.message(_('Vote deleted.'), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _('Delete vote'),
        'button_text': _('Delete vote'),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='trigger',
    form=TriggerNotificationForm,
    template='manage/trigger_notification.pt'
)
def trigger_vote(
    self: Vote,
    request: ElectionDayRequest,
    form: TriggerNotificationForm
) -> RenderData | Response:
    """ Trigger the notifications related to a vote. """

    session = request.session
    notifications = NotificationCollection(session)
    layout = ManageVotesLayout(self, request)

    if form.submitted(request):
        assert form.notifications.data is not None
        notifications.trigger(request, self, form.notifications.data)
        request.message(_('Notifications triggered.'), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    callout = None
    message = ''
    title = _('Trigger notifications')
    button_class = 'primary'
    subject = MailLayout(None, request).subject(self)

    if notifications.by_model(self):
        callout = _(
            'There are no changes since the last time the notifications '
            'have been triggered!'
        )
        message = _(
            'Do you really want to retrigger the notfications?',
        )
        button_class = 'alert'

    return {
        'message': message,
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subject': subject,
        'subtitle': title,
        'callout': callout,
        'button_text': title,
        'button_class': button_class,
        'cancel': layout.manage_model_link,
        'last_notifications': notifications.by_model(self, False)
    }
