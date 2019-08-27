from chameleon import PageTemplate
from wtforms.fields import Field
from wtforms.widgets.core import html_params
from wtforms.widgets.core import HTMLString


class HintWidget(object):

    def __call__(self, field, **kwargs):
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
        return HTMLString(template.render(translate=translate))


class HintField(Field):

    widget = HintWidget()

    def __init__(self, *args, **kwargs):
        self.macro = kwargs.pop('macro')
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj, name):
        pass
