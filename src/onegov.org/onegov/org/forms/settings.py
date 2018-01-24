import re

from lxml import etree
from onegov.form import Form
from onegov.form import with_options
from onegov.form.validators import Stdnum
from onegov.gis import CoordinatesField
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.homepage_widgets import (
    transform_homepage_structure,
    XML_LINE_OFFSET
)
from onegov.org.theme import user_options
from wtforms import HiddenField, StringField, TextAreaField, RadioField
from wtforms import ValidationError
from wtforms import validators
from wtforms.fields.html5 import EmailField, URLField
from wtforms_components import ColorField


ERROR_LINE_RE = re.compile(r'line ([0-9]+)')


class SettingsForm(Form):
    """ Defines the settings form for onegov org. """

    name = StringField(
        label=_("Name"),
        validators=[validators.InputRequired()],
        fieldset=_("General")
    )
    logo_url = StringField(
        label=_("Logo"),
        description=_("URL pointing to the logo"),
        fieldset=_("General"),
        render_kw={'class_': 'image-url'}
    )
    square_logo_url = StringField(
        label=_("Logo (Square)"),
        description=_("URL pointing to the logo"),
        fieldset=_("General"),
        render_kw={'class_': 'image-url'}
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
    locales = RadioField(
        label=_("Languages"),
        fieldset=_("General"),
        choices=(
            ('de_CH', _("German")),
            ('fr_CH', _("French"))
        ),
        validators=[validators.InputRequired()]
    )
    bank_account = StringField(
        label=_("Bank Account (IBAN)"),
        fieldset=_("Payment"),
        validators=[Stdnum(format='iban')]
    )
    bank_beneficiary = StringField(
        label=_("Beneficiary"),
        fieldset=_("Payment"),
    )
    bank_payment_order_type = RadioField(
        label=_("Payment Order"),
        fieldset=_("Payment"),
        choices=[
            ('basic', _("Basic")),
            ('esr', _("With reference number (ESR)")),
        ],
        default='basic'
    )
    bank_esr_participant_number = StringField(
        label=_("ESR participant number"),
        fieldset=_("Payment"),
        validators=[validators.InputRequired()],
        depends_on=('bank_payment_order_type', 'esr')
    )
    contact = TextAreaField(
        label=_("Contact"),
        description=_("The address and phone number of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("Information")
    )
    contact_url = URLField(
        label=_("Contact Link"),
        description=_("URL pointing to a contact page"),
        fieldset=_("Information"),
        render_kw={'class_': 'internal-url'}
    )
    opening_hours = TextAreaField(
        label=_("Opening Hours"),
        description=_("The opening hours of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("Information")
    )
    opening_hours_url = URLField(
        label=_("Opening Hours Link"),
        description=_("URL pointing to an opening hours page"),
        fieldset=_("Information"),
        render_kw={'class_': 'internal-url'}
    )
    facebook_url = URLField(
        label=_("Facebook"),
        description=_("URL pointing to the facebook site"),
        fieldset=_("Social Media")
    )
    twitter_url = URLField(
        label=_("Twitter"),
        description=_("URL pointing to the twitter site"),
        fieldset=_("Social Media")
    )
    homepage_image_1 = StringField(
        label=_("Homepage Image #1"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_2 = StringField(
        label=_("Homepage Image #2"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_3 = StringField(
        label=_("Homepage Image #3"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_4 = StringField(
        label=_("Homepage Image #4"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_5 = StringField(
        label=_("Homepage Image #5"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_6 = StringField(
        label=_("Homepage Image #6"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_cover = HtmlField(
        label=_("Homepage Cover"),
        render_kw={'rows': 10},
        fieldset=_("Homepage")
    )
    homepage_structure = TextAreaField(
        label=_("Homepage Structure (for advanced users only)"),
        description=_("The structure of the homepage"),
        render_kw={'rows': 32, 'data-editor': 'xml'},
        fieldset=_("Homepage")
    )
    default_map_view = CoordinatesField(
        label=_("The default map view. This should show the whole town"),
        render_kw={
            'data-map-type': 'crosshair'
        },
        fieldset=_("Maps")
    )
    analytics_code = TextAreaField(
        label=_("Analytics Code"),
        description=_("JavaScript for web statistics support"),
        render_kw={'rows': 10},
        fieldset=_("Advanced")
    )
    # the footer height is determined by javascript, see org.scss and
    # common.js for more information (search for footer)
    footer_height = HiddenField()

    def validate_homepage_structure(self, field):
        if field.data:
            try:
                transform_homepage_structure(self.request.app, field.data)
            except etree.XMLSyntaxError as e:
                correct_line = e.position[0] - XML_LINE_OFFSET

                correct_msg = 'line {}'.format(correct_line)
                correct_msg = ERROR_LINE_RE.sub(correct_msg, e.msg)

                field.widget = with_options(
                    field.widget, **{'data-highlight-line': correct_line}
                )

                raise ValidationError(correct_msg)

    @property
    def theme_options(self):
        try:
            primary_color = self.primary_color.data.get_hex()
        except AttributeError:
            primary_color = user_options['primary-color']

        options = {
            'primary-color': primary_color,
            'footer-height': self.footer_height.data
        }

        # set the images only if provided
        for i in range(1, 7):
            image = getattr(self, 'homepage_image_{}'.format(i)).data

            if not image:
                continue

            options['tile-image-{}'.format(i)] = '"{}"'.format(image)

        # override the options using the default vaules if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        return options

    def ensure_beneificary_if_bank_account(self):
        if self.bank_account.data and not self.bank_beneficiary.data:
            self.bank_beneficiary.errors.append(_(
                "A beneficiary is required if a bank account is given."
            ))
            return False

    @theme_options.setter
    def theme_options(self, options):
        self.primary_color.data = options.get('primary-color')
        self.footer_height.data = options.get('footer-height')
        self.homepage_image_1.data = options.get('tile-image-1', '').strip('"')
        self.homepage_image_2.data = options.get('tile-image-2', '').strip('"')
        self.homepage_image_3.data = options.get('tile-image-3', '').strip('"')
        self.homepage_image_4.data = options.get('tile-image-4', '').strip('"')
        self.homepage_image_5.data = options.get('tile-image-5', '').strip('"')
        self.homepage_image_6.data = options.get('tile-image-6', '').strip('"')
