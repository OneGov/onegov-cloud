from wtforms import StringField, TextAreaField

from onegov.form import Form
from onegov.fsi import _


class NotificationForm(Form):

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
