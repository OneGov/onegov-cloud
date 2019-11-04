from wtforms import StringField, RadioField

from onegov.form.fields import HtmlField
from onegov.fsi import _
from onegov.form import Form


class EditCourseForm(Form):

    name = StringField(
        label=_('Name'),
        render_kw={'size': 4},
        description=_('Short title of the course')
    )

    description = HtmlField(
        label=_("Description"),
        render_kw={'rows': 10}
    )

    presenter_name = StringField(
        label=_('Presenter'),
        description=_('Full name of the presenter')
    )

    presenter_company = StringField(
        label=_('Company'),
        description='Presenters company',
        render_kw={'size': 4}
    )

    mandatory_refresh = RadioField(
        label=_("Refresh mandatory"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        coerce=bool,
        render_kw={'size': 2},
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
        render_kw={'size': 2},
        description=_(
            "If checked, the course will only be visible by admins"
        )
    )


