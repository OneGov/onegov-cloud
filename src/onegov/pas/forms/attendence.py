from __future__ import annotations

import datetime
from datetime import date

from wtforms import HiddenField

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import MultiCheckboxField
from onegov.pas import _
from onegov.pas.custom import get_current_settlement_run
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.custom import AttendenceCollection
from onegov.pas.models import PASCommissionMembership, SettlementRun
from onegov.pas.models.attendence import TYPES
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import FloatField
from wtforms.fields import RadioField
from wtforms.validators import InputRequired, ValidationError
from onegov.user import User

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.request import CoreRequest
    from onegov.pas.models import Attendence
    from typing import Any


class SettlementRunBoundMixin:

    if TYPE_CHECKING:
        # forward declaration of required attributes
        date: DateField
        request: CoreRequest

    def ensure_date(self) -> bool:
        if self.date.data:
            query = self.request.session.query(SettlementRun)
            query = query.filter(
                SettlementRun.active.is_(True),
                SettlementRun.start <= self.date.data,
            )
            if not query.first():
                assert isinstance(self.date.errors, list)
                self.date.errors.append(
                    _('No within an active settlement run.')
                )
                return False

        return True

    def set_default_value_to_settlement_run_start(self) -> None:
        if self.request.method == 'POST':
            return

        settlement_run = get_current_settlement_run(self.request.session)
        if settlement_run is not None:
            self.date.data = settlement_run.start


