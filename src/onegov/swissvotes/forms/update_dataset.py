from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes.fields import SwissvoteDatasetField
from wtforms.validators import DataRequired


class UpdateDatasetForm(Form):

    callout = _("Updating the dataset may take some time.")

    dataset = SwissvoteDatasetField(
        label=_("Dataset"),
        validators=[
            DataRequired()
        ]
    )
