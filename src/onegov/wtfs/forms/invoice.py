from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.wtfs import _
from onegov.wtfs.models import Municipality
from wtforms import SelectField
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


class CreateInvoicesForm(Form):

    from_date = DateField(
        label=_("From date"),
        validators=[
            InputRequired(),
        ]
    )

    to_date = DateField(
        label=_("To date"),
        validators=[
            InputRequired(),
        ]
    )

    cs2_user = StringField(
        label=_("CS2 User"),
        validators=[
            InputRequired(),
        ]
    )

    subject = StringField(
        label=_("Subject"),
        validators=[
            InputRequired(),
        ]
    )

    municipality_id = SelectField(
        label=_("Municipality"),
        choices=[],
        validators=[InputRequired()]
    )

    accounting_unit = StringField(
        label=_("Accounting unit"),
        validators=[
            InputRequired(),
        ]
    )

    revenue_account = StringField(
        label=_("Revenue account"),
        validators=[
            InputRequired(),
        ]
    )

    def on_request(self):
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number'),
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [
            ('-', self.request.translate(_("For all municipalities")))
        ]
        self.municipality_id.choices += [
            (r.id.hex, f"{r.name} ({r.bfs_number})") for r in query
        ]

    def update_model(self, model):
        model.from_date = self.from_date.data
        model.to_date = self.to_date.data
        model.cs2_user = self.cs2_user.data
        model.subject = self.subject.data
        model.municipality_id = None
        if self.municipality_id.data != '-':
            model.municipality_id = self.municipality_id.data
        model.accounting_unit = self.accounting_unit.data
        model.revenue_account = self.revenue_account.data
