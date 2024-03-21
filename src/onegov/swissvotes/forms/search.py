from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.fields import PolicyAreaField
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models import PolicyAreaDefinition
from onegov.swissvotes.models.vote import SwissVote
from wtforms.fields import DateField
from wtforms.fields import HiddenField
from wtforms.fields import RadioField
from wtforms.fields import StringField


class SearchForm(Form):

    term = StringField(
        label=_("Text Search"),
        render_kw={'size': 6, 'clear': False},
    )

    full_text = RadioField(
        label=_("Full-text"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        default=1,
        coerce=bool,
        render_kw={'size': 6},
        description=_(
            "Select «No» if you want to limit the search to title, keyword, "
            "vote number, and procedure number only. If you select «Yes», the "
            "full-text search also includes the following documents, in their "
            "available language versions: brief description by Swissvotes, "
            "text subject to vote, preliminary examination, decree on "
            "success, Federal Council dispatch, parliamentary debate, "
            "documents from the voting campaign. In contrast to the "
            "abovementioned documents, the following documents are not "
            "included in the search because they invariably contain "
            "information on all the subjects that were put to the vote on "
            "that day : explanatory brochure, analysis of the advertising "
            "campaign, analysis of the media coverage, decree on voting "
            "result, reports on the post-vote poll."
        ),
    )

    policy_area = PolicyAreaField(
        label=_("Policy area"),
        choices=[],
        render_kw={'size': 6, 'clear': True}
    )

    legal_form = MultiCheckboxField(
        label=_("Legal form"),
        coerce=int,
        choices=[],
        render_kw={'size': 6, 'clear': False}
    )

    result = MultiCheckboxField(
        label=_("Voting result"),
        coerce=int,
        choices=[],
        render_kw={'size': 6}
    )

    from_date = DateField(
        label=_("From date"),
        render_kw={'size': 6, 'clear': False}
    )

    to_date = DateField(
        label=_("To date"),
        render_kw={'size': 6}
    )

    position_federal_council = MultiCheckboxField(
        label=_("Position of the Federal Council"),
        fieldset=_("Other Filters"),
        choices=[],
        coerce=int,
        render_kw={'size': 3, 'clear': False}
    )

    position_national_council = MultiCheckboxField(
        label=_("Position of the National Council"),
        fieldset=_("Other Filters"),
        choices=[],
        coerce=int,
        render_kw={'size': 3, 'clear': False}
    )

    position_council_of_states = MultiCheckboxField(
        label=_("Position of the Council of States"),
        fieldset=_("Other Filters"),
        choices=[],
        coerce=int,
        render_kw={'size': 3}
    )

    sort_by = HiddenField()
    sort_order = HiddenField()

    def populate_policy_area(self):
        votes = SwissVoteCollection(self.request.app)
        available = votes.available_descriptors

        def serialize(item):
            children = [serialize(child) for child in item.children]
            children = [child for child in children if child]
            if not item.value:
                return children
            value = PolicyArea(item.path).descriptor_decimal
            if not children and not any((value in s for s in available)):
                return None
            return {
                "label": self.request.translate(item.label),
                "value": '.'.join([str(x) for x in item.path]),
                "children": children
            }

        self.policy_area.tree = serialize(PolicyAreaDefinition.all())

    def populate_choice(self, name, remove=None, add_none=False):
        remove = remove or []
        field = getattr(self, name)
        field.choices = [
            (code, text) for code, text in SwissVote.codes(name).items()
            if code not in remove
        ]
        if add_none:
            field.choices.append((-1, _("Missing")))

    def on_request(self):
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')
        self.populate_choice('legal_form')
        self.populate_choice('result', [3, 8, 9])
        self.populate_choice('position_federal_council', [8, 9], True)
        self.populate_choice('position_national_council', [8, 9])
        self.populate_choice('position_council_of_states', [8, 9])
        self.populate_policy_area()

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def apply_model(self, model):
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.legal_form.data = model.legal_form
        self.result.data = model.result
        self.policy_area.data = model.policy_area
        self.term.data = model.term
        self.full_text.data = 0 if model.full_text is False else 1
        self.position_federal_council.data = model.position_federal_council
        self.position_national_council.data = model.position_national_council
        self.position_council_of_states.data = model.position_council_of_states
        self.sort_by.data = model.sort_by
        self.sort_order.data = model.sort_order

        # default unselected checkboxes to all choices
        self.select_all('legal_form')
        self.select_all('result')
        self.select_all('position_federal_council')
        self.select_all('position_national_council')
        self.select_all('position_council_of_states')


class AttachmentsSearchForm(Form):

    term = StringField(
        label=_("Text Search"),
        render_kw={'size': 12, 'clear': True},
    )

    def on_request(self):
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def apply_model(self, model):
        self.term.data = model.term
