from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.winterthur import WinterthurApp
from onegov.org.views import directory as base
from onegov.directory import DirectoryCollection
from onegov.core.security import Secret
from onegov.form import merge_forms
from onegov.form.utils import get_fields_from_class


def get_directory_form_class(model, request):
    forms = [base.get_directory_form_class(model, request)]
    registry = request.app.config.directory_search_widget_registry

    fields = {}

    for name, cls in registry.items():
        if hasattr(cls, 'form'):
            fields[name] = tuple(n for n, f in get_fields_from_class(cls.form))
            forms.append(cls.form)

    class AdaptedDirectoryForm(merge_forms(*forms)):

        def populate_obj(self, obj, *args, **kwargs):
            nonlocal fields

            super().populate_obj(obj, *args, **kwargs)

            obj.search_widget_config = {}

            for name, fields_ in fields.items():
                obj.search_widget_config[name] = {
                    f: self.data[f] for f in fields_
                }

        def process_obj(self, obj):
            nonlocal fields

            super().process_obj(obj)

            if not obj.search_widget_config:
                return

            for name, fields_ in fields.items():
                if name not in obj.search_widget_config:
                    continue

                for f in fields_:
                    getattr(self, f).data\
                        = obj.search_widget_config[name].get(f)

    return AdaptedDirectoryForm


@WinterthurApp.form(model=DirectoryCollection, name='new', template='form.pt',
                    permission=Secret, form=get_directory_form_class)
def handle_new_directory(self, request, form):
    return base.handle_new_directory(self, request, form)


@WinterthurApp.form(model=ExtendedDirectoryEntryCollection, name='edit',
                    template='directory_form.pt', permission=Secret,
                    form=get_directory_form_class)
def handle_edit_directory(self, request, form):
    return base.handle_edit_directory(self, request, form)
