from __future__ import annotations

from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.org.forms import ManageUserGroupForm
from onegov.ticket import TicketPermission
from onegov.user import UserCollection
from onegov.translator_directory import _
from onegov.translator_directory.constants import FINANZSTELLE
from wtforms.validators import InputRequired
from wtforms.validators import Optional


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.user import UserGroup


class TranslatorUserGroupForm(ManageUserGroupForm):
    """Custom user group form for translator directory.

    Links user groups to a Finanzstelle (cost center) and
    associated accountant emails for notifications.
    Members of this group will have permission to view/edit
    time report tickets for their assigned Finanzstelle.
    """

    # Feature is not used in Translator Directory
    shared_email = None  # type: ignore[assignment]

    finanzstelle = ChosenSelectField(
        label=_('Cost Center (Finanzstelle)'),
        choices=[],
        validators=[InputRequired()],
        description=_(
            'Select the cost center this user group is responsible for'
        ),
    )

    accountant_emails = ChosenSelectMultipleField(
        label=_('Accountant Users'),
        choices=[],
        validators=[Optional()],
        description=_(
            'Select users who are accountants for this cost center. '
            'Their emails will be used for notifications.'
        ),
    )

    def on_request(self) -> None:

        super().on_request()
        self.finanzstelle.choices = [
            (key, fs.name) for key, fs in FINANZSTELLE.items()
        ]

        users = UserCollection(self.request.session).query().all()
        self.accountant_emails.choices = [
            (user.username, f'{user.realname or user.username}')
            for user in users
        ]

    def update_model(self, model: UserGroup) -> None:
        if not model.meta:
            model.meta = {}

        model.meta['finanzstelle'] = self.finanzstelle.data
        model.meta['accountant_emails'] = self.accountant_emails.data or []

        assert hasattr(model, 'ticket_permissions')

        super().update_model(model)

        trp_permission = (
            self.request.session.query(TicketPermission)
            .filter_by(user_group_id=model.id, handler_code='TRP')
            .first()
        )

        if self.finanzstelle.data:
            if trp_permission:
                trp_permission.group = self.finanzstelle.data
            else:
                self.request.session.add(
                    TicketPermission(
                        user_group_id=model.id,
                        handler_code='TRP',
                        group=self.finanzstelle.data,
                        exclusive=True,
                    )
                )
        else:
            if trp_permission:
                self.request.session.delete(trp_permission)

    def apply_model(self, model: UserGroup) -> None:
        super().apply_model(model)

        if model.meta:
            self.finanzstelle.data = model.meta.get('finanzstelle')
            self.accountant_emails.data = model.meta.get(
                'accountant_emails', []
            )
