from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
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
        model.html = self.get_html(request)

    def apply_model(self, model):
        self.title.data = model.title
        self.editorial.data = model.meta.get('editorial', '')

    def get_html(self, request):
        return ''

    @classmethod
    def with_news(cls, request, news, default):

        choices = [
            (str(item.id), item.title) for item in news
        ]

        class NewsletterWithNewsForm(cls):

            news = MultiCheckboxField(
                label=_("Latest news"),
                choices=choices,
                render_kw={
                    'prefix_label': False
                }
            )

            def update_model(self, model, request):
                super().update_model(model, request)
                model.content['news'] = self.news.data

            def apply_model(self, model):
                super().apply_model(model)
                self.news.data = model.content['news']

        return NewsletterWithNewsForm
