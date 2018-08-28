from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes.fields import SwissvoteDatasetField
from wtforms.validators import DataRequired


class UpdateDatasetForm(Form):

    dataset = SwissvoteDatasetField(
        label=_("Dataset"),
        validators=[
            DataRequired()
        ]
    )