class AttendenceForm(Form, SettlementRunBoundMixin):

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

    abschluss = BooleanField(
        label=_('Abschluss'),
        description=_('Mark as completed/closed'),
    )

    def _can_edit_parliamentarian(
        self, parliamentarian_id: str
    ) -> tuple[bool, str | None]:
        """Check if current user can edit attendance for given parl ID.

        Returns: (can_edit, error_message)
        """
        if not hasattr(self.request.identity, 'role'):
            return (False, _('No role found for user.'))

        role = self.request.identity.role
        if role in ('admin', 'editor'):
            return (True, None)

        if role not in ('parliamentarian', 'commission_president'):
            return (False, _('Insufficient permissions.'))

        user = (
            self.request.session.query(User)
            .filter_by(username=self.request.identity.userid)
            .first()
        )
        if not user or not user.parliamentarian:  # type: ignore[attr-defined]
            return (False, _('User has no parliamentarian record.'))

        user_parl_id = str(user.parliamentarian.id)  # type: ignore[attr-defined]

        if parliamentarian_id == user_parl_id:
            return (True, None)

        if role == 'parliamentarian':
            return (False, _('You can only edit your own attendance.'))

        target_parl = PASParliamentarianCollection(self.request.app).by_id(
            parliamentarian_id
        )
        if not target_parl:
            return (False, _('Target parliamentarian not found.'))

        for pres_membership in user.parliamentarian.commission_memberships:  # type: ignore[attr-defined]
            if pres_membership.role == 'president' and (
                pres_membership.end is None
                or pres_membership.end >= date.today()
            ):
                for member_membership in target_parl.commission_memberships:
                    if (
                        member_membership.commission_id
                        == pres_membership.commission_id
                        and (
                            member_membership.end is None
                            or member_membership.end >= date.today()
                        )
                    ):
                        return (True, None)

        return (
            False,
            _(
                'You can only edit your own or your commission '
                "members' attendance."
            ),
        )

    def validate_parliamentarian_id(self, field: ChosenSelectField) -> None:
        """Prevent parliamentarians from editing other people's attendance."""
        can_edit, error_msg = self._can_edit_parliamentarian(field.data)
        if not can_edit and error_msg is not None:
            raise ValidationError(error_msg)

    def ensure_commission(self) -> bool:
        if (
            self.type.data
            and self.type.data != 'plenary'
            and self.commission_id.data
            and self.parliamentarian_id.data
        ):
            collection = PASParliamentarianCollection(self.request.app)
            parliamentarian = collection.by_id(self.parliamentarian_id.data)
            if parliamentarian:
                commission_ids = [
                    str(membership.commission_id)
                    for membership in parliamentarian.commission_memberships
                ]
                if self.commission_id.data not in commission_ids:
                    assert isinstance(self.commission_id.errors, list)
                    self.commission_id.errors.append(
                        _('Parliamentarian is not in this commission.')
                    )
                    return False

        return True

    def process_obj(self, obj: Attendence) -> None:  # type:ignore
        super().process_obj(obj)
        self.duration.data = obj.duration / 60

    def populate_obj(  # type: ignore[override]
        self,
        obj: Attendence,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        super().populate_obj(obj, exclude, include)
        obj.commission_id = obj.commission_id or None
        obj.duration *= 60
        if obj.type == 'plenary':
            obj.commission_id = None

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['commission_id'] = result.get('commission_id') or None
        if result.get('type', '') == 'plenary':
            result['commission_id'] = None
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.set_default_value_to_settlement_run_start()

        if not self.request.is_admin:  # type: ignore[attr-defined]
            self.type.choices = [
                (key, value)
                for key, value in TYPES.items()
                if key != 'plenary'
            ]
        else:
            self.type.choices = list(TYPES.items())

        if (
            hasattr(self.request.identity, 'role')
            and self.request.identity.role == 'parliamentarian'
        ):
            user = (
                self.request.session.query(User)
                .filter_by(username=self.request.identity.userid)
                .first()
            )
            if user and user.parliamentarian:  # type: ignore[attr-defined]
                self.parliamentarian_id.choices = [
                    (str(user.parliamentarian.id), user.parliamentarian.title)  # type: ignore[attr-defined]
                ]
            else:
                self.parliamentarian_id.choices = []
        elif (
            hasattr(self.request.identity, 'role')
            and self.request.identity.role == 'commission_president'
        ):
            user = (
                self.request.session.query(User)
                .filter_by(username=self.request.identity.userid)
                .first()
            )
            if user and user.parliamentarian:  # type: ignore[attr-defined]
                choices = [
                    (
                        str(user.parliamentarian.id),  # type: ignore[attr-defined]
                        user.parliamentarian.title,  # type: ignore[attr-defined]
                    )
                ]

                for membership in user.parliamentarian.commission_memberships:  # type: ignore[attr-defined]
                    if membership.role == 'president' and (
                        membership.end is None
                        or membership.end >= date.today()
                    ):
                        for member_membership in (
                            self.request.session.query(PASCommissionMembership)
                            .filter_by(commission_id=membership.commission_id)
                            .filter(
                                PASCommissionMembership.end.is_(None)
                                | (PASCommissionMembership.end >= date.today())
                            )
                        ):
                            if (
                                member_membership.parliamentarian_id
                                != user.parliamentarian.id  # type: ignore[attr-defined]
                            ):
                                member = member_membership.parliamentarian
                                choices.append((str(member.id), member.title))

                self.parliamentarian_id.choices = list(dict.fromkeys(choices))
            else:
                self.parliamentarian_id.choices = []
        else:
            self.parliamentarian_id.choices = [
                (str(parliamentarian.id), parliamentarian.title)
                for parliamentarian in PASParliamentarianCollection(
                    self.request.app
                ).query()
            ]

        # Filter commission choices based on user role
        if hasattr(
            self.request.identity, 'role'
        ) and self.request.identity.role in (
            'parliamentarian',
            'commission_president',
        ):
            user = (
                self.request.session.query(User)
                .filter_by(username=self.request.identity.userid)
                .first()
            )
            if user and user.parliamentarian:  # type: ignore[attr-defined]
                memberships = user.parliamentarian.commission_memberships  # type: ignore[attr-defined]
                commission_ids = [
                    membership.commission_id
                    for membership in memberships
                    if membership.end is None or membership.end >= date.today()
                ]
                self.commission_id.choices = [
                    (commission.id, commission.title)
                    for commission in PASCommissionCollection(
                        self.request.session
                    ).query()
                    if commission.id in commission_ids
                ]
            else:
                self.commission_id.choices = []
        else:
            self.commission_id.choices = [
                (commission.id, commission.title)
                for commission in PASCommissionCollection(
                    self.request.session
                ).query()
            ]
        self.commission_id.choices.insert(0, ('', '-'))


class AttendenceAddForm(AttendenceForm):

    def on_request(self) -> None:
        super().on_request()

        # Limit choices based on user role
        if (hasattr(self.request.identity, 'role')
            and self.request.identity.role == 'parliamentarian'):
            # Regular parliamentarians can only select themselves
            user = self.request.session.query(User).filter_by(
                username=self.request.identity.userid).first()
            if user and user.parliamentarian:  # type: ignore[attr-defined]
                self.parliamentarian_id.choices = [
                    (str(user.parliamentarian.id), user.parliamentarian.title)  # type: ignore[attr-defined]
                ]
            else:
                self.parliamentarian_id.choices = []
        elif (hasattr(self.request.identity, 'role')
              and self.request.identity.role == 'commission_president'):
            # Commission presidents can select themselves + commission members
            user = self.request.session.query(User).filter_by(
                username=self.request.identity.userid).first()
            if user and user.parliamentarian:  # type: ignore[attr-defined]
                choices = [(str(user.parliamentarian.id),  # type: ignore[attr-defined]
                           user.parliamentarian.title)]  # type: ignore[attr-defined]

                # Add commission members
                for membership in user.parliamentarian.commission_memberships:  # type: ignore[attr-defined]
                    if (membership.role == 'president'
                        and (membership.end is None
                             or membership.end >= date.today())):
                        # Get all members of this commission
                        for member_membership in (
                            self.request.session.query(PASCommissionMembership)
                            .filter_by(commission_id=membership.commission_id)
                            .filter(PASCommissionMembership.end.is_(None)
                                   | (PASCommissionMembership.end
                                      >= date.today()))
                        ):
                            if (member_membership.parliamentarian_id
                                != user.parliamentarian.id):  # type: ignore[attr-defined]
                                member = member_membership.parliamentarian
                                choices.append((str(member.id), member.title))

                self.parliamentarian_id.choices = list(dict.fromkeys(choices))
            else:
                self.parliamentarian_id.choices = []
        else:
            # Admins, editors can select any active parliamentarian
            self.parliamentarian_id.choices = [
                (str(parliamentarian.id), parliamentarian.title)
                for parliamentarian in PASParliamentarianCollection(
                    self.request.app, active=[True]).query()
            ]


class AttendenceAddPlenaryForm(Form, SettlementRunBoundMixin):

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.set_default_value_to_settlement_run_start()
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(
                self.request.app, active=[True]).query()
        ]
        self.parliamentarian_id.data = [
            choice[0] for choice in self.parliamentarian_id.choices
        ]


