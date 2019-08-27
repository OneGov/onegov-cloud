from onegov.form import Form
from wtforms import FloatField
from wtforms.validators import InputRequired


class PaymentTypesForm(Form):

    @staticmethod
    def get_form_class(model, request):
        form = PaymentTypesForm
        for payment_type in model.query().all():
            field = FloatField(
                payment_type.name.capitalize(),
                validators=[InputRequired()]
            )
            setattr(form, payment_type.name, field)
        return form

    def update_model(self, model):
        for field in self:
            payment_type = model.query().filter_by(name=field.name).first()
            if payment_type:
                payment_type.price_per_quantity = field.data

    def apply_model(self, model):
        for field in self:
            payment_type = model.query().filter_by(name=field.name).first()
            if payment_type:
                field.data = payment_type.price_per_quantity
