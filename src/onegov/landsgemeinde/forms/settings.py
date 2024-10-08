from wtforms.fields import EmailField
from onegov.form import Form
from onegov.landsgemeinde import _
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import Optional

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models import Organisation


class OpenDataSettingsForm(Form):

    ogd_publisher_mail = EmailField(
        label=_('E-Mail'),
        validators=[Optional(), Email()]
    )

    ogd_publisher_id = StringField(
        label=_('ID')
    )

    ogd_publisher_name = StringField(
        label=_('Name')
    )

    def process_obj(
        self,
        obj: 'Organisation'  # type:ignore[override]
    ) -> None:

        super().process_obj(obj)
        self.ogd_publisher_mail.data = obj.ogd_publisher_mail or ''
        self.ogd_publisher_id.data = obj.ogd_publisher_id or ''
        self.ogd_publisher_name.data = obj.ogd_publisher_name or ''

    def populate_obj(  # type:ignore[override]
        self,
        obj: 'Organisation',  # type:ignore[override]
        *args: Any,
        **kwargs: Any
    ) -> None:

        super().populate_obj(obj, *args, **kwargs)
        obj.ogd_publisher_mail = self.ogd_publisher_mail.data
        obj.ogd_publisher_id = self.ogd_publisher_id.data
        obj.ogd_publisher_name = self.ogd_publisher_name.data
