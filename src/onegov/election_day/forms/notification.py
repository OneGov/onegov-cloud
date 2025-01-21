from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.election_day.request import ElectionDayRequest
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session


class TriggerNotificationForm(Form):

    request: ElectionDayRequest

    notifications = MultiCheckboxField(
        label=_('Notifications'),
        choices=[],
        validators=[
            InputRequired()
        ],
        default=['email', 'sms', 'webhooks']
    )

    def on_request(self) -> None:
        """ Adjusts the form to the given principal. """

        principal = self.request.app.principal

        self.notifications.choices = []
        if principal.email_notification:
            self.notifications.choices.append(('email', _('Email')))
        if principal.sms_notification:
            self.notifications.choices.append(('sms', _('SMS')))
        if principal.webhooks:
            self.notifications.choices.append(('webhooks', _('Webhooks')))


class TriggerNotificationsForm(TriggerNotificationForm):

    votes = MultiCheckboxField(
        label=_('Votes'),
        choices=[],
    )

    election_compounds = MultiCheckboxField(
        label=_('Compounds of elections'),
        choices=[],
    )

    elections = MultiCheckboxField(
        label=_('Elections'),
        choices=[],
    )

    def ensure_items_selected(self) -> bool:
        if (
            not self.votes.data
            and not self.elections.data
            and not self.election_compounds.data
        ):
            message = _('Select at least one election or vote.')
            assert isinstance(self.votes.errors, list)
            self.votes.errors.append(message)
            assert isinstance(self.elections.errors, list)
            self.elections.errors.append(message)
            return False
        return True

    def latest_date(self, session: Session) -> date | None:
        query = session.query(Election.date)
        row = query.order_by(Election.date.desc()).first()
        latest_election = row[0] if row else None

        query = session.query(Vote.date)
        row = query.order_by(Vote.date.desc()).first()
        latest_vote = row[0] if row else None

        if latest_election and latest_vote:
            return max((latest_election, latest_vote))
        return latest_election or latest_vote

    def available_elections(self, session: Session) -> Query[Election]:
        query = session.query(Election)
        query = query.order_by(Election.shortcode)
        query = query.filter(Election.date == self.latest_date(session))
        return query

    def available_election_compounds(
        self,
        session: Session
    ) -> Query[ElectionCompound]:

        query = session.query(ElectionCompound)
        query = query.order_by(ElectionCompound.shortcode)
        query = query.filter(
            ElectionCompound.date == self.latest_date(session)
        )
        return query

    def available_votes(self, session: Session) -> Query[Vote]:
        query = session.query(Vote)
        query = query.order_by(Vote.shortcode)
        query = query.filter(Vote.date == self.latest_date(session))
        return query

    def election_models(self, session: Session) -> list[Election]:
        if not self.elections.data:
            return []

        query = session.query(Election)
        query = query.filter(Election.id.in_(self.elections.data))
        query = query.order_by(Election.shortcode)
        return query.all()

    def election_compound_models(
        self,
        session: Session
    ) -> list[ElectionCompound]:

        if not self.election_compounds.data:
            return []

        query = session.query(ElectionCompound)
        query = query.filter(
            ElectionCompound.id.in_(self.election_compounds.data)
        )
        query = query.order_by(ElectionCompound.shortcode)
        return query.all()

    def vote_models(self, session: Session) -> list[Vote]:
        if not self.votes.data:
            return []

        query = session.query(Vote)
        query = query.filter(Vote.id.in_(self.votes.data))
        query = query.order_by(Vote.shortcode)
        return query.all()

    def on_request(self) -> None:
        """ Adjusts the form to the given principal. """

        super().on_request()

        session = self.request.session
        self.elections.choices = [
            (election.id, election.title or election.id)
            for election in self.available_elections(session)
        ]
        self.election_compounds.choices = [
            (compound.id, compound.title or compound.id)
            for compound in self.available_election_compounds(session)
        ]
        self.votes.choices = [
            (vote.id, vote.title or vote.id)
            for vote in self.available_votes(session)
        ]
