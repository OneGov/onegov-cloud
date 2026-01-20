from __future__ import annotations

import json
from wtforms.fields import BooleanField, RadioField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import ChosenSelectField, ChosenSelectMultipleField
from onegov.form.fields import TagsField
from onegov.org.forms.settings import (
    GeneralSettingsForm as OrgGeneralSettingsForm)
from onegov.town6 import _
from onegov.user import UserCollection, User
from onegov.town6.theme import user_options
from wtforms.fields import StringField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models import Organisation
    from webob import Response


class GeneralSettingsForm(OrgGeneralSettingsForm):
    """ Defines the settings form for onegov org. """

    page_image_position = RadioField(
        fieldset=_('Images'),
        description=_(
            'Choose the position of the page images on the content pages'),
        label=_('Page image position'),
        choices=(
            ('as_content', _('As a content image (between the title and text '
                             'of a content page)')),
            ('header', _('As header image (wide above the page content)'))
        ),
        default='as_content'
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

    def populate_font_families(self) -> None:
        self.body_font_family_ui.choices = [
            (value, label) for label, value in self.theme.font_families.items()
        ]
        self.header_font_family_ui.choices = [
            (value, label) for label, value in self.theme.font_families.items()
        ]

    def on_request(self) -> None:
        self.populate_font_families()
        # We delete this from the org form
        self.delete_field('font_family_sans_serif')

        @self.request.after
        def clear_locale(response: Response) -> None:
            response.delete_cookie('locale')


class ChatSettingsForm(Form):

    enable_chat = RadioField(
        label=_('Enable the chat'),
        choices=[
            ('disabled', _('Disable chat')),
            ('people_chat', _('Enable chat for chosen people')),
            ('chatbot', _('Enable AI chatbot')),
        ],
        default='disabled'
    )

    chat_link = StringField(
        label=_('Link to chat service'),
        description=_('https://govikonchatbot.seantis.ch'),
        depends_on=('enable_chat', 'chatbot'),
        validators=[InputRequired()]
    )

    chat_staff = ChosenSelectMultipleField(
        label=_('Show chat for chosen people'),
        choices=[],
        depends_on=('enable_chat', 'people_chat')
    )

    chat_topics = TagsField(
        label=_('Chat Topics'),
        description=_(
            "The topics can be chosen on the form at the start of the chat. "
            "Example topics are 'Social', 'Clubs' or 'Planning & Construction'"
            ". If left empty, all Chats get the topic 'General'."),
        depends_on=('enable_chat', 'people_chat')
    )

    specific_opening_hours = BooleanField(
        label=_('Specific Opening Hours'),
        description=_('If unchecked, the chat is open 24/7.'),
        depends_on=('enable_chat', 'people_chat')
    )

    opening_hours_chat = StringField(
        label=_('Opening Hours'),
        depends_on=('specific_opening_hours', 'y'),
        render_kw={'class_': 'many many-opening-hours'}
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.time_errors: dict[int, str] = {}

    def process_obj(
        self,
        obj: Organisation  # type:ignore[override]
    ) -> None:

        super().process_obj(obj)
        self.chat_staff.data = obj.chat_staff or []
        self.enable_chat.data = obj.enable_chat or 'disabled'
        self.chat_topics.data = obj.chat_topics or []
        self.specific_opening_hours.data = obj.specific_opening_hours
        if not obj.opening_hours_chat:
            self.opening_hours_chat.data = self.time_to_json(None)
        else:
            self.opening_hours_chat.data = self.time_to_json(
                obj.opening_hours_chat
            )

    def populate_obj(  # type:ignore[override]
        self,
        obj: Organisation,  # type:ignore[override]
        *args: Any,
        **kwargs: Any
    ) -> None:

        super().populate_obj(obj, *args, **kwargs)
        obj.chat_staff = self.chat_staff.data
        obj.enable_chat = self.enable_chat.data
        obj.chat_topics = self.chat_topics.data  # type:ignore[assignment]
        obj.specific_opening_hours = self.specific_opening_hours.data
        obj.opening_hours_chat = self.json_to_time(
            self.opening_hours_chat.data) or None

    def populate_chat_staff(self) -> None:
        people = UserCollection(self.request.session).query().filter(
            User.role.in_(['editor', 'admin']))
        staff_members = [(
            (p.id.hex, p.username)
        ) for p in people]
        self.chat_staff.choices = list(staff_members)

    def ensure_valid_opening_hours(self) -> bool:
        if not self.specific_opening_hours.data:
            return True

        opening_times = self.json_to_time(self.opening_hours_chat.data)
        if not opening_times:
            assert isinstance(self.opening_hours_chat.errors, list)
            self.opening_hours_chat.errors.append(
                _('Please add a day and times to each opening hour '
                  'entry or deactivate specific opening hours.')
            )
            return False

        result = True
        for day, start, end in opening_times:
            # FIXME: shouldn't this use time_errors?
            if not (day and start and end):
                assert isinstance(self.opening_hours_chat.errors, list)
                self.opening_hours_chat.errors.append(
                    _('Please add a day and times to each opening hour '
                      'entry or deactivate specific opening hours.')
                )
                result = False
            if start > end:
                assert isinstance(self.opening_hours_chat.errors, list)
                self.opening_hours_chat.errors.append(
                    _('Start time cannot be later than end time.')
                )
                result = False
        return result

    def json_to_time(self, text: str | None = None) -> list[list[str]]:
        if not text:
            return []

        return [
            [
                value.get('day', ''),
                value.get('start', ''),
                value.get('end', '')
            ]
            for value in json.loads(text).get('values', [])
        ]

    def time_to_json(
        self,
        opening_hours: list[list[str]] | None = None
    ) -> str:

        opening_hours = opening_hours or []
        return json.dumps({
            'labels': {
                'day': self.request.translate(_('day')),
                'start': self.request.translate(_('Start')),
                'end': self.request.translate(_('End')),
                'add': self.request.translate(_('Add')),
                'remove': self.request.translate(_('Remove')),
            },
            'values': [
                {
                    'day': o[0],
                    'start': o[1],
                    'end': o[2],
                    'error': self.time_errors.get(ix, '')
                } for ix, o in enumerate(opening_hours)
            ],
            'days': {
                0: self.request.translate(_('Mo')),
                1: self.request.translate(_('Tu')),
                2: self.request.translate(_('We')),
                3: self.request.translate(_('Th')),
                4: self.request.translate(_('Fr')),
                5: self.request.translate(_('Sa')),
                6: self.request.translate(_('Su'))
            }
        })

    def on_request(self) -> None:
        self.populate_chat_staff()


class RISSettingsForm(Form):

    ris_enabled = BooleanField(
        label=_('Enable RIS'),
        description=_('Enables the RIS integration for this organisation.'),
        default=False
    )

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
