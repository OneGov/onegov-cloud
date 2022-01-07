from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.fields.html5 import DateField
from wtforms import StringField
from onegov.election_day import _


class ArchiveSearchForm(Form):

    term = StringField(
        label=_("Term"),
        render_kw={'size': 4, 'clear': False},
        description=_(
            "Searches the title of the election/vote. "
            "Use Wilcards (*) to find more results, e.g Nationalrat*."
        ),
    )

    from_date = DateField(
        label=_("From date"),
        render_kw={'size': 4, 'clear': False}
    )

    to_date = DateField(
        label=_("To date"),
        render_kw={'size': 4, 'clear': True}
    )

    domains = MultiCheckboxField(
        label=_("Domain"),
        render_kw={'size': 4, 'clear': False},
        choices=[]
    )

    def on_request(self):
        # Removes csrf token from query params, it's public page
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def apply_model(self, model):
        self.term.data = model.term
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.domains.data = model.domains

        self.select_all('domains')


class ArchiveSearchFormVote(ArchiveSearchForm):

    answers = MultiCheckboxField(
        label=_("Voting result"),
        choices=(
            ('accepted', _("Accepted")),
            ('rejected', _("Rejected")),
            ('counter_proposal', _("Counter Proposal"))
        ),
        render_kw={'size': 4, 'clear': True}
    )

    def on_request(self):
        super().on_request()
        principal = self.request.app.principal
        self.domains.choices = principal.domains_vote.items()

    def apply_model(self, model):
        super().apply_model(model)
        self.answers.data = model.answers
        self.select_all('answers')


class ArchiveSearchFormElection(ArchiveSearchForm):

    def on_request(self):
        super().on_request()
        principal = self.request.app.principal
        domains = principal.domains_election.copy()
        if 'region' in domains:
            domains['region'] = _('Regional')
        if 'district' in domains:
            domains['district'] = _('Regional')
        if 'region' in domains and 'district' in domains:
            del domains['district']
        self.domains.choices = domains.items()
