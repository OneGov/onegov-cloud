from __future__ import annotations

from base64 import b64decode, b64encode
from markupsafe import Markup
from onegov.core.custom import json
from onegov.form.display import registry, BaseRenderer
from onegov.gis.forms.widgets import CoordinatesWidget
from onegov.gis.models import Coordinates
from wtforms.fields import StringField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from onegov.form.types import (
        FormT, PricingRules, RawFormValue, Validators)
    from onegov.gis.models.coordinates import AnyCoordinates
    from typing import Self
    from wtforms.fields.core import _Filter, _Widget
    from wtforms.form import BaseForm
    from wtforms.meta import _SupportsGettextAndNgettext, DefaultMeta


class CoordinatesField(StringField):
    """ Represents a single pair of coordinates with optional zoom and
    marker icon/color selection.

    In the browser and during transit the point is stored as a base64 encoded
    json string on a simple input field. For example::

        eydsYXQnOiA4LjMwNTc2ODY5MTczODc5LCAnbG.. (and so on)

        =>

        {'lon': 8.30576869173879, 'lat': 47.05183585, 'zoom': 10}

    For verification: This points to the Seantis office in Lucerne.

    For convenience, the coordinates are accessible with the
    :class:`onegov.gis.models.coordinates.Coordinates` class when 'data' is
    used.

    Note that this field doesn't work with the ``InputRequired`` validator.
    Instead the ``DataRequired`` validator has to be chosen.

    """

    data: AnyCoordinates  # type:ignore[assignment]
    widget: _Widget[Self] = CoordinatesWidget()

    def __init__(
        self,
        label: str | None = None,
        validators: Validators[FormT, Self] | None = None,
        filters: Sequence[_Filter] = (),
        description: str = '',
        id: str | None = None,
        default: AnyCoordinates | Callable[[], AnyCoordinates] | None = None,
        widget: _Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        _form: BaseForm | None = None,
        _prefix: str = '',
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        *,
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
    ):
        super().__init__(
            label=label,
            validators=validators,
            filters=filters,
            description=description,
            id=id,
            default=default,  # type:ignore[arg-type]
            widget=widget,
            render_kw=render_kw,
            name=name,
            _form=_form,
            _prefix=_prefix,
            _translations=_translations,
            _meta=_meta
        )
        self.data = getattr(self, 'data', Coordinates())

    def _value(self) -> str:
        text = b'{}' if self.data is None else json.dumps_bytes(self.data)
        text = b64encode(text)

        return text.decode('ascii')

    def process_data(self, value: object) -> None:
        if isinstance(value, dict):
            self.data = Coordinates(**value)
        elif isinstance(value, Coordinates):
            self.data = value
        else:
            self.data = Coordinates()

    def populate_obj(self, obj: object, name: str) -> None:
        setattr(obj, name, self.data)

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if valuelist and valuelist[0]:
            assert isinstance(valuelist[0], str)
            data = json.loads(b64decode(valuelist[0]))

            # if the data we receive doesn't result in a coordinates value
            # for some reason, we create one
            if not isinstance(data, Coordinates):
                data = Coordinates()

            self.data = data
        else:
            self.data = Coordinates()


@registry.register_for('CoordinatesField')
class CoordinatesFieldRenderer(BaseRenderer):
    def __call__(self, field: CoordinatesField) -> Markup:  # type:ignore
        return Markup("""
            <div class="marker-map"
                 data-map-type="thumbnail"
                 data-lat="{lat}"
                 data-lon="{lon}"
                 data-zoom="{zoom}">
                 {lat}, {lon}
            </div>
        """).format(
            lat=field.data.lat,
            lon=field.data.lon,
            zoom=field.data.zoom
        )
