from onegov.form import Form
from wtforms.fields import FloatField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.wtfs.collections import PaymentTypeCollection


class PaymentTypesForm(Form):

    @staticmethod
    def get_form_class(
        model: 'PaymentTypeCollection',
        request: 'CoreRequest'
    ) -> type['PaymentTypesForm']:
        form = PaymentTypesForm
        for payment_type in model.query().all():
            field = FloatField(
                payment_type.name.capitalize(),
                validators=[InputRequired()]
            )
            setattr(form, payment_type.name, field)
        return form

    def update_model(self, model: 'PaymentTypeCollection') -> None:
        for field in self:
            payment_type = model.query().filter_by(name=field.name).first()
            if payment_type:
                payment_type.price_per_quantity = field.data

    def apply_model(self, model: 'PaymentTypeCollection') -> None:
        for field in self:
            payment_type = model.query().filter_by(name=field.name).first()
            if payment_type:
                field.data = payment_type.price_per_quantity
