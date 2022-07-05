from onegov.ballot.models import Election
from onegov.ballot.models import ElectionCompound
from onegov.ballot.models import Vote
from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.validators import InputRequired


class TriggerNotificationForm(Form):

    notifications = MultiCheckboxField(
        label=_("Notifications"),
        choices=[],
        validators=[
            InputRequired()
        ],
        default=['email', 'sms', 'webhooks']
    )

    def on_request(self):
        """ Adjusts the form to the given principal. """

        principal = self.request.app.principal

        self.notifications.choices = []
        if principal.email_notification:
            self.notifications.choices.append(('email', _("Email")))
        if principal.sms_notification:
            self.notifications.choices.append(('sms', _("SMS")))
        if principal.webhooks:
            self.notifications.choices.append(('webhooks', _("Webhooks")))


class TriggerNotificationsForm(TriggerNotificationForm):

    votes = MultiCheckboxField(
        label=_("Votes"),
        choices=[],
    )

    election_compounds = MultiCheckboxField(
        label=_("Compounds of elections"),
        choices=[],
    )

    elections = MultiCheckboxField(
        label=_("Elections"),
        choices=[],
    )

    def ensure_items_selected(self):
        if (
            not self.votes.data
            and not self.elections.data
            and not self.election_compounds.data
        ):
            message = _("Select at least one election or vote.")
            self.votes.errors.append(message)
            self.elections.errors.append(message)
            return False

    def latest_date(self, session):
        query = session.query(Election.date)
        query = query.order_by(Election.date.desc()).first()
        latest_election = query[0] if query else None

        query = session.query(Vote.date)
        query = query.order_by(Vote.date.desc()).first()
        latest_vote = query[0] if query else None

        if latest_election and latest_vote:
            return max((latest_election, latest_vote))
        return latest_election or latest_vote

    def available_elections(self, session):
        query = session.query(Election)
        query = query.order_by(Election.shortcode)
        query = query.filter(Election.date == self.latest_date(session))
        return query

    def available_election_compounds(self, session):
        query = session.query(ElectionCompound)
        query = query.order_by(ElectionCompound.shortcode)
        query = query.filter(
            ElectionCompound.date == self.latest_date(session)
        )
        return query

    def available_votes(self, session):
        query = session.query(Vote)
        query = query.order_by(Vote.shortcode)
        query = query.filter(Vote.date == self.latest_date(session))
        return query

    def election_models(self, session):
        if not self.elections.data:
            return []

        query = session.query(Election)
        query = query.filter(Election.id.in_(self.elections.data))
        query = query.order_by(Election.shortcode)
        return query.all()

    def election_compound_models(self, session):
        if not self.election_compounds.data:
            return []

        query = session.query(ElectionCompound)
        query = query.filter(
            ElectionCompound.id.in_(self.election_compounds.data)
        )
        query = query.order_by(ElectionCompound.shortcode)
        return query.all()

    def vote_models(self, session):
        if not self.votes.data:
            return []

        query = session.query(Vote)
        query = query.filter(Vote.id.in_(self.votes.data))
        query = query.order_by(Vote.shortcode)
        return query.all()

    def on_request(self):
        """ Adjusts the form to the given principal. """

        super(TriggerNotificationsForm, self).on_request()

        session = self.request.session
        self.elections.choices = [
            (election.id, election.title)
            for election in self.available_elections(session)
        ]
        self.election_compounds.choices = [
            (compound.id, compound.title)
            for compound in self.available_election_compounds(session)
        ]
        self.votes.choices = [
            (vote.id, vote.title)
            for vote in self.available_votes(session)
        ]
