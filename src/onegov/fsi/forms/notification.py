from wtforms import SelectField, StringField, TextAreaField

from onegov.form import Form
from onegov.fsi import _
from onegov.fsi.models.notification_template import template_type_choices


class NotificationForm(Form):
    # type = SelectField(
    #     label=_('Notification Type'),
    #     choices=template_type_choices(),
    #     render_kw={'size': 3}
    # )

    subject = StringField(
        label=_('Email Subject'),
        render_kw={'size': 6, 'clear': True}
    )

    text = TextAreaField(
        label=_('Email Text'),
        render_kw={'rows': 10, 'cols': 12}
    )

    def apply_model(self, model):
        # self.type.data = model.type
        self.subject.data = model.subject
        self.text.data = model.text

    def update_model(self, model):
        # model.type = self.type.data
        model.subject = self.subject.data
        model.text = self.text.data



