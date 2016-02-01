from onegov.form import Form
from onegov.town import _
from wtforms import StringField, TextAreaField, validators


class NewsletterForm(Form):

    title = StringField(
        label=_("Title"),
        description=_("Used in the overview and the e-mail subject"),
        validators=[validators.InputRequired()])

    editorial = TextAreaField(
        label=_("Editorial"),
        description=_("A few words about this edition of the newsletter"),
        render_kw={'rows': 6})

    def update_model(self, model, request):
        model.title = self.title.data
        model.meta['editorial'] = self.editorial.data
        model.content = self.get_content(request)

    def apply_model(self, model):
        self.title.data = model.title
        self.editorial.data = model.meta.get('editorial', '')

    def get_content(self, request):
        return ''
