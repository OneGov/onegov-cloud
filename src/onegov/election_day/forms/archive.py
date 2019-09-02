from onegov.election_day.models import ArchivedResult
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.fields.html5 import DateField
from wtforms import StringField
from onegov.election_day import _


class ArchiveSearchForm(Form):

    term = StringField(
        label=_("Text Retrieval"),
        render_kw={'size': 4, 'clear': True},
        description=_(
            "Searches the title of the election/vote. "
            "Use Wilcards (*) to find more results, e.g Nationalrat*."
        ),
    )

    from_date = DateField(
        label=_("From date"),
        render_kw={'size': 4}
    )

    to_date = DateField(
        label=_("To date"),
        render_kw={'size': 4, 'clear': False}
    )

    answers = MultiCheckboxField(
        label=_("Voting result"),
        choices=ArchivedResult.types_of_answers,
        render_kw={'size': 4}
    )

    # Is always hidden since item_type in url will filter the types
    types = MultiCheckboxField(
        label=_("Type"),
        render_kw={'size': 4, 'clear': False, 'hidden': True},
        choices=ArchivedResult.types_of_results,
        description=_(
            "Compound of elections field summarizes all related elections"
            " in one. To display all elections,"
            " uncheck 'Compound of Elections'")
    )

    domains = MultiCheckboxField(
        label=_("Domain"),
        render_kw={'size': 8, 'clear': False},
        choices=ArchivedResult.types_of_domains
    )

    def on_request(self):
        # Roves crf token from query params
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def toggle_hidden_fields(self, model):
        """ Hides answers field for election view and move the field to
        the right side with render_kw. """
        if model.item_type in ('election', 'election_compound'):
            self.answers.render_kw['hidden'] = True
            self.domains.render_kw['size'] = 12
        else:
            self.domains.render_kw['size'] = 8
            self.answers.render_kw['hidden'] = False

    def apply_model(self, model):

        self.term.data = model.term
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.answers.data = model.answers
        self.types.data = model.types
        self.domains.data = model.domains

        self.select_all('domains')
        self.select_all('types')
        self.select_all('answers')
        self.toggle_hidden_fields(model)
