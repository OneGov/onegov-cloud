from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.pas import _
from onegov.pas.models import RateSet
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


def default_year() -> int:
    return date.today().year


class RateSetForm(Form):

    year = IntegerField(
        label=_('Year'),
        validators=[InputRequired()],
        default=default_year
    )

    cost_of_living_adjustment = DecimalField(
        label=_('Cost of living adjustment'),
        render_kw={'long_description': _('Percentage')},
        validators=[InputRequired()],
    )

    plenary_none_president_halfday = IntegerField(
        label=_('President'),
        fieldset=_('Plenary session'),
        render_kw={'long_description': _('half-day')},
        validators=[InputRequired()],
    )

    plenary_none_member_halfday = IntegerField(
        label=_('Member'),
        fieldset=_('Plenary session'),
        render_kw={'long_description': _('half-day')},
        validators=[InputRequired()],
    )

    commission_normal_president_initial = IntegerField(
        label=_('President'),
        fieldset=_('Commission meeting'),
        render_kw={
            'long_description': _('first 2h'),
            'size': 3
        },
        validators=[InputRequired()],
    )

    commission_normal_president_additional = IntegerField(
        label=_('President'),
        render_kw={
            'long_description': _('per additional 1/2h'),
            'size': 3,
            'offset': 1
        },
        fieldset=_('Commission meeting'),
        validators=[InputRequired()],
    )

    study_normal_president_halfhour = IntegerField(
        label=_('President: File study'),
        render_kw={
            'long_description': _('per 1/2h'),
            'size': 4,
            'offset': 1
        },
        fieldset=_('Commission meeting'),
        validators=[InputRequired()],
    )

    commission_normal_member_initial = IntegerField(
        label=_('Member'),
        render_kw={
            'long_description': _('first 2h'),
            'size': 3,
        },
        fieldset=_('Commission meeting'),
        validators=[InputRequired()],
    )

    commission_normal_member_additional = IntegerField(
        label=_('Member'),
        render_kw={
            'long_description': _('per additional 1/2h'),
            'size': 3,
            'offset': 1
        },
        fieldset=_('Commission meeting'),
        validators=[InputRequired()],
    )

    study_normal_member_halfhour = IntegerField(
        label=_('Member: File study'),
        render_kw={
            'long_description': _('per 1/2h'),
            'size': 4,
            'offset': 1
        },
        fieldset=_('Commission meeting'),
        validators=[InputRequired()],
    )

    commission_intercantonal_president_halfday = IntegerField(
        label=_('President'),
        render_kw={
            'long_description': _('half-day'),
            'size': 7,
        },
        fieldset=_('intercantonal commission'),
        validators=[InputRequired()],
    )

    study_intercantonal_president_hour = IntegerField(
        label=_('President: File study'),
        render_kw={
            'long_description': _('per 1h'),
            'size': 4,
            'offset': 1
        },
        fieldset=_('intercantonal commission'),
        validators=[InputRequired()],
    )

    commission_intercantonal_member_halfday = IntegerField(
        label=_('Member'),
        render_kw={
            'long_description': _('half-day'),
            'size': 7,
        },
        fieldset=_('intercantonal commission'),
        validators=[InputRequired()],
    )

    study_intercantonal_member_hour = IntegerField(
        label=_('Member: File study'),
        render_kw={
            'long_description': _('per 1h'),
            'size': 4,
            'offset': 1
        },
        fieldset=_('intercantonal commission'),
        validators=[InputRequired()],
    )

    commission_official_president_halfday = IntegerField(
        label=_('President'),
        render_kw={
            'long_description': _('half-day'),
            'size': 3
        },
        fieldset=_('official mission'),
        validators=[InputRequired()],
    )

    commission_official_president_fullday = IntegerField(
        label=_('President'),
        render_kw={
            'long_description': _('full-day'),
            'size': 3,
            'offset': 1
        },
        fieldset=_('official mission'),
        validators=[InputRequired()],
    )

    study_official_president_halfhour = IntegerField(
        label=_('President: File study'),
        render_kw={
            'long_description': _('per 1/2h'),
            'size': 4,
            'offset': 1
        },
        fieldset=_('official mission'),
        validators=[InputRequired()],
    )

    commission_official_vice_president_halfday = IntegerField(
        label=_('Vice president'),
        render_kw={
            'long_description': _('half-day'),
            'size': 3,
        },
        fieldset=_('official mission'),
        validators=[InputRequired()],
    )

    commission_official_vice_president_fullday = IntegerField(
        label=_('Vice president'),
        render_kw={
            'long_description': _('full-day'),
            'size': 3,
            'offset': 1
        },
        fieldset=_('official mission'),
        validators=[InputRequired()],
    )

    study_official_member_halfhour = IntegerField(
        label=_('Vice president: File study'),
        render_kw={
            'long_description': _('per 1/2h'),
            'size': 4,
            'offset': 1
        },
        fieldset=_('official mission'),
        validators=[InputRequired()],
    )

    shortest_all_president_halfhour = IntegerField(
        label=_('President'),
        render_kw={'long_description': _('per 1/2h')},
        fieldset=_('Shortest meeting'),
        validators=[InputRequired()],
    )

    shortest_all_member_halfhour = IntegerField(
        label=_('Member'),
        render_kw={'long_description': _('per 1/2h')},
        fieldset=_('Shortest meeting'),
        validators=[InputRequired()],
    )

    def validate_year(self, field: IntegerField) -> None:
        if field.data is not None:
            query = self.request.session.query(RateSet)
            query = query.filter(RateSet.year == field.data)
            if isinstance(self.model, RateSet):
                query = query.filter(RateSet.id != self.model.id)
            if query.first():
                raise ValidationError(_(
                    'Rate set for ${year} alredy exists',
                    mapping={'year': field.data}
                ))
