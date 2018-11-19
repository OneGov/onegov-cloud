from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.fields import PolicyAreaField
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models.policy_area import POLICY_AREA
from onegov.swissvotes.models.vote import SwissVote
from wtforms import HiddenField
from wtforms import RadioField
from wtforms import StringField
from wtforms.fields.html5 import DateField


class SearchForm(Form):

    from_date = DateField(
        label=_("From date"),
        render_kw={'size': 6, 'clear': False}
    )

    to_date = DateField(
        label=_("To date"),
        render_kw={'size': 6}
    )

    legal_form = MultiCheckboxField(
        label=_("Legal form"),
        coerce=int,
        render_kw={'size': 6, 'clear': False}
    )

    result = MultiCheckboxField(
        label=_("Voting result"),
        coerce=int,
        render_kw={'size': 6}
    )

    policy_area = PolicyAreaField(
        label=_("Policy area"),
        choices=[],
        render_kw={'size': 6, 'clear': False}
    )

    term = StringField(
        label=_("Text Search"),
        render_kw={'size': 4, 'clear': False},
    )

    full_text = RadioField(
        label=_("Full Text"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        coerce=bool,
        render_kw={'size': 2}
    )

    position_federal_council = MultiCheckboxField(
        label=_("Position of the Federal Council"),
        fieldset=_("Other Filters"),
        coerce=int,
        render_kw={'size': 3, 'clear': False}
    )

    position_national_council = MultiCheckboxField(
        label=_("Position of the National Council"),
        fieldset=_("Other Filters"),
        coerce=int,
        render_kw={'size': 3, 'clear': False}
    )

    position_council_of_states = MultiCheckboxField(
        label=_("Position of the Council of States"),
        fieldset=_("Other Filters"),
        coerce=int,
        render_kw={'size': 3}
    )

    sort_by = HiddenField()
    sort_order = HiddenField()

    def populate_policy_area(self):
        votes = SwissVoteCollection(self.request.session)
        available = votes.available_descriptors

        def add_choice(value, label, level):
            self.policy_area.choices.append(
                (value, '‧' * level + ' ' + self.request.translate(label))
            )

        self.policy_area.choices = []
        for key_1, value_1 in POLICY_AREA.items():
            area = PolicyArea([key_1])
            if area.descriptor_decimal in available[0]:
                add_choice(area.value, value_1.get('label'), 0)
            for key_2, value_2 in value_1.get('children', {}).items():
                area = PolicyArea([key_1, key_2])
                if area.descriptor_decimal in available[1]:
                    add_choice(area.value, value_2.get('label'), 1)
                for key_3, value_3 in value_2.get('children', {}).items():
                    area = PolicyArea([key_1, key_2, key_3])
                    if area.descriptor_decimal in available[2]:
                        add_choice(area.value, value_3.get('label'), 2)

    def populate_choice(self, name, add_none=False):
        field = getattr(self, name)
        field.choices = list(SwissVote.codes(name).items())
        if add_none:
            field.choices.append((-1, _("Without / Unknown")))

    def on_request(self):
        self.delete_field('csrf_token')
        self.populate_choice('legal_form')
        self.populate_choice('result')
        self.populate_choice('position_federal_council', True)
        self.populate_choice('position_national_council', True)
        self.populate_choice('position_council_of_states', True)
        self.populate_policy_area()

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = next(zip(*field.choices))

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
