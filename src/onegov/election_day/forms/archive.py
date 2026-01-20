from __future__ import annotations

from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.fields import DateField
from wtforms.fields import StringField


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.collections import (
        SearchableArchivedResultCollection)
    from onegov.election_day.request import ElectionDayRequest


class ArchiveSearchForm(Form):

    request: ElectionDayRequest

    term = StringField(
        label=_('Term'),
        render_kw={'size': 4, 'clear': False},
        description=_(
            'Searches the title of the election/vote. '
            'Use Wildcards (`*`) to find more results, e.g `Nationalrat*`.'
        ),
    )

    from_date = DateField(
        label=_('From date'),
        render_kw={'size': 4, 'clear': False}
    )

    to_date = DateField(
        label=_('To date'),
        render_kw={'size': 4, 'clear': True}
    )

    domains = MultiCheckboxField(
        label=_('Domain'),
        render_kw={'size': 4, 'clear': False},
        choices=[]
    )

    def on_request(self) -> None:
        # Removes csrf token from query params, it's public page
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name: str) -> None:
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def apply_model(self, model: SearchableArchivedResultCollection) -> None:
        self.term.data = model.term
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.domains.data = model.domains

        self.select_all('domains')


class ArchiveSearchFormVote(ArchiveSearchForm):

    answers = MultiCheckboxField(
        label=_('Voting result'),
        choices=(
            ('accepted', _('Accepted')),
            ('rejected', _('Rejected')),
            ('counter_proposal', _('Counter Proposal'))
        ),
        render_kw={'size': 4, 'clear': True}
    )

    def on_request(self) -> None:
        super().on_request()
        principal = self.request.app.principal
        self.domains.choices = list(principal.domains_vote.items())

    def apply_model(self, model: SearchableArchivedResultCollection) -> None:
        super().apply_model(model)
        self.answers.data = model.answers
        self.select_all('answers')


class ArchiveSearchFormElection(ArchiveSearchForm):

    def on_request(self) -> None:
        super().on_request()
        domains = self.request.app.principal.domains_election

        self.domains.choices = [
            ('federation', _('Federal')),
            ('canton', _('Cantonal')),
        ]
        if 'region' in domains or 'region' in domains or 'none' in domains:
            self.domains.choices.append(('region', _('Regional')))
        if 'municipality' in domains:
            self.domains.choices.append(('municipality', _('Communal')))
