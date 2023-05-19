from cached_property import cached_property
from onegov.form.fields import UploadField
from onegov.form import Form


class NamedFileForm(Form):

    """ Base class for handling database models using named files with forms.

    Example:

        class MyModel(AssociatedFiles):
            pdf = NamedFile()

        class MyForm(NamedFileForm):
            pdf = UploadField('PDF')

        @MyApp.form(model=MyCollection, form=MyForm, ...)
        def add(self, request, form):

            if form.submitted(request):
                self.add(**form.get_useful_data())
                ...
            ...

        @MyApp.form(model=MyModel, form=MyForm, ...)
        def edit(self, request, form):

            if form.submitted(request):
                form.populate_obj(self)
                ...

            form.process(obj=self)
            ...

    """

    @cached_property
    def file_fields(self):
        return {
            field.name: field for field in self
            if isinstance(field, UploadField)
        }

    def get_useful_data(self):
        exclude = set(self.file_fields.keys())
        exclude.add('csrf_token')
        data = super().get_useful_data(exclude=exclude)
        for name, field in self.file_fields.items():
            if field.data:
                data[name] = (
                    field.file,
                    field.filename
                )
        return data

    def populate_obj(self, obj):
        super().populate_obj(obj, exclude=self.file_fields.keys())
        for name, field in self.file_fields.items():
            action = getattr(field, 'action', '')
            if action == 'delete':
                delattr(obj, name)
            if action == 'replace' and field.data:
                setattr(obj, name, (field.file, field.filename))

    def process_obj(self, obj):
        super().process_obj(obj)
        for name, field in self.file_fields.items():
            file = getattr(obj, name)
            if file:
                field.data = {
                    'filename': file.reference.filename,
                    'size': file.reference.file.content_length,
                    'mimetype': file.reference.content_type
                }