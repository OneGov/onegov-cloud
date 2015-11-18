from onegov.form import Form, with_options
from wtforms import HiddenField, StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField, URLField
from wtforms.widgets import TextArea
from wtforms_components import ColorField
from onegov.town import _
from onegov.town.theme import user_options


class SettingsForm(Form):
    """ Defines the settings form for onegov town. """

    name = StringField(
        label=_("Name"),
        validators=[validators.InputRequired()],
        fieldset=_("General")
    )
    logo_url = StringField(
        label=_("Logo"),
        description=_("URL pointing to the logo"),
        fieldset=_("General")
    )
    reply_to = EmailField(
        _("E-Mail Reply Address"), [validators.InputRequired()],
        description=_("Replies to automated e-mails go to this address."),
        fieldset=_("General")
    )
    primary_color = ColorField(
        label=_("Primary Color"),
        fieldset=_("General")
    )
    contact = TextAreaField(
        label=_("Contact"),
        description=_("The address and phone number of the municipality"),
        widget=with_options(TextArea, rows=8),
        fieldset=_("General")
    )
    contact_url = URLField(
        label=_("Contact Page"),
        description=_("URL pointing to a contact page"),
        fieldset=_("General")
    )
    opening_hours = TextAreaField(
        label=_("Opening Hours"),
        description=_("The opening hours of the municipality"),
        widget=with_options(TextArea, rows=8),
        fieldset=_("General")
    )
    opening_hours_url = URLField(
        label=_("Opening Hours Page"),
        description=_("URL pointing to an opening hours page"),
        fieldset=_("General")
    )
    facebook_url = URLField(
        label=_("Facebook"),
        description=_("URL pointing to the facebook site"),
        fieldset=_("General")
    )
    twitter_url = URLField(
        label=_("Twitter"),
        description=_("URL pointing to the twitter site"),
        fieldset=_("General")
    )
    homepage_images = TextAreaField(
        label=_("Homepage Images"),
        description=_(
            "Up to six URLs pointing to images for the tiles on the homepage."
        ),
        widget=with_options(TextArea, rows=6),
        fieldset=_("Homepage")
    )
    online_counter_label = StringField(
        label=_("Online Counter Label"),
        description=_("Forms and applications"),
        fieldset=_("Homepage")
    )
    reservations_label = StringField(
        label=_("Reservations Label"),
        description=_("Daypasses and rooms"),
        fieldset=_("Homepage")
    )
    sbb_daypass_label = StringField(
        label=_("SBB Daypass Label"),
        description=_("Generalabonnement for Towns"),
        fieldset=_("Homepage")
    )
    analytics_code = TextAreaField(
        label=_("Analytics Code"),
        description=_("JavaScript for web statistics support"),
        widget=with_options(TextArea, rows=10),
        fieldset=_("Advanced")
    )

    # the footer height is determined by javascript, see town.scss and
    # common.js for more information (search for footer)
    footer_height = HiddenField()

    @property
    def theme_options(self):
        options = {
            'primary-color': self.primary_color.data.get_hex(),
            'footer-height': self.footer_height.data
        }

        # override the options using the default vaules if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        urls = (url.strip() for url in self.homepage_images.data.split('\n'))
        urls = (url for url in urls if url)

        for ix, url in enumerate(urls):
            # put the url in apostrophes, because it's a sass string
            options['tile-image-{}'.format(ix + 1)] = '"{}"'.format(url)

        return options

    @theme_options.setter
    def theme_options(self, theme_options):
        self.primary_color.data = theme_options.get('primary-color')
        self.footer_height.data = theme_options.get('footer-height')

        tile_image_keys = ('tile-image-{}'.format(ix) for ix in range(1, 7))
        urls = (theme_options.get(key) for key in tile_image_keys)
        urls = (url.strip('"') for url in urls if url)

        self.homepage_images.data = '\n'.join(urls)
