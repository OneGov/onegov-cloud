from wtforms import SelectField
from onegov.fsi import _
from onegov.form import Form
from onegov.form.fields import TimezoneDateTimeField

from wtforms import StringField, RadioField
from wtforms.validators import InputRequired

from onegov.form.fields import HtmlField
from onegov.fsi import _
from onegov.form import Form


class CourseEventForm(Form):

    name = StringField(
        label=_('Short Description'),
        render_kw={'size': 4},
        description=_('Short title of the course'),
        validators=[
            InputRequired()
        ]

    )

    presenter_name = StringField(
        label=_('Presenter'),
        render_kw={'size': 4},
        description=_('Full name of the presenter'),
        validators=[
            InputRequired()
        ]
    )

    presenter_company = StringField(
        label=_('Company'),
        description='Presenters company',
        render_kw={'size': 4},
        validators=[
            InputRequired()
        ]
    )

    mandatory_refresh = RadioField(
        label=_("Refresh mandatory"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        coerce=bool,
        render_kw={'size': 4},
        description=_(
            "Define if this course has a refresh. The refresh"
        )
    )

    hidden_from_public = RadioField(
        label=_("Hide from public"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        coerce=bool,
        render_kw={'size': 4},
        description=_(
            "If checked, the course will only be visible by admin"
        )
    )

    description = HtmlField(
        label=_("Description"),
        render_kw={'rows': 10},
        validators=[
            InputRequired()
        ]
    )

    def apply_model(self, model):
        self.name.data = model.name
        self.presenter_name.data = model.presenter_name
        self.presenter_company = model.presenter_company
        self.description = model.description
        self.mandatory_refresh = model.mandatory_refresh
        self.hidden_from_public = model.hidden_from_public

    def update_model(self, model):
        model.name = self.name.data
        model.presenter_name = self.presenter_name.data
        model.presenter_company = self.presenter_company.data
        model.description = self.description
        model.mandatory_refresh = self.mandatory_refresh
        model.hidden_from_public = self.hidden_from_public



# class CourseEventForm(Form):
#
#     course = SelectField(
#         label=_('Course'),
#         render_kw={'size': 4}
#     )
#
#
#     start = TimezoneDateTimeField(
#         label=_('Course Start'),
#         render_kw={'size': 4}
#     )
#
#     end = TimezoneDateTimeField(
#         label=_('Course End')
#     )