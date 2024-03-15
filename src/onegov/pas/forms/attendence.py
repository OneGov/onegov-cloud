import datetime

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.pas import _
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.models.attendence import TYPES
from wtforms.fields import DateField
from wtforms.fields import FloatField
from wtforms.fields import RadioField
from wtforms.validators import InputRequired

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.pas.models import Attendence
    from typing import Any


class AttendenceForm(Form):

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    type = RadioField(
        label=_('Type'),
        choices=list(TYPES.items()),
        validators=[InputRequired()],
        default='plenary'
    )

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
        validators=[InputRequired()],
        depends_on=('type', '!plenary'),
    )

    def validate(self) -> bool:  # type:ignore[override]
        result = super().validate()

        if self.type.data != 'plenary' and not self.commission_id.data:
            assert isinstance(self.commission_id.errors, list)
            self.commission_id.errors.append(
                _("Please select a commission.")
            )
            result = False

        if (
            self.type.data != 'plenary'
            and self.commission_id.data
            and self.parliamentarian_id.data
        ):
            collection = ParliamentarianCollection(self.request.session)
            parliamentarian = collection.by_id(self.parliamentarian_id.data)
            if parliamentarian:
                commission_ids = [
                    str(membership.commission_id)
                    for membership in parliamentarian.commission_memberships
                ]
                if self.commission_id.data not in commission_ids:
                    assert isinstance(self.commission_id.errors, list)
                    self.commission_id.errors.append(
                        _("Parliamentarian is not in this commission.")
                    )
                    result = False
        return result

    def process_obj(self, obj: 'Attendence') -> None:  # type:ignore
        super().process_obj(obj)
        self.duration.data = obj.duration / 60

    def populate_obj(  # type: ignore[override]
        self,
        obj: 'Attendence',  # type: ignore[override]
        exclude: 'Collection[str] | None' = None,
        include: 'Collection[str] | None' = None
    ) -> None:
        super().populate_obj(obj, exclude, include)
        obj.commission_id = obj.commission_id or None
        obj.duration *= 60
        if obj.type == 'plenary':
            obj.commission_id = None

    def get_useful_data(self) -> dict[str, 'Any']:  # type:ignore[override]
        result = super().get_useful_data()
        result['commission_id'] = result.get('commission_id') or None
        if result.get('type', '') == 'plenary':
            result['commission_id'] = None
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(self.request.session).query()
        ]
        self.commission_id.choices = [
            (commission.id, commission.title)
            for commission
            in CommissionCollection(self.request.session).query()
        ]
        self.commission_id.choices.insert(0, ('', '-'))
