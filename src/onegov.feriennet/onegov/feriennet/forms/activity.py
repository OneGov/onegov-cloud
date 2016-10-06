from onegov.core.html import sanitize_html
from onegov.core.utils import normalize_for_url
from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.org.utils import annotate_html
from onegov.user import User, UserCollection
from wtforms import TextField, TextAreaField, SelectField
from wtforms.validators import InputRequired


TAGS = tuple((tag, tag) for tag in (
    _("Adventure"),
    _("Animals"),
    _("Baking"),
    _("Cinema"),
    _("Computer"),
    _("Cooking"),
    _("Dance"),
    _("Design"),
    _("Handicraft"),
    _("Health"),
    _("Media"),
    _("Museums"),
    _("Music"),
    _("Nature"),
    _("Science"),
    _("Security"),
    _("Sport"),
    _("Styling"),
    _("Theater"),
    _("Trade"),
))


class VacationActivityForm(Form):

    title = TextField(
        label=_("Title"),
        description=_("The title of the activity"),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes briefly what this activity is about"),
        validators=[InputRequired()],
        render_kw={'rows': 4})

    text = TextAreaField(
        label=_("Text"),
        render_kw={'class_': 'editor'},
        filters=[sanitize_html, annotate_html])

    tags = OrderedMultiCheckboxField(
        label=_("Tags"),
        choices=TAGS)

    username = SelectField(
        label=_("Organiser"),
        validators=[InputRequired()],
        fieldset=_("Administration"),
        default='0xdeadbeef')

    @property
    def username_choices(self):
        assert self.request.is_admin  # safety net

        users = UserCollection(self.request.app.session())
        users = users.by_roles('admin', 'editor')
        users = users.with_entities(User.username, User.title)

        def choice(row):
            return row[0], row[1]

        def by_title(choice):
            return normalize_for_url(choice[1])

        return sorted([choice(r) for r in users.all()], key=by_title)

    def set_username_default(self, value):
        # we can't set self.username.default here, as that has already been
        # done by wtforms - but we can see if the default has been used
        if self.username.data == '0xdeadbeef':
            self.username.data = value

    def for_admins(self):
        self.set_username_default(self.request.current_username)
        self.username.choices = self.username_choices

    def for_non_admins(self):
        self.delete_field('username')

    def on_request(self):
        if self.request.is_admin:
            self.for_admins()
        else:
            self.for_non_admins()
