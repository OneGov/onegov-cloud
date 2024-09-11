from dateutil.parser import parse
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.wtfs import _
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.core.types import FileDict
    from onegov.form.types import PricingRules
    from typing import Self
    from wtforms.fields.core import _Filter, _Widget
    from wtforms.form import BaseForm
    from wtforms.meta import _SupportsGettextAndNgettext, DefaultMeta


class MunicipalityDataUploadField(UploadField):
    """ An upload field containg municipality data. """

    # FIXME: This field is doing some real nasty stuff with post_validate
    #        modifying data in place, this seems really fragile, we should
    #        come up with a more robust way to do this
    data: Any

    if TYPE_CHECKING:
        def __init__(
            self,
            *,
            label: str | None = None,
            # FIXME: allow tuple[Validator, ...], but we need to
            #        change the implementation for that
            validators: list[Any] | None = None,
            filters: 'Sequence[_Filter]' = (),
            description: str = '',
            id: str | None = None,
            default: 'Sequence[FileDict]' = (),
            widget: '_Widget[Self] | None' = None,
            render_kw: dict[str, Any] | None = None,
            name: str | None = None,
            _form: 'BaseForm | None' = None,
            _prefix: str = '',
            _translations: '_SupportsGettextAndNgettext | None' = None,
            _meta: 'DefaultMeta | None' = None,
            # onegov specific kwargs that get popped off
            fieldset: str | None = None,
            depends_on: Sequence[Any] | None = None,
            pricing: PricingRules | None = None,
        ): ...
    else:
        def __init__(self, *args: Any, **kwargs: Any):
            kwargs.setdefault('validators', [])
            kwargs['validators'].append(WhitelistedMimeType({'text/plain', }))
            kwargs['validators'].append(FileSizeLimit(10 * 1024 * 1024))

            kwargs.setdefault('render_kw', {})
            kwargs['render_kw']['force_simple'] = True

            super().__init__(*args, **kwargs)

    def post_validate(
        self,
        form: 'BaseForm',
        validation_stopped: bool
    ) -> None:

        errors = []
        data = {}

        if not self.data:
            raise ValidationError(_("No data"))

        file = self.file
        assert file is not None
        lines = file.read().decode('cp1252').split('\r\n')
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
                mapping={'errors': ', '.join(str(e) for e in errors)}
            ))

        self.data = data
