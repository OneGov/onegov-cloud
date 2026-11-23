from wtforms.fields import BooleanField, RadioField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.org.forms.settings import (
    AppearanceSettingsForm as OrgAppearanceSettingsForm)
from onegov.org.forms.settings import (
    ModuleActivationSettingsForm as OrgModuleActivationSettingsForm)
from onegov.town6 import _
from onegov.town6.theme import user_options
from wtforms.fields import SelectChoice
from wtforms.fields import StringField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response


class AppearanceSettingsForm(OrgAppearanceSettingsForm):
    """ Defines the settings form for onegov org. """

    page_image_position = RadioField(
        fieldset=_('Images'),
        description=_(
            'Choose the position of the page images on the content pages'),
        label=_('Page image position'),
        choices=(
            SelectChoice(
                'as_content',
                _(
                    'As a content image (between the title and '
                    'text of a content page)'
                )
            ),
            SelectChoice(
                'header',
                _('As header image (wide above the page content)')
            )
        ),
        default='as_content'
    )

    body_font_family_ui = ChosenSelectField(
        fieldset=_('Fonts'),
        label=_('Font family serif'),
        description=_('Used for text in html body'),
        choices=lambda form, field: [
            SelectChoice(value, label)
            for label, value in form.theme.font_families.items()
        ],
        validators=[InputRequired()]
    )

    header_font_family_ui = ChosenSelectField(
        fieldset=_('Fonts'),
        label=_('Font family sans-serif'),
        description=_('Used for all the headings'),
        choices=lambda form, field: [
            SelectChoice(value, label)
            for label, value in form.theme.font_families.items()
        ],
        validators=[InputRequired()]
    )

    @property
    def theme_options(self) -> dict[str, Any]:
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
    def theme_options(self, options: dict[str, Any]) -> None:
        self.primary_color.data = options.get('primary-color-ui')
        self.page_image_position.data = options.get('page-image-position')
        self.body_font_family_ui.data = options.get(
            'body-font-family-ui') or self.default_font_family
        self.header_font_family_ui.data = options.get(
            'header-font-family-ui') or self.default_font_family

    @property
    def default_font_family(self) -> str | None:
        return self.theme.default_options.get('body-font-family-ui')

    @property
    def header_font_family(self) -> str | None:
        return self.theme.default_options.get('header-font-family-ui')

    def on_request(self) -> None:
        # We delete this from the org form
        self.delete_field('font_family_sans_serif')

        @self.request.after
        def clear_locale(response: Response) -> None:
            response.delete_cookie('locale')


class ChatSettingsForm(Form):

    enable_chat = RadioField(
        label=_('Enable the chat'),
        choices=[
            SelectChoice('disabled', _('Disable chat')),
            SelectChoice('chatbot', _('Enable AI chatbot')),
        ],
        default='disabled'
    )

    chat_link = StringField(
        label=_('Link to chat service'),
        description=_('https://govikonchatbot.seantis.ch'),
        depends_on=('enable_chat', 'chatbot'),
        validators=[InputRequired()]
    )


class RISSettingsForm(Form):

    ris_parliamentarian_term = ChosenSelectField(
        label=_('Designation for parliamentarians'),
        description=_(
            'This designation is used for parliamentarians throughout the '
            'RIS pages and menus.'
        ),
        choices=(
            SelectChoice(
                'parliamentarians',
                _('Parliamentarians')
            ),
            SelectChoice(
                'residents_council_members',
                _('Town council members')
            ),
        ),
        default='parliamentarians',
    )

    def on_request(self) -> None:
        self.ris_parliamentarian_term.choices = [
            SelectChoice(
                'parliamentarians',
                self.request.translate(_('Parliamentarians')),
            ),
            SelectChoice(
                'residents_council_members',
                self.request.translate(_('Town council members')),
            ),
        ]

    # the url breadcrumbs shall point to for non-logged-in users
    ris_main_url = StringField(
        label=_('URL path for the RIS main page'),
        description=_(
            'The URL path for the RIS main page for non-logged-in users.'),
        default='',
    )

    # predefined categories for interest ties
    ris_interest_tie_categories = TextAreaField(
        label=_('Predefined categories for interest ties'),
        description=_(
            'Enter a list of categories for interest ties. Each '
            'category should be separated by a semicolon. '
            'Example: Cat 1 text; Cat 2 text; Cat 3 text'),
        render_kw={'rows': 12}
    )


class ModuleActivationSettingsForm(OrgModuleActivationSettingsForm):
    ris_enabled = BooleanField(
        label=_('Enable Ratsinformationssystem (RIS)'),
        description=_('Enables the RIS integration for this organisation.'),
        default=False
    )
