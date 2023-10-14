from markupsafe import Markup
from onegov.core.templates import PageTemplate
from wtforms.fields import Field
from wtforms.widgets.core import html_params


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.form.types import PricingRules, Validators, _FormT
    from typing_extensions import Self
    from wtforms.fields.core import _Filter, _Widget
    from wtforms.form import BaseForm
    from wtforms.meta import _SupportsGettextAndNgettext, DefaultMeta


class HintWidget:

    def __call__(self, field: 'HintField', **kwargs: Any) -> Markup:
        params = html_params(name=field.name, **kwargs)
        request = field.meta.request
        registry = request.app.config.template_engine_registry
        macros = registry._template_loaders['.pt'].macros
        template = PageTemplate(
            f"""
                <div {params}>
                    <div metal:use-macro="macros['{field.macro}']"/>
                </div>
            """,
            macros=macros
        )

        translate = request.get_translate(for_chameleon=True)
        return Markup(template.render(translate=translate))  # noqa: MS001


class HintField(Field):

    widget = HintWidget()

    def __init__(
        self,
        label: str | None = None,
        validators: 'Validators[_FormT, Self] | None' = None,
        filters: 'Sequence[_Filter]' = (),
        description: str = '',
        id: str | None = None,
        default: None = None,
        widget: '_Widget[Self] | None' = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        _form: 'BaseForm | None' = None,
        _prefix: str = '',
        _translations: '_SupportsGettextAndNgettext | None' = None,
        _meta: 'DefaultMeta | None' = None,
        *,
        macro: str | None = None,
        # onegov specific kwargs that get popped off
        fieldset: str | None = None,
        depends_on: 'Sequence[Any] | None' = None,
        pricing: 'PricingRules | None' = None,
    ) -> None:

        self.macro = macro
        super().__init__(
            label=label,
            validators=validators,
            filters=filters,
            description=description,
            id=id,
            widget=widget,
            render_kw=render_kw,
            name=name,
            _form=_form,
            _prefix=_prefix,
            _translations=_translations,
            _meta=_meta
        )

    def populate_obj(self, obj: object, name: str) -> None:
        pass