BULK_MEETING_TYPES: dict[str, str] = {
    'commission': _('Commission meeting'),
    'shortest': _('Shortest meeting'),
}


class AttendenceAddCommissionBulkForm(Form, SettlementRunBoundMixin):
    """Bulk form for commission-based meetings (commission or shortest)."""

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    type = RadioField(
        label=_('Type'),
        choices=list(BULK_MEETING_TYPES.items()),
        validators=[InputRequired()],
        default='commission',
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
        validators=[InputRequired()],
    )

    abschluss = BooleanField(
        label=_('Abschluss'),
        description=_('Mark as completed/closed'),
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
        choices=[]  # are set with in src/pas/assets/custom.js
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.set_default_value_to_settlement_run_start()
        self.commission_id.choices = [
            (commission.id, commission.title)
            for commission
            in PASCommissionCollection(self.request.session).query()
        ]
        # Set choices for all possible parliamentarians so WTForms can validate
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(
                self.request.app, active=[True]).query()
        ]
        # JavaScript will handle selection based on commission
        self.parliamentarian_id.data = []


class AttendenceEditBulkForm(Form, SettlementRunBoundMixin):
    """ Edit form for bulk attendance changes. """

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
        validators=[InputRequired()],
        render_kw={'readonly': True},
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
        choices=[]
    )

    bulk_edit_id = HiddenField(
        label=_('Bulk edit group'),
        validators=[InputRequired()],
    )

    abschluss = BooleanField(
        label=_('Abschluss'),
        description=_('Mark as completed/closed'),
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.set_default_value_to_settlement_run_start()
        self.commission_id.choices = [
            (commission.id, commission.title)
            for commission
            in PASCommissionCollection(self.request.session).query()
        ]
        # Set choices for all possible parliamentarians so WTForms can validate
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(
                self.request.app, active=[True]).query()
        ]


