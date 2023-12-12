from datetime import timedelta
import transaction
from sqlalchemy.exc import IntegrityError
from wtforms.validators import DataRequired
from onegov.core.csv import convert_excel_to_csv, CSVFile
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import BooleanField
from onegov.core.layout import Layout
from onegov.file.utils import name_without_extension
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import DateTimeLocalField
from onegov.form.fields import MultiCheckboxField
from onegov.newsletter import Recipient, RecipientCollection
from onegov.org import _
from sedate import replace_timezone, to_timezone, utcnow
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError
from markupsafe import Markup


class NewsletterForm(Form):
    title = StringField(
        label=_("Title"),
        description=_("Used in the overview and the e-mail subject"),
        validators=[InputRequired()])

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

        choices = tuple(
            (
                str(item.id),
                Markup(
                    '<div class="title">{}</div>'
                    '<div class="date">{}</div>'
                ).format(
                    item.title,
                    layout.format_date(item.created, 'relative')
                )
            )
            for item in news
        )

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
                Markup(
                    '<div class="title">{}</div>'
                    '<div class="date">{}</div>'
                ).format(
                    item.title,
                    layout.format_date(item.localized_start, 'datetime')
                )
            )
            for item in occurrences
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
                Markup(
                    '<div class="title">{}</div>'
                    '<div class="date">{}</div>'
                ).format(
                    name_without_extension(item.name),
                    layout.format_date(item.created, 'date')
                )
            )
            for item in publications
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

    time = DateTimeLocalField(
        label=_("Time"),
        validators=[InputRequired()],
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
            selected_recipient = ChosenSelectField(
                label=_("Recipient"),
                choices=choices,
            )

            @property
            def recipient(self):
                return request.session.query(Recipient)\
                    .filter_by(id=self.selected_recipient.data)\
                    .one()

        return NewsletterSendFormWithRecipients


class NewsletterSubscriberImportExportForm(Form):

    dry_run = BooleanField(
        label=_("Dry Run"),
        description=_("Do not actually import the newsletter subscribers"),
        default=False
    )

    file = UploadField(
        label=_("Import"),
        validators=[
            DataRequired(),
            WhitelistedMimeType({
                'application/excel',
                'application/vnd.ms-excel',
                (
                    'application/'
                    'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
                'application/vnd.ms-office',
                'application/octet-stream',
                'application/zip',
                'text/csv',
                'text/plain',
            }),
            FileSizeLimit(10 * 1024 * 1024)
        ],
        render_kw={'force_simple': True}
    )

    @property
    def headers(self):
        return {
            'address': self.request.translate(_("Address")),
        }

    def run_export(self):
        recipients = RecipientCollection(self.request.session)
        headers = self.headers

        def get(recipient, attribute):
            result = getattr(recipient, attribute, "")
            result = result.strip()
            return result

        result = []
        for recipient in recipients.query():
            result.append({
                v: get(recipient, k)
                for k, v in headers.items()
            })
        return result

    def run_import(self):
        headers = self.headers
        session = self.request.session
        recipients = RecipientCollection(session)
        try:
            csvfile = convert_excel_to_csv(self.file.file)
        except Exception:
            return 0, ['0']

        try:
            # dialect needs to be set, else error
            csv = CSVFile(csvfile, dialect='excel')
        except Exception:
            return 0, ['0']

        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        def get(line, column):
            return getattr(line, column)

        count = 0
        errors = []
        for number, line in enumerate(lines, start=1):
            try:
                kwargs = {
                    attribute: get(line, column)
                    for attribute, column in columns.items()
                }
                kwargs['confirmed'] = True
                recipients.add(**kwargs)
                count += 1
            except IntegrityError:
                message = str(number) + self.request.translate(
                    _(': (Address already exists)')
                )
                errors.append(message)
            except Exception:
                errors.append(str(number))

        if self.dry_run.data or errors:
            transaction.abort()

        return count, errors
