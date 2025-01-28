from __future__ import annotations

from onegov.form import Form
from onegov.org import _
from wtforms.fields import BooleanField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired


class ImageSetForm(Form):
    title = StringField(_('Title'), [InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes what this photo album is about'),
        render_kw={'rows': 4})

    view = RadioField(
        label=_('View'),
        default='full',
        choices=[
            ('full', _('Full size images')),
            ('grid', _('Grid layout'))
        ])

    show_images_on_homepage = BooleanField(
        label=_('Show images on homepage'))

    order = RadioField(
        label=_('Order'),
        fieldset=_('Order'),
        choices=[
            ('by-name', _('By filename')),
            ('by-caption', _('By caption')),
            ('by-last-change', _('By last change'))
        ],
        default='by-last-change')

    order_direction = RadioField(
        label=_('Direction'),
        fieldset=_('Order'),
        choices=[
            ('asc', _('Ascending')),
            ('desc', _('Descending'))
        ],
        default='desc')
