import json
from wtforms.fields import BooleanField, RadioField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import ChosenSelectField, ChosenSelectMultipleField
from onegov.org.forms.settings import \
    GeneralSettingsForm as OrgGeneralSettingsForm
from onegov.town6 import _
from onegov.user import UserCollection, User
from onegov.town6.theme import user_options
from wtforms.fields import StringField


class GeneralSettingsForm(OrgGeneralSettingsForm):
    """ Defines the settings form for onegov org. """

    page_image_position = RadioField(
        fieldset=_('Images'),
        description=_(
            "Choose the position of the page images on the content pages"),
        label=_("Page image position"),
        choices=(
            ('as_content', _("As a content image (between the title and text "
                             "of a content page)")),
            ('header', _("As header image (wide above the page content)"))
        ),
    )

    body_font_family_ui = ChosenSelectField(
        fieldset=_('Fonts'),
        label=_('Font family serif'),
        description=_('Used for text in html body'),
        choices=[],
        validators=[InputRequired()]
    )

    header_font_family_ui = ChosenSelectField(
        fieldset=_('Fonts'),
        label=_('Font family sans-serif'),
        description=_('Used for all the headings'),
        choices=[],
        validators=[InputRequired()]
    )

    @property
    def theme_options(self):
        options = self.model.theme_options

        if self.primary_color.data is None:
            options['primary-color-ui'] = user_options['primary-color-ui']
        else:
            options['primary-color-ui'] = self.primary_color.data

        if self.page_image_position.data is None:
            options['page-image-position'] = user_options[
                'page-image-position']
        else:
            options['page-image-position'] = self.page_image_position.data

        body_family = self.body_font_family_ui.data
        if body_family not in self.theme.font_families.values():
            options['body-font-family-ui'] = self.default_font_family
        else:
            options['body-font-family-ui'] = body_family
        header_family = self.header_font_family_ui.data
        if header_family not in self.theme.font_families.values():
            options['header-font-family-ui'] = self.default_font_family
        else:
            options['header-font-family-ui'] = header_family

        # override the options using the default values if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        return options

    @theme_options.setter
    def theme_options(self, options):
        self.primary_color.data = options.get('primary-color-ui')
        self.page_image_position.data = options.get('page-image-position')
        self.body_font_family_ui.data = options.get(
            'body-font-family-ui') or self.default_font_family
        self.header_font_family_ui.data = options.get(
            'header-font-family-ui') or self.default_font_family

    @property
    def default_font_family(self):
        return self.theme.default_options.get('body-font-family-ui')

    @property
    def header_font_family(self):
        return self.theme.default_options.get('header-font-family-ui')

    def populate_font_families(self):
        self.body_font_family_ui.choices = tuple(
            (value, label) for label, value in self.theme.font_families.items()
        )
        self.header_font_family_ui.choices = tuple(
            (value, label) for label, value in self.theme.font_families.items()
        )

    def on_request(self):
        self.populate_font_families()
        # We delete this from the org form
        self.delete_field('font_family_sans_serif')

        @self.request.after
        def clear_locale(response):
            response.delete_cookie('locale')


class ChatSettingsForm(Form):
    on_request_include = ()

    chat_staff = ChosenSelectMultipleField(
        label=_('Show chat for chosen people'),
        choices=[]
    )

    enable_chat = BooleanField(
        label=_('Enable the chat'),
        description=_('The chat is currently in a test-phase. '
                      'Activate at your own risk.'),
        default=False
    )

    opening_hours_chat = StringField(
        label=_("Opening Hours"),
        description=_("If left empty, the chat is open 24/7"),
        fieldset=_("Opening Hours"),
        render_kw={'class_': 'many many-opening-hours'}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_errors = {}

    def process_obj(self, obj):
        super().process_obj(obj)
        self.chat_staff = obj.chat_staff or {}
        self.enable_chat = obj.enable_chat or {}
        if not obj.opening_hours_chat or None:
            self.opening_hours_chat.data = self.time_to_json(None)
        else:
            self.opening_hours_chat.data = self.time_to_json(
                obj.opening_hours_chat
            )

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.chat_staff = self.chat_staff.data
        obj.enable_chat = self.enable_chat.data
        obj.opening_hours_chat = self.json_to_time(
            self.opening_hours_chat.data) or None

    def populate_chat_staff(self):
        people = UserCollection(self.request.session).query().filter(
            User.role.in_(['editor', 'admin']))
        staff_members = [(
            (p.id.hex, p.username)
        ) for p in people]
        self.chat_staff.choices = [
            (v, k) for v, k in staff_members
        ]

    def validate(self):
        result = super().validate()
        for day, start, end in self.json_to_time(self.opening_hours_chat.data):
            if not (day and start and end):
                self.opening_hours_chat.errors.append(
                    _('Please add a day and times to each opening hour entry.')
                )
                result = False
            if start > end:
                self.opening_hours_chat.errors.append(
                    _("Start time cannot be later than end time.")
                )
                result = False
        return result

    def json_to_time(self, text=None):
        result = []

        for value in json.loads(text or '{}').get('values', []):
            result.append([value.get('day', ''), value.get('start', ''),
                          value.get('end', '')])

        return result

    def time_to_json(self, opening_hours=None):
        opening_hours = opening_hours or []

        return json.dumps({
            'labels': {
                'day': self.request.translate(_("day")),
                'start': self.request.translate(_("Start")),
                'end': self.request.translate(_("End")),
                'remove': self.request.translate(_("Remove")),
            },
            'values': [
                {
                    'day': o[0],
                    'start': o[1],
                    'end': o[2],
                    'error': self.time_errors.get(ix, "")
                } for ix, o in enumerate(opening_hours)
            ],
            'days': {
                self.request.translate(
                    _("Mo")): self.request.translate(_("Mo")),
                self.request.translate(
                    _("Tu")): self.request.translate(_("Tu")),
                self.request.translate(
                    _("We")): self.request.translate(_("We")),
                self.request.translate(
                    _("Th")): self.request.translate(_("Th")),
                self.request.translate(
                    _("Fr")): self.request.translate(_("Fr")),
                self.request.translate(
                    _("Sa")): self.request.translate(_("Sa")),
                self.request.translate(
                    _("Su")): self.request.translate(_("Su"))
            }
        })

    def on_request(self):
        self.populate_chat_staff()
        for include in self.on_request_include:
            self.request.include(include)
