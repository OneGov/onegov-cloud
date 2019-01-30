from onegov.form import Form
from onegov.wtfs import _
from wtforms import IntegerField
from wtforms import StringField
from wtforms.validators import InputRequired


class MunicipalityForm(Form):

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ]
    )

    bfs_number = IntegerField(
        label=_("BFS Number"),
        validators=[
            InputRequired()
        ]
    )

    def update_model(self, model):
        model.name = self.name.data
        model.bfs_number = self.bfs_number.data

    def apply_model(self, model):
        self.name.data = model.name
        self.bfs_number.data = model.bfs_number
