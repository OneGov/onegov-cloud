from onegov.core.layout import Layout
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from wtforms import StringField, TextAreaField, validators


class NewsletterForm(Form):

    title = StringField(
        label=_("Title"),
        description=_("Used in the overview and the e-mail subject"),
        validators=[validators.InputRequired()])

    lead = TextAreaField(
        label=_("Editorial"),
        description=_("A few words about this edition of the newsletter"),
        render_kw={'rows': 6})

    def update_model(self, model, request):
        model.title = self.title.data
        model.lead = self.lead.data
        model.html = self.get_html(request)

    def apply_model(self, model):
        self.title.data = model.title
        self.lead.data = model.lead

    def get_html(self, request):
        return ''

    @classmethod
    def with_news(cls, request, news):

        layout = Layout(None, request)

        choices = tuple((
            str(item.id),
            '<div class="title">{}</div><div class="date">{}</div>'.format(
                item.title,
                layout.format_date(item.created, 'relative')
            )
        ) for item in news)

        class NewsletterWithNewsForm(cls):

            news = MultiCheckboxField(
                label=_("Latest news"),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                },
                fieldset=_("Selected News / Events")
            )

            def update_model(self, model, request):
                super().update_model(model, request)
                model.content['news'] = self.news.data

            def apply_model(self, model):
                super().apply_model(model)
                self.news.data = model.content.get('news')

        return NewsletterWithNewsForm

    @classmethod
    def with_occurrences(cls, request, occurrences):

        choices = tuple(
            (
                str(item.id),
                '<div class="title">{}</div><div class="date">{}</div>'.format(
                    item.title, item.localized_start.strftime('%d.%m.%Y %H:%M')
                )
            ) for item in occurrences
        )

        class NewsletterWithOccurrencesForm(cls):

            occurrences = MultiCheckboxField(
                label=_("Events"),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                },
                fieldset=_("Selected News / Events")
            )

            def update_model(self, model, request):
                super().update_model(model, request)
                model.content['occurrences'] = self.occurrences.data

            def apply_model(self, model):
                super().apply_model(model)
                self.occurrences.data = model.content.get('occurrences')

        return NewsletterWithOccurrencesForm


class NewsletterSendForm(Form):

    @classmethod
    def for_newsletter(cls, newsletter, recipients):
        choices = tuple(
            (
                (recipient.id.hex, recipient.address)
                for recipient in recipients
                if recipient.confirmed and
                recipient not in newsletter.recipients
            )
        )

        class NewsletterSendFormWithRecipients(cls):

            recipients = MultiCheckboxField(
                label=_("Recipients"),
                choices=choices,
                default=tuple(c[0] for c in choices),
                render_kw={
                    'prefix_label': False
                },
            )

            def validate_recipients(self, field):
                if len(field.data) == 0:
                    raise validators.ValidationError(
                        _("Please select at least one recipient")
                    )

        return NewsletterSendFormWithRecipients
