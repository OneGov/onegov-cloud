from __future__ import annotations

from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes.fields import SwissvoteDatasetField
from onegov.swissvotes.fields import SwissvoteMetadataField
from wtforms.validators import DataRequired


class UpdateDatasetForm(Form):

    callout = _('Updating the dataset may take some time.')

    dataset = SwissvoteDatasetField(
        label=_('Dataset'),
        validators=[
            DataRequired()
        ]
    )


class UpdateMetadataForm(Form):

    callout = _('Updating the metadata may take some time.')

    metadata = SwissvoteMetadataField(
        label=_('Metadata'),
        validators=[
            DataRequired()
        ]
    )
