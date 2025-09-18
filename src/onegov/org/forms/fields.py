from __future__ import annotations

from onegov.file import File, FileCollection
from onegov.core.utils import binary_to_dictionary, dictionary_to_binary
from onegov.form.fields import HtmlField as HtmlFieldBase
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.fields import UploadMultipleFilesWithORMSupport
from onegov.org.forms.widgets import UploadOrLinkExistingFileWidget
from onegov.org.forms.widgets import UploadOrSelectExistingFileWidget
from onegov.org.forms.widgets import UploadOrSelectExistingMultipleFilesWidget
from onegov.org.utils import annotate_html, remove_empty_paragraphs
from operator import itemgetter


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from onegov.form.types import RawFormValue


class HtmlField(HtmlFieldBase):
    """A textfield with html with integrated sanitation and annotation,
    cleaning the html and adding extra information including setting the
    image size by querying the database.

    """

    def pre_validate(self, form: Form) -> None:  # type:ignore[override]
        super().pre_validate(form)
        self.data = remove_empty_paragraphs(
            annotate_html(
                self.data, form.request
            )
        )


def file_choices_from_collection(
    collection: FileCollection[Any]
) -> list[tuple[str, str]]:
    return sorted(
        (
            (file_id, name)
            for file_id, name in collection.query().with_entities(
                File.id,
                File.name,
            )
        ),
        key=itemgetter(1)
    )


class UploadOrLinkExistingFileField(UploadFileWithORMSupport):
    """ An extension of :class:`onegov.form.fields.UploadFileWithORMSupport`
    which will select existing uploaded files to link from a given
    :class:`onegov.file.FileCollection` class in addition to uploading
    new files.

    This class is mostly useful in conjunction with
    :class:`onegov.org.forms.fields.UploadOrSelectExistingMultipleFilesField`
    if you want to link or upload only a single file, then you should
    use :class:`onegov.org.forms.fields.UploadOrSelectExistingFileField`.

    """

    existing_file: File | None
    widget = UploadOrLinkExistingFileWidget()

    def __init__(
        self,
        *args: Any,
        file_collection: type[FileCollection[Any]] = FileCollection,
        file_type: str = 'general',
        allow_duplicates: bool = False,
        # these params are used by the MultipleFiles version to avoid
        # doing static prep work multiple times
        _collection: FileCollection[Any] | None = None,
        **kwargs: Any
    ) -> None:
        # if we got this argument we discard it, we don't use it
        kwargs.pop('_choices', None)

        # we don't really use file_class since we use the collection
        # to create the files instead
        kwargs.setdefault('file_class', File)
        super().__init__(*args, **kwargs)
        self.allow_duplicates = allow_duplicates

        # this can happen with merge_forms before we create the
        # final merged form instance, we delay errors in this case
        # since it's only an error once someone tries to use the
        # collection
        if not hasattr(self.meta, 'request'):
            return

        if _collection is None:
            _collection = file_collection(
                self.meta.request.session,
                type=file_type,
                # we do ensure this ourselves in create
                allow_duplicates=True
            )
        self.collection = _collection

    def populate_obj(self, obj: object, name: str) -> None:
        # shortcut for when a file was explicitly selected
        existing = getattr(self, 'existing_file', None)
        if existing is not None:
            setattr(obj, name, existing)
            return

        super().populate_obj(obj, name)

    def create(self) -> File | None:
        if not getattr(self, 'file', None):
            return None

        assert self.file is not None
        self.file.filename = self.filename  # type:ignore[attr-defined]
        self.file.seek(0)

        if not self.allow_duplicates:
            # return the existing file instead
            existing = self.collection.by_content(self.file).first()
            if existing is not None:
                self.existing_file = existing
                return existing

            self.file.seek(0)

        return self.collection.add(
            filename=self.filename,  # type:ignore[arg-type]
            content=self.file
        )


