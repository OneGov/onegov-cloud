from dateutil.parser import parse
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.wtfs import _
from wtforms.validators import ValidationError


class MunicipalityDataUploadField(UploadField):
    """ An upload field containg municipality data. """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('validators', [])
        kwargs['validators'].append(WhitelistedMimeType({'text/plain', }))
        kwargs['validators'].append(FileSizeLimit(10 * 1024 * 1024))

        kwargs.setdefault('render_kw', {})
        kwargs['render_kw']['force_simple'] = True

        super().__init__(*args, **kwargs)

    def post_validate(self, form, validation_stopped):
        errors = []
        data = {}

        if not self.data:
            raise ValidationError(_("No data"))

        lines = self.file.read().decode('cp1252').split('\r\n')
        for line_number, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                parts = [part.strip() for part in line.split(';')]
                parts = [part for part in parts if part]
                bfs_number = int(parts[1])
                dates = [parse(d, dayfirst=True).date() for d in parts[4:]]
            except (IndexError, TypeError, ValueError):
                errors.append(line_number)
            else:
                data[bfs_number] = {'dates': dates}

        if errors:
            raise ValidationError(_(
                "Some rows contain invalid values: ${errors}.",
                mapping={'errors': ', '.join((str(e) for e in errors))}
            ))

        self.data = data
