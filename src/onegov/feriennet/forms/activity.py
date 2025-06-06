from __future__ import annotations

from onegov.core.utils import normalize_for_url
from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.org.forms.fields import HtmlField
from onegov.user import User, UserCollection
from wtforms.fields import TextAreaField, SelectField, StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from wtforms.fields.choices import _Choice


TAGS = tuple((tag, tag) for tag in (
    _('Accessible'),
    _('Adventure'),
    _('Animals'),
    _('Baking'),
    _('Cinema'),
    _('Computer'),
    _('Cooking'),
    _('Dance'),
    _('Design'),
    _('Excursion'),
    _('Farm'),
    _('Game'),
    _('Handicraft'),
    _('Health'),
    _('Media'),
    _('Museums'),
    _('Music'),
    _('Nature'),
    _('Professions'),
    _('Science'),
    _('Security'),
    _('Sightseeing'),
    _('Sport'),
    _('Styling'),
    _('Theater'),
    _('Trade'),
    _('Camp'),
    _('Camp in House'),
    _('Tent Camp'),
    _('Family Camp'),
    _('Trecking Camp'),
    _('Water'),
    _('Continuing Education'),
    _('Healthy Snacks'),
    _('Just for Boys'),
    _('Just for Girls'),
))
# When adding new tags for WWF, adapt exports/base.py::141


class VacationActivityForm(Form):

    request: FeriennetRequest

    title = StringField(
        label=_('Title'),
        description=_('The title of the activity'),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes briefly what this activity is about'),
        validators=[InputRequired()],
        render_kw={'rows': 4})

    text = HtmlField(
        label=_('Text'))

    tags = OrderedMultiCheckboxField(
        label=_('Tags'),
        choices=TAGS)

    username = SelectField(
        label=_('Organiser'),
        validators=[InputRequired()],
        fieldset=_('Administration'),
        default='0xdeadbeef')

    location = TextAreaField(
        label=_('Location'),
        fieldset=_('Map'),
        render_kw={'rows': 4}
    )

    @property
    def username_choices(self) -> list[_Choice]:
        assert self.request.is_admin  # safety net

        users = (
            UserCollection(self.request.session)
            .by_roles('admin', 'editor')
            .with_entities(User.username, User.title)
        )

        def by_title(choice: _Choice) -> str:
            return normalize_for_url(choice[1])

        return sorted((
            (username, title) for username, title in users
        ), key=by_title)

    def set_username_default(self, value: str) -> None:
        # we can't set self.username.default here, as that has already been
        # done by wtforms - but we can see if the default has been used
        if self.username.data == '0xdeadbeef':
            self.username.data = value

    def for_admins(self) -> None:
        assert self.request.current_username is not None
        self.set_username_default(self.request.current_username)
        self.username.choices = self.username_choices

    def for_non_admins(self) -> None:
        self.delete_field('username')

    def on_request(self) -> None:
        if self.request.is_admin:
            self.for_admins()
        else:
            self.for_non_admins()