class UploadOrSelectExistingFileField(UploadOrLinkExistingFileField):
    """ An extension of :class:`onegov.form.fields.UploadFileWithORMSupport`
    to allow selecting existing uploaded files from a given
    :class:`onegov.file.FileCollection` class in addition to uploading
    new files.

    :param file_collection:
        The file collection class to use, should be a subclass of
        :class:`onegov.file.FileCollection`.

    :param file_type:
        The polymoprhic type to use and to filter for.

    :param allow_duplicates:
        Prevents duplicates if set to false. Rather than throw an error
        it will link to the existing file and discard the new file.

    """

    widget = UploadOrSelectExistingFileWidget()

    def __init__(
        self,
        *args: Any,
        file_collection: type[FileCollection[Any]] = FileCollection,
        file_type: str = 'general',
        allow_duplicates: bool = False,
        _choices: list[tuple[str, str]] | None = None,
        **kwargs: Any
    ):
        super().__init__(
            *args,
            file_collection=file_collection,
            file_type=file_type,
            allow_duplicates=allow_duplicates,
            **kwargs
        )
        # this can happen with merge_forms before we create the
        # final merged form instance, we delay errors in this case
        # since it's only an error once someone tries to use the
        # collection/choices
        if not hasattr(self, 'collection'):
            return

        if _choices is None:
            _choices = file_choices_from_collection(self.collection)
        self.choices = _choices

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:

        if not valuelist:
            self.data = {}
            return

        fieldstorage: RawFormValue
        action: RawFormValue
        if len(valuelist) == 5:
            # resend_upload
            action = valuelist[0]
            fieldstorage = valuelist[1]
            existing = valuelist[2]
            self.data = binary_to_dictionary(  # type: ignore[assignment]
                dictionary_to_binary({'data': str(valuelist[4])}),
                str(valuelist[3])
            )
        elif len(valuelist) == 3:
            action, fieldstorage, existing = valuelist
        else:
            # default
            action = 'replace'
            fieldstorage = valuelist[0]

        if action == 'replace':
            self.action = 'replace'
            self.data = self.process_fieldstorage(fieldstorage)
            self.existing = None
        elif action == 'delete':
            self.action = 'delete'
            self.data = {}
            self.existing = None
        elif action == 'keep':
            self.action = 'keep'
            self.existing = None
        elif action == 'select':
            self.action = 'replace'
            if not isinstance(existing, str):
                self.existing = None
                return

            if self.collection is None:
                self.collection = self.collection_class(  # type:ignore
                    self.meta.request.session,
                    type=self.file_type,
                    allow_duplicates=True
                )

            self.existing = existing
            self.existing_file = self.collection.by_id(existing)
            self.process_data(self.existing_file)
        else:
            raise NotImplementedError()


class UploadOrSelectExistingMultipleFilesField(
    UploadMultipleFilesWithORMSupport
):
    """ An extension of
    :class:`onegov.form.fields.UploadMultipleFilesWithORMSupport` to
    allow selecting existing uploaded files from a given
    :class:`onegov.file.FileCollection` class in addition to uploading
    new files.

    :param file_collection:
        The file collection class to use, should be a subclass of
        :class:`onegov.file.FileCollection`.

    :param file_type:
        The polymoprhic type to use and to filter for.

    :param allow_duplicates:
        Prevents duplicates if set to false. Rather than throw an error
        it will link to the existing file and discard the new file.

    """

    widget = UploadOrSelectExistingMultipleFilesWidget()
    upload_field_class = UploadOrLinkExistingFileField
    upload_widget = UploadOrLinkExistingFileWidget()

    def __init__(
        self,
        *args: Any,
        file_collection: type[FileCollection[Any]] = FileCollection,
        file_type: str = 'general',
        allow_duplicates: bool = False,
        **kwargs: Any
    ):

        meta = kwargs.get('_meta') or kwargs['_form'].meta
        # this can happen with merge_forms before we create the
        # final merged form instance, we delay errors in this case
        # since it's only an error once someone tries to use the
        # collection/choices
        if not hasattr(meta, 'request'):
            super().__init__(*args, **kwargs, file_class=File)
            return

        self.collection = file_collection(
            meta.request.session,
            type=file_type,
            # we do ensure this ourselves in create
            allow_duplicates=True
        )
        self.choices = file_choices_from_collection(self.collection)

        super().__init__(
            *args,
            **kwargs,
            file_class=File,
            file_collection=file_collection,
            file_type=file_type,
            allow_duplicates=allow_duplicates,
            _collection=self.collection,
            _choices=self.choices,
        )

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not valuelist:
            return

        for value in valuelist:
            if isinstance(value, str):
                if any(f.id == value for f in self.object_data or ()):
                    # if this file has already been added, then don't add
                    # it again
                    continue

                existing = self.collection.by_id(value)
                if existing is not None:
                    field = self.append_entry(existing)
                    field.existing_file = existing  # type:ignore[attr-defined]

            elif hasattr(value, 'file') or hasattr(value, 'stream'):
                self.append_entry_from_field_storage(value)
