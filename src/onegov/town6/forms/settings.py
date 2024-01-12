from wtforms.fields import BooleanField, RadioField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import ChosenSelectField, ChosenSelectMultipleField
from onegov.org.forms.settings import \
    GeneralSettingsForm as OrgGeneralSettingsForm
from onegov.town6 import _
from onegov.user import UserCollection, User
from onegov.town6.theme import user_options


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

    chat_staff = ChosenSelectMultipleField(
        label=_('Show chat for chosen people'),
        choices=[]
    )

    enable_chat = BooleanField(
        label=_('Enable the chat'),
        description=_('The chat is currently in an test-phase. '
                      'Activate at your own risk.'),
        default=False
    )

    def process_obj(self, obj):
        super().process_obj(obj)
        self.chat_staff = obj.chat_staff or {}
        self.enable_chat = obj.enable_chat or {}

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.chat_staff = self.chat_staff.data
        obj.enable_chat = self.enable_chat.data

    def populate_chat_staff(self):
        people = UserCollection(self.request.session).query().filter(
            User.role.in_(['editor', 'admin']))
        staff_members = [(
            (p.id.hex, p.username)
        ) for p in people]
        self.chat_staff.choices = [
            (v, k) for v, k in staff_members
        ]

    def on_request(self):
        self.populate_chat_staff()
