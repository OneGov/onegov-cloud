from __future__ import annotations

from collections import OrderedDict
from datetime import timedelta
import transaction
from wtforms.validators import DataRequired
from onegov.core.csv import convert_excel_to_csv, CSVFile
from onegov.form.fields import UploadField
from onegov.org.forms.fields import HtmlField
from onegov.org.utils import extract_categories_and_subcategories
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import BooleanField
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


from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Callable
    from onegov.core.csv import DefaultRow
    from onegov.file import File
    from onegov.event.models import Occurrence
    from onegov.org.models import News
    from onegov.org.request import OrgRequest
    from onegov.newsletter.models import Newsletter
    from typing import Self
    from wtforms.fields.choices import _Choice


class NewsletterForm(Form):
    title = StringField(
        label=_('Title'),
        description=_('Used in the overview and the e-mail subject'),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_('Editorial'),
        description=_('A few words about this edition of the newsletter'),
        render_kw={'rows': 6})

    closing_remark = HtmlField(
        label=_('Closing remark'),
        description=_('Closing remark at the end of the newsletter'),
        render_kw={'rows': 6},
    )

    # FIXME: Why are we passing the request in? It should alread be stored on
    #        the form itself.
    def update_model(self, model: Newsletter, request: OrgRequest) -> None:
        assert self.title.data is not None
        model.title = self.title.data
        model.lead = self.lead.data
        model.html = self.get_html(request)
        model.closing_remark = self.closing_remark.data

    def apply_model(self, model: Newsletter) -> None:
        self.title.data = model.title
        self.lead.data = model.lead
        self.closing_remark.data = model.closing_remark

    # FIXME: same here
    def get_html(self, request: OrgRequest) -> str:
        return ''

    @classmethod
    def with_news(
        cls,
        request: OrgRequest,
        news: Iterable[News]
    ) -> type[Self]:

        choices = tuple(
            (
                str(item.id),
                Markup(
                    '<div class="title">{}</div>'
                    '<div class="date">{}</div>'
                ).format(
                    item.title,
                    request.format_date(item.created, 'relative'),
                )
            )
            for item in news
        )

        if not choices:
            return cls

        class NewsletterWithNewsForm(cls):  # type:ignore
            news = MultiCheckboxField(
                label=_('Latest news'),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                }
            )
            show_news_as_tiles = BooleanField(
                label=_('Show news as tiles'),
                description=_(
                    'If checked, news are displayed as tiles. Otherwise, '
                    'news are listed in full length.'),
                default=True
            )

            def update_model(
                self,
                model: Newsletter,
                request: OrgRequest  # FIXME: same here
            ) -> None:

                super().update_model(model, request)
                model.content['news'] = self.news.data
                model.content['show_news_as_tiles'] = (
                    self.show_news_as_tiles.data)

            def apply_model(self, model: Newsletter) -> None:
                super().apply_model(model)
                self.news.data = model.content.get('news')
                self.show_news_as_tiles.data = model.content.get(
                    'show_news_as_tiles', True)

        return NewsletterWithNewsForm

    @classmethod
    def with_occurrences(
        cls,
        request: OrgRequest,
        occurrences: Iterable[Occurrence]
    ) -> type[Self]:

        choices = tuple(
            (
                str(item.id),
                Markup(
                    '<div class="title">{}</div>'
                    '<div class="date">{}</div>'
                ).format(
                    item.title,
                    request.format_date(
                        item.localized_start, 'dd.MM.yyyy HH:mm')
                )
            )
            for item in occurrences
        )

        if not choices:
            return cls

        class NewsletterWithOccurrencesForm(cls):  # type:ignore
            occurrences = MultiCheckboxField(
                label=_('Events'),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                }
            )

            def update_model(
                self,
                model: Newsletter,
                request: OrgRequest  # FIXME: same here
            ) -> None:

                super().update_model(model, request)
                model.content['occurrences'] = self.occurrences.data

            def apply_model(self, model: Newsletter) -> None:
                super().apply_model(model)
                self.occurrences.data = model.content.get('occurrences')

        return NewsletterWithOccurrencesForm

    @classmethod
    def with_publications(
        cls,
        request: OrgRequest,
        publications: Iterable[File]
    ) -> type[Self]:

        choices = tuple(
            (
                str(item.id),
                Markup(
                    '<div class="title">{}</div>'
                    '<div class="date">{}</div>'
                ).format(
                    name_without_extension(item.name),
                    request.format_date(item.created, 'dd.MM.yyyy')
                )
            )
            for item in publications
        )

        if not choices:
            return cls

        class NewsletterWithPublicationsForm(cls):  # type:ignore
            publications = MultiCheckboxField(
                label=_('Publications'),
                choices=choices,
                render_kw={
                    'prefix_label': False,
                    'class_': 'recommended'
                }
            )

            def update_model(
                self,
                model: Newsletter,
                request: OrgRequest  # FIXME: same here
            ) -> None:

                super().update_model(model, request)
                model.content['publications'] = self.publications.data

            def apply_model(self, model: Newsletter) -> None:
                super().apply_model(model)
                self.publications.data = model.content.get('publications')

        return NewsletterWithPublicationsForm


class NewsletterSendForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    categories = MultiCheckboxField(
        label=_('Categories'),
        description=_('Select categories the newsletter reports on. The '
                      'users will receive the newsletter only if it '
                      'reports on at least one of the categories the user '
                      'subscribed to.'),
        choices=[]
    )

    send = RadioField(
        _('Send'),
        choices=(
            ('now', _('Now')),
            ('specify', _('At a specified time'))
        ),
        default='now'
    )

    time = DateTimeLocalField(
        label=_('Time'),
        validators=[InputRequired()],
        depends_on=('send', 'specify')
    )

    def validate_time(self, field: DateTimeLocalField) -> None:
        if not field.data:
            return

        # FIXME: We should probably store the timezone on the request
        #        and make the attribute on Layout a pure forwarding
        #        of the one on the request
        from onegov.org.layout import DefaultLayout  # XXX circular import
        layout = DefaultLayout(self.model, self.request)

        if self.send.data == 'specify':
            time = replace_timezone(field.data, layout.timezone)
            time = to_timezone(time, 'UTC')

            if time < (utcnow() + timedelta(seconds=60 * 5)):
                raise ValidationError(_(
                    'Scheduled time must be at least 5 minutes in the future'
                ))

            if time.minute != 0:
                raise ValidationError(_(
                    'Newsletters can only be sent on the hour '
                    '(10:00, 11:00, etc.)'
                ))

            self.time.data = time

    def on_request(self) -> None:
        choices: list[_Choice] = []
        categories, subcategories = extract_categories_and_subcategories(
            self.request.app.org.newsletter_categories)

        for cat, sub in zip(categories, subcategories):
            choices.append((cat, cat))
            choices.extend((s, f'\xa0\xa0\xa0{s}') for s in sub)

        if not choices:
            self.delete_field('categories')
            return

        self.categories.choices = choices


class NewsletterTestForm(Form):
    selected_recipient = ChosenSelectField(
        label=_('Recipient'),
        choices=[],
    )

    @property
    def recipient(self) -> Recipient:
        return (
            self.request.session.query(Recipient)
            .filter_by(id=self.selected_recipient.data)
            .one()
        )

    def on_request(self) -> None:
        recipients = (
            self.request.session.query(Recipient)
            .with_entities(Recipient.id, Recipient.address)
            .filter_by(confirmed=True)
        )

        self.selected_recipient.choices = [
            (r.id.hex, r.address)
            for r in recipients
        ]


class NewsletterSubscriberImportExportForm(Form):

    dry_run = BooleanField(
        label=_('Dry Run'),
        description=_('Do not actually import the newsletter subscribers'),
        default=False
    )

    file = UploadField(
        label=_('Import'),
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
    def headers(self) -> dict[str, str]:
        return {
            'address': self.request.translate(_('Address')),
            'created': self.request.translate(_(
                'Subscribed on')),
        }

    def run_export(self,
                   formatter: Callable[[object], Any]
    ) -> list[OrderedDict[str, Any]]:
        recipients = RecipientCollection(
            self.request.session).ordered_by_status_address().filter_by(
                confirmed=True
            )
        headers = self.headers

        data = []
        for recipient in recipients:
            r = OrderedDict()

            for k, v in headers.items():
                r[v] = formatter(getattr(recipient, k))

            data.append(r)

        return data

    def run_import(self) -> tuple[int, list[str]]:
        headers = self.headers
        headers.pop('created')
        session = self.request.session
        recipients = RecipientCollection(session)
        try:
            assert self.file.file is not None
            csvfile = convert_excel_to_csv(self.file.file)
        except Exception:
            return 0, ['Error converting file']
        try:
            # dialect needs to be set, else error
            csv = CSVFile(csvfile, dialect='excel')
        except Exception:
            return 0, ['Error reading CSV file']

        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        def get(line: DefaultRow, column: str) -> Any:
            return getattr(line, column)

        count = 0
        skipped = 0
        errors = []
        for number, line in enumerate(lines, start=1):
            try:
                kwargs = {
                    attribute: get(line, column)
                    for attribute, column in columns.items()
                }
                kwargs['confirmed'] = True
                address = next(iter(kwargs.values()))
                if recipients.by_address(address):
                    # silently skip duplicates
                    skipped += 1
                    continue
                recipients.add(**kwargs)
                count += 1
            except Exception as e:
                error_msg = f'Error on line {number}: {e!s}'
                errors.append(error_msg)

        if self.dry_run.data:
            transaction.abort()

        summary = [f'Imported: {count}, Skipped duplicates: {skipped}']
        if errors:
            summary.append(f'Errors: {len(errors)}')
            summary.extend(errors)

        return count, summary
