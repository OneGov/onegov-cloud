from __future__ import annotations

from datetime import date
from itertools import zip_longest
from markupsafe import Markup
from onegov.core.templates import render_macro
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.org import _
from onegov.org.models import PoliticalBusiness
from onegov.org.models import PoliticalBusinessParticipation
from onegov.org.models import PoliticalBusinessParticipationCollection
from onegov.org.models import RISParliamentarian
from onegov.org.models import RISParliamentaryGroup
from onegov.org.models.political_business import (
    POLITICAL_BUSINESS_TYPE,
    POLITICAL_BUSINESS_STATUS
)
from wtforms.fields import DateField
from wtforms.fields import FormField
from wtforms.fields import FieldList
from wtforms.fields import StringField
from wtforms.fields import SelectField
from wtforms.utils import unset_value
from wtforms.validators import InputRequired
from wtforms.validators import Optional


from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Sequence
    from wtforms.fields.choices import _Choice
    from wtforms.fields.core import _Filter
    from wtforms.meta import _MultiDictLikeWithGetlist


class ParticipantForm(Form):
    parliamentarian_id = SelectField(
        label='',
        choices=(),
        render_kw={
            'class_': 'participant-select',
            'data-placeholder': _('Select additional participant'),
            'data-no_results_text': _('No results match'),
        }
    )
    participant_type = SelectField(
        label=_('Role'),
        depends_on=('parliamentarian_id', '!'),
        render_kw={'class_': 'indent-form-field'},
        choices=[
            ('', ''),
            ('First signatory', _('First signatory')),
            ('Co-signatory', _('Co-signatory')),
        ]
    )


if TYPE_CHECKING:
    FieldBase = FieldList[FormField[ParticipantForm]]
else:
    FieldBase = FieldList


def participant_widget(field: FieldBase, **kwargs: Any) -> Markup:
    field.meta.request.include('participant-select')
    return Markup('<br>').join(
        Markup('<div id="{}">{}</div>').format(f.id, f())
        for f in field
    )


class BusinessParticipationField(FieldBase):

    def process(
        self,
        formdata: _MultiDictLikeWithGetlist | None,
        data: Any = unset_value,
        extra_filters: Sequence[_Filter] | None = None
    ) -> None:

        # FIXME: I'm not quite sure why we need to do this
        #        but it looks like the last_index gets updated
        #        to 0 by something, so we start counting at 1
        #        instead of 0, which breaks the field
        self.last_index = -1
        super().process(formdata, data, extra_filters)

        # always have an empty extra entry
        if (
            formdata is None
            and self[-1].form.parliamentarian_id.data is not None
        ):
            self.append_entry()

    def populate_obj(self, obj: PoliticalBusiness, name: str) -> None:  # type: ignore[override]
        assert name == 'participants'
        collection = PoliticalBusinessParticipationCollection(
            self.meta.request.session
        )
        participants = obj.participants
        output: list[PoliticalBusinessParticipation] = []
        for field, participant in zip_longest(self.entries, participants):
            if field is None:
                # this generally shouldn't happen, but we should
                # guard against it anyways, since it can happen
                # if people manually call pop_entry()
                break

            participant_id = field.form.parliamentarian_id.data
            participant_type = field.form.participant_type.data
            if not participant_id:
                if participant is not None:
                    collection.delete(participant)
                continue
            elif participant is None:
                participant = collection.add(
                    political_business_id=obj.id,
                    parliamentarian_id=participant_id,
                    participant_type=participant_type
                )
            elif str(participant.id) != participant_id:
                collection.delete(participant)
                participant = collection.add(
                    political_business_id=obj.id,
                    parliamentarian_id=participant_id,
                    participant_type=participant_type
                )
            else:
                participant.participant_type = participant_type

            output.append(participant)

        setattr(obj, name, output)


