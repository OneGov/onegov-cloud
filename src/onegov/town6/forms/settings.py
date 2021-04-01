from onegov.org.forms.settings import GeneralSettingsForm as \
    OrgGeneralSettingsForm
from onegov.form.fields import ChosenSelectField
from onegov.town6 import _
from onegov.org.theme import user_options
from wtforms import validators


class GeneralSettingsForm(OrgGeneralSettingsForm):
    """ Defines the settings form for onegov org. """

    # Todo: Add those fields after primary color
    body_font_family_ui = ChosenSelectField(
        label=_('Font family serif'),
        description=_('Used for text in html body'),
        choices=[],
        validators=[validators.InputRequired()]
    )

    header_font_family_ui = ChosenSelectField(
        label=_('Font family sans-serif'),
        description=_('Used for all the headings'),
        choices=[],
        validators=[validators.InputRequired()]
    )

    @property
    def theme_options(self):
        options = self.model.theme_options

        try:
            options['primary-color-ui'] = self.primary_color.data.get_hex()
        except AttributeError:
            options['primary-color-ui'] = user_options['primary-color-ui']

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

    @property
    def default_font_family(self):
        return self.theme.default_options.get('body-font-family-ui')

    @property
    def header_font_family(self):
        return self.theme.default_options.get('header-font-family-ui')

    @theme_options.setter
    def theme_options(self, options):
        self.primary_color.data = options.get('primary-color-ui')
        self.body_font_family_ui.data = options.get(
            'body-font-family-ui') or self.default_font_family
        self.header_font_family_ui.data = options.get(
            'header-font-family-ui') or self.default_font_family

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