class AttendenceCommissionBulkEditForm(AttendenceEditBulkForm):
    """ Edit form for commission bulk attendance changes. """

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['type'] = 'commission'
        return result

    def process_obj(self, obj: Attendence) -> None:   # type: ignore[override]
        super().process_obj(obj)

        memberships = self.request.session.query(
            PASCommissionMembership).filter(
                PASCommissionMembership.commission_id == obj.commission_id
            ).all()

        self.parliamentarian_id.choices = [
            (str(m.parliamentarian.id), m.parliamentarian.title)
            for m in memberships
        ]

        self.duration.data = obj.duration / 60
        self.abschluss.data = obj.abschluss

        attendences = AttendenceCollection(
                self.request.session).query().filter_by(
                    bulk_edit_id=obj.bulk_edit_id
                )
        selected_parliamentarians = [
            (
                str(attendence.parliamentarian.id),
                attendence.parliamentarian.title
            ) for attendence in attendences
        ]

        self.commission_id.choices = [
            (obj.commission.id, obj.commission.title)  # type:ignore
        ]

        self.commission_id.data = str(obj.commission_id)

        self.parliamentarian_id.data = [
            choice[0] for choice in selected_parliamentarians
        ]

    def populate_obj(self, obj: Attendence) -> None:  # type: ignore[override]
        obj.duration = int(60 * (self.duration.data or 0))
        obj.date = self.date.data  # type: ignore[assignment]
        obj.commission_id = self.commission_id.data
        obj.abschluss = self.abschluss.data


class AttendencePlenaryBulkEditForm(AttendenceEditBulkForm):
    """ Edit form for plenary bulk attendance changes. """

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['type'] = 'plenary'
        return result

    def process_obj(self, obj: Attendence) -> None:   # type: ignore[override]
        super().process_obj(obj)
        self.duration.data = obj.duration / 60

        attendences = AttendenceCollection(
                self.request.session).query().filter_by(
                    bulk_edit_id=obj.bulk_edit_id
                )
        selected_parliamentarians = [
            (
                str(attendence.parliamentarian.id),
                attendence.parliamentarian.title
            ) for attendence in attendences
        ]

        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(
                self.request.app, active=[True]).query()
        ]

        self.parliamentarian_id.data = [
            choice[0] for choice in selected_parliamentarians
        ]

    def on_request(self) -> None:
        super().on_request()
        self.delete_field('commission_id')

    def populate_obj(self, obj: Attendence) -> None:  # type: ignore[override]
        obj.duration = int(60 * (self.duration.data or 0))
        obj.date = self.date.data  # type: ignore[assignment]


class AttendenceAddCommissionForm(Form, SettlementRunBoundMixin):

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
        choices=[
            (key, value) for key, value in TYPES.items() if key != 'plenary'
        ],
        validators=[InputRequired()],
        default='commission'
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    abschluss = BooleanField(
        label=_('Abschluss'),
        description=_('Mark as completed/closed'),
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['commission_id'] = self.model.id
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.set_default_value_to_settlement_run_start()
        self.parliamentarian_id.choices = [
            (
                str(membership.parliamentarian.id),
                membership.parliamentarian.title
            )
            for membership in self.model.memberships
        ]
        self.parliamentarian_id.data = [
            choice[0] for choice in self.parliamentarian_id.choices
        ]
