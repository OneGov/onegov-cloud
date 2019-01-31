from onegov.form import Form
from onegov.wtfs import _
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms.validators import InputRequired
from onegov.wtfs.models import Municipality
from onegov.user import UserGroup
from sqlalchemy import func
from sqlalchemy import String


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

    group_id = SelectField(
        label=_("User group"),
        choices=[],
    )

    def on_request(self):
        session = self.request.session

        used_groups = session.query(Municipality.group_id)
        used_groups = used_groups.filter(Municipality.group_id.isnot(None))
        used_groups = used_groups.all()

        groups = session.query(func.cast(UserGroup.id, String), UserGroup.name)
        if used_groups:
            groups = groups.filter(UserGroup.id.notin_(used_groups))
        groups = groups.order_by(UserGroup.name)
        self.group_id.choices = groups.all()
        self.group_id.choices.insert(0, ('', ''))

    def add_group(self, group):
        if group and (str(group.id), group.name) not in self.group_id.choices:
            self.group_id.choices.insert(0, (str(group.id), group.name))

    def update_model(self, model):
        model.name = self.name.data
        model.bfs_number = self.bfs_number.data
        model.group_id = self.group_id.data or None

    def apply_model(self, model):
        self.name.data = model.name
        self.bfs_number.data = model.bfs_number
        self.group_id.data = str(model.group_id) if model.group_id else ''
