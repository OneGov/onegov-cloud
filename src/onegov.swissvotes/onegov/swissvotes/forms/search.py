from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.fields import PolicyAreaField
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models.policy_area import POLICY_AREA
from onegov.swissvotes.models.vote import LEGAL_FORM
from onegov.swissvotes.models.vote import RESULT
from wtforms.fields.html5 import DateField
from wtforms import HiddenField
from wtforms import StringField


class SearchForm(Form):

    from_date = DateField(
        label=_("From date")
    )

    to_date = DateField(
        label=_("To date")
    )

    legal_form = MultiCheckboxField(
        label=_("Legal form"),
        choices=list(LEGAL_FORM.items()),
        coerce=int
    )

    result = MultiCheckboxField(
        label=_("Voting result"),
        choices=list(RESULT.items()),
        coerce=int
    )

    policy_area = PolicyAreaField(
        label=_("Policy area"),
        choices=[]
    )

    term = StringField(
        label=_("Full-text search"),
    )

    sort_by = HiddenField()
    sort_order = HiddenField()

    def populate_policy_area(self):
        votes = SwissVoteCollection(self.request.app)
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

    def on_request(self):
        self.delete_field('csrf_token')
        self.populate_policy_area()

    def apply_model(self, model):
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.legal_form.data = model.legal_form
        self.result.data = model.result
        self.policy_area.data = model.policy_area
        self.term.data = model.term
        self.sort_by.data = model.sort_by
        self.sort_order.data = model.sort_order

        # default unselected checkboxes to all choices
        if not self.legal_form.data:
            self.legal_form.data = list(LEGAL_FORM.keys())
        if not self.result.data:
            self.result.data = list(RESULT.keys())
