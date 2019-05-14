from datetime import date
from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.wtfs import _
from onegov.wtfs.fields import MunicipalityDataUploadField
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PaymentType
from onegov.wtfs.models import PickupDate
from sqlalchemy import func
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class MunicipalityForm(Form):

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ]
    )

    bfs_number = IntegerField(
        label=_("BFS number"),
        validators=[
            InputRequired()
        ]
    )

    address_supplement = StringField(
        label=_("Address supplement"),
    )

    gpn_number = IntegerField(
        label=_("GPN number"),
        validators=[
            Optional()
        ]
    )

    payment_type = RadioField(
        label=_("Payment type"),
        validators=[InputRequired()]
    )

    def on_request(self):
        query = self.request.session.query(PaymentType.name)
        self.payment_type.choices = [
            (r.name, r.name.capitalize()) for r in query
        ]

    def update_model(self, model):
        model.name = self.name.data
        model.bfs_number = self.bfs_number.data
        model.address_supplement = self.address_supplement.data
        model.gpn_number = self.gpn_number.data
        model.payment_type = self.payment_type.data

    def apply_model(self, model):
        self.name.data = model.name
        self.bfs_number.data = model.bfs_number
        self.address_supplement.data = model.address_supplement
        self.gpn_number.data = model.gpn_number
        self.payment_type.data = model.payment_type


class ImportMunicipalityDataForm(Form):

    file = MunicipalityDataUploadField(
        label=_("File"),
        validators=[
            DataRequired()
        ]
    )

    def update_model(self, model):
        model.import_data(self.file.data)


class DeleteMunicipalityDatesForm(Form):

    start = DateField(
        label=_("Start date"),
        validators=[
            DataRequired()
        ]
    )

    end = DateField(
        label=_("End date"),
        validators=[
            DataRequired()
        ]
    )

    def update_model(self, model):
        dates = model.pickup_dates
        dates = dates.filter(PickupDate.date >= self.start.data)
        dates = dates.filter(PickupDate.date <= self.end.data)
        for date_ in dates:
            self.request.session.delete(date_)

    def apply_model(self, model):
        start = model.pickup_dates.filter(
            func.extract('year', PickupDate.date) == date.today().year
        ).first()
        self.start.data = start.date if start else None

        end = model.pickup_dates.order_by(None)
        end = end.order_by(PickupDate.date.desc()).first()
        self.end.data = end.date if end else None


class MunicipalityIdSelectionForm(Form):

    municipality_id = SelectField(
        label=_("Municipality"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [(r.id.hex, r.name) for r in query]

    @property
    def municipality(self):
        if self.municipality_id.data:
            query = self.request.session.query(Municipality)
            query = query.filter(Municipality.id == self.municipality_id.data)
            return query.first()
