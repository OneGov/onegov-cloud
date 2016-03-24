from onegov.form import Form
from onegov.form.fields import CoordinateField
from onegov.gis import _
from wtforms import RadioField
from wtforms.validators import InputRequired


class CoordinateForm(Form):

    coordinate_enabled = RadioField(
        label=_("Show on map"),
        fieldset=_("Map"),
        choices=[
            ('no', _("No")),
            ('yes', _("Yes")),
        ],
        validators=[InputRequired()],
        default='no'
    )

    coordinate = CoordinateField(
        label=_("Coordinate"),
        fieldset=_("Map"),
        validators=[InputRequired()],
        depends_on=('coordinate_enabled', 'yes')
    )
