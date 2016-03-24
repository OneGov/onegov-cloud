from onegov.form import Form
from onegov.gis import _
from onegov.gis.forms.fields import MapPointField
from wtforms import RadioField
from wtforms.validators import InputRequired


class MapPointForm(Form):

    map_point_enabled = RadioField(
        label=_("Show on map"),
        fieldset=_("Map"),
        choices=[
            ('no', _("No")),
            ('yes', _("Yes")),
        ],
        validators=[InputRequired()],
        default='no'
    )

    map_point = MapPointField(
        label=_("Coordinate"),
        fieldset=_("Map"),
        validators=[InputRequired()],
        depends_on=('coordinate_enabled', 'yes')
    )
