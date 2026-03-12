from __future__ import annotations

from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.org.forms import ManageUserGroupForm
from onegov.user import UserCollection
from onegov.user.models import User
from onegov.translator_directory import _
from onegov.translator_directory.constants import FINANZSTELLE
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.user import UserGroup


class TranslatorUserGroupForm(ManageUserGroupForm):
    """Custom user group form for translator directory.

    Links user groups to a Finanzstelle (cost center) and
    associated accountant emails for notifications.
    Editors defined as accountant_emails can see
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
        validators=[InputRequired()],
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

    def ensure_accountants_are_editors(self) -> bool:
        if not self.accountant_emails.data:
            return True

        session = self.request.session
        emails = self.accountant_emails.data

        non_editor_query = (
            session.query(User)
            .filter(User.username.in_(emails))
            .filter(User.role.notin_(['editor', 'admin']))
        )

        if session.query(non_editor_query.exists()).scalar():
            assert isinstance(self.accountant_emails.errors, list)
            self.accountant_emails.errors.append(
                _('All accountant users must have the editor or admin role')
            )
            return False
        return True

    def update_model(self, model: UserGroup) -> None:
        if not model.meta:
            model.meta = {}

        model.meta['finanzstelle'] = self.finanzstelle.data
        model.meta['accountant_emails'] = self.accountant_emails.data or []

        super().update_model(model)

    def apply_model(self, model: UserGroup) -> None:
        super().apply_model(model)

        if model.meta:
            self.finanzstelle.data = model.meta.get('finanzstelle')
            self.accountant_emails.data = model.meta.get(
                'accountant_emails', []
            )
