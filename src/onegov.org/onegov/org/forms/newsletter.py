from datetime import timedelta
from onegov.core.layout import Layout
from onegov.file.utils import name_without_extension
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.newsletter import Recipient
from onegov.org import _
from sedate import replace_timezone, to_timezone, utcnow
from wtforms import RadioField, StringField, TextAreaField, validators
from wtforms import ValidationError
from wtforms.fields.html5 import DateTimeField


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

        if not choices:
            return cls

        class NewsletterWithNewsForm(cls):

            news = MultiCheckboxField(
                label=_("Latest news"),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                }
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

        layout = Layout(None, request)

        choices = tuple(
            (
                str(item.id),
                '<div class="title">{}</div><div class="date">{}</div>'.format(
                    item.title, layout.format_date(
                        item.localized_start, 'datetime'
                    )
                )
            ) for item in occurrences
        )

        if not choices:
            return cls

        class NewsletterWithOccurrencesForm(cls):

            occurrences = MultiCheckboxField(
                label=_("Events"),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                }
            )

            def update_model(self, model, request):
                super().update_model(model, request)
                model.content['occurrences'] = self.occurrences.data

            def apply_model(self, model):
                super().apply_model(model)
                self.occurrences.data = model.content.get('occurrences')

        return NewsletterWithOccurrencesForm

    @classmethod
    def with_publications(cls, request, publications):

        layout = Layout(None, request)

        choices = tuple(
            (
                str(item.id),
                '<div class="title">{}</div><div class="date">{}</div>'.format(
                    name_without_extension(item.name),
                    layout.format_date(item.created, 'date')
                )
            ) for item in publications
        )

        if not choices:
            return cls

        class NewsletterWithPublicationsForm(cls):

            publications = MultiCheckboxField(
                label=_("Publications"),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                }
            )

            def update_model(self, model, request):
                super().update_model(model, request)
                model.content['publications'] = self.publications.data

            def apply_model(self, model):
                super().apply_model(model)
                self.publications.data = model.content.get('publications')

        return NewsletterWithPublicationsForm


class NewsletterSendForm(Form):

    send = RadioField(
        _("Send"),
        choices=(
            ('now', _("Now")),
            ('specify', _("At a specified time"))
        ),
        default='now'
    )

    time = DateTimeField(
        _("Time"),
        validators=[validators.InputRequired()],
        depends_on=('send', 'specify')
    )

    def validate_time(self, field):
        if not field.data:
            return

        from onegov.org.layout import DefaultLayout  # XXX circular import
        layout = DefaultLayout(self.model, self.request)

        if self.send.data == 'specify':
            time = replace_timezone(field.data, layout.timezone)
            time = to_timezone(time, 'UTC')

            if time < (utcnow() + timedelta(seconds=60 * 5)):
                raise ValidationError(_(
                    "Scheduled time must be at least 5 minutes in the future"
                ))

            if time.minute != 0:
                raise ValidationError(_(
                    "Newsletters can only be sent on the hour "
                    "(10:00, 11:00, etc.)"
                ))

            self.time.data = time


class NewsletterTestForm(Form):

    @classmethod
    def build(cls, newsletter, request):
        recipients = request.session.query(Recipient)\
            .with_entities(Recipient.id, Recipient.address)\
            .filter_by(confirmed=True)

        choices = tuple((r.id.hex, r.address) for r in recipients)

        class NewsletterSendFormWithRecipients(cls):

            selected_recipient = RadioField(
                label=_("Recipient"),
                choices=choices,
            )

            @property
            def recipient(self):
                return request.session.query(Recipient)\
                    .filter_by(id=self.selected_recipient.data)\
                    .one()

        return NewsletterSendFormWithRecipients
