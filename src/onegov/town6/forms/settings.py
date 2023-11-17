from wtforms.fields import BooleanField, StringField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import (ChosenSelectField, ChosenSelectMultipleField,
                                ColorField)
from onegov.org.forms.settings import \
    GeneralSettingsForm as OrgGeneralSettingsForm
from onegov.town6 import _
from onegov.town6.theme import user_options


class GeneralSettingsForm(OrgGeneralSettingsForm):
    """ Defines the settings form for onegov org. """

    body_font_family_ui = ChosenSelectField(
        label=_('Font family serif'),
        description=_('Used for text in html body'),
        choices=[],
        validators=[InputRequired()]
    )

    header_font_family_ui = ChosenSelectField(
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

    show_chat_for = ChosenSelectMultipleField(
        label=_('Hide chat for chosen roles'),
        choices=[]
    )

    disable_chat = BooleanField(
        label=_('Disable the chat'),
        description=_('The chat is currently in an test-phase. '
                      'Activate at your own risk.'),
        default=True
    )

    def process_obj(self, obj):
        super().process_obj(obj)
        color = obj.chat_bg_color
        if not color:
            color = obj.theme_options.get(
                'primary-color-ui', user_options['primary-color-ui'])

        # self.chat_color.data = color

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        # obj.chat_bg_color = self.chat_color.data
