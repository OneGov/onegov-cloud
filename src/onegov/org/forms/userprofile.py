from __future__ import annotations

from onegov.form import Form
from onegov.org import _
from wtforms.fields import RadioField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.user import User


class UserProfileForm(Form):
    """ Defines the settings form for user profiles. """

    if TYPE_CHECKING:
        request: OrgRequest

    ticket_statistics = RadioField(
        label=_('Send a periodic status e-mail.'),
        fieldset=_('General'),
        default='weekly',
        validators=[InputRequired()],
        choices=(
            ('daily', _(
                'Daily (exluding the weekend)')),
            ('weekly', _(
                'Weekly (on mondays)')),
            ('monthly', _(
                'Monthly (on first monday of the month)')),
            ('never', _(
                'Never')),
        )
    )

    @property
    def enable_ticket_statistics(self) -> bool:
        if not self.request.app.send_ticket_statistics:
            # no point in showing it if we don't send it.
            return False

        roles = self.request.app.settings.org.status_mail_roles
        return self.request.current_role in roles

    def on_request(self) -> None:
        if not self.enable_ticket_statistics:
            self.delete_field('ticket_statistics')

    def populate_obj(self, obj: User) -> None:  # type:ignore
        super().populate_obj(obj, exclude={
            'ticket_statistics',
        })

        if self.enable_ticket_statistics:
            obj.data = obj.data or {}
            obj.data['ticket_statistics'] = self.ticket_statistics.data

    def process_obj(self, obj: User) -> None:  # type:ignore
        super().process_obj(obj)

        if self.enable_ticket_statistics:
            self.ticket_statistics.data = (
                obj.data or {}).get('ticket_statistics', 'weekly')