class PoliticalBusinessForm(Form):
    title = StringField(
        label=_('Title'),
        validators=[InputRequired()],
    )

    number = StringField(
        label=_('Number'),
        validators=[Optional()],
    )

    political_business_type = TranslatedSelectField(
        label=_('Type'),
        choices=POLITICAL_BUSINESS_TYPE.items(),
        validators=[InputRequired()],
        choices_sorted=True,
    )

    status = TranslatedSelectField(
        label=_('Business Status'),
        choices=POLITICAL_BUSINESS_STATUS.items(),
        validators=[InputRequired()],
        choices_sorted=True,
        default='-',
    )

    entry_date = DateField(
        label=_('Submission/publication date'),
        validators=[InputRequired()],
        default=date.today,
    )

    # FIXME : make multiple groups possible ChosenSelectMultipleField
    parliamentary_group_id = ChosenSelectField(
        label=_('Parliamentary Group'),
        validators=[Optional()],
        choices=[],
    )

    participants = BusinessParticipationField(
        FormField(
            ParticipantForm,
            widget=lambda field, **kw: Markup('').join(
                Markup('<div><label>{}</label></div>').format(render_macro(
                    field.meta.request.template_loader.macros['field'],
                    field.meta.request,
                    {
                        'field': f,
                        # FIXME: only used for rendering descriptions
                        #        we should probably move this logic
                        #        into a template macro or a method on
                        #        CoreRequest, this doesn't really need
                        #        to be part of Form, we could also move
                        #        it to the form meta and access it
                        #        through the field instead
                        'form': field.meta.request.get_form(
                            Form, csrf_support=False
                        )
                    }
                )) for f in field
            )
        ),
        label=_('Participations'),
        fieldset=_('Participations'),
        # we always have at least one empty entry
        min_entries=1,
        widget=participant_widget,
    )

    def on_request(self) -> None:
        selectable_participants = (
            self.request.session.query(RISParliamentarian)
            .filter(RISParliamentarian.active)
            .order_by(
                RISParliamentarian.last_name,
                RISParliamentarian.first_name
            )
        )
        if selectable_participants:
            selected = {
                participant.parliamentarian_id: participant.participant_type
                for participant in self.model.participants
            } if isinstance(self.model, PoliticalBusiness) else {}
            choices: list[_Choice] = [
                (
                    str(participant.id),
                    participant.title,
                    {'data-role': selected.get(participant.id) or ''}
                )
                for participant in selectable_participants
            ]
            choices.insert(0, ('', ''))

            # NOTE: Ensures translations work in FormField
            for field in self.participants:
                field.form.meta = self.meta

                field.form.parliamentarian_id.meta = self.meta
                field.form.parliamentarian_id.choices = choices
                render_kw = field.form.parliamentarian_id.render_kw
                render_kw['data-placeholder'] = self.request.translate(
                    render_kw['data-placeholder'])
                render_kw['data-no_results_text'] = self.request.translate(
                    render_kw['data-no_results_text'])

                field.form.participant_type.meta = self.meta
                field.form.participant_type.choices = [  # type: ignore[misc]
                    (value, self.request.translate(label) if label else label)
                    for value, label in field.form.participant_type.choices
                ]
        else:
            self.delete_field('participants')

        self.political_business_type.choices.insert(0, ('', '-'))  # type:ignore[union-attr]
        self.status.choices.insert(0, ('', '-'))  # type:ignore[union-attr]

        groups = (
            self.request.session.query(RISParliamentaryGroup)
            .filter(RISParliamentaryGroup.end == None)
            .order_by(RISParliamentaryGroup.name)
            .all()
        )
        self.parliamentary_group_id.choices = [
            (str(g.id.hex), g.name) for g in groups
        ]
        self.parliamentary_group_id.choices.insert(0, ('', '-'))

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result.pop('participants', None)
        result.pop('files', None)
        result['parliamentary_group_id'] = (
            result.get('parliamentary_group_id') or None)
        return result

    def populate_obj(  # type: ignore[override]
        self,
        obj: PoliticalBusiness,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        super().populate_obj(
            obj,
            exclude={
                'parliamentary_group_id',
                *(exclude or ())
            },
            include=include
        )

        obj.parliamentary_group_id = self.parliamentary_group_id.data or None
