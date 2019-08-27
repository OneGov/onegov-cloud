from cached_property import cached_property
from onegov.core.html_diff import render_html_diff
from onegov.form.extensions import FormExtension
from onegov.form.fields import UploadField
from onegov.gis import CoordinatesField
from onegov.org import _
from wtforms.fields import TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class CoordinatesFormExtension(FormExtension, name='coordinates'):

    def create(self):
        class CoordinatesForm(self.form_class):
            coordinates = CoordinatesField(
                label=_("Coordinates"),
                description=_(
                    "The marker can be moved by dragging it with the mouse"
                ),
                fieldset=_("Map"),
                render_kw={'data-map-type': 'marker'}
            )

        return CoordinatesForm


class SubmitterFormExtension(FormExtension, name='submitter'):

    def create(self):
        class SubmitterForm(self.form_class):
            submitter = EmailField(
                label=_("E-Mail"),
                fieldset=_("Submitter"),
                validators=[DataRequired()]
            )

        return SubmitterForm


class CommentFormExtension(FormExtension, name='comment'):

    def create(self):
        class CommentForm(self.form_class):
            comment = TextAreaField(
                label=_("Comment"),
                fieldset=_("Submitter"),
                render_kw={'rows': 7}
            )

        return CommentForm


class ChangeRequestFormExtension(FormExtension, name='change-request'):

    def create(self):

        # XXX circular import
        from onegov.org.models.directory import ExtendedDirectoryEntry

        class ChangeRequestForm(self.form_class):

            @cached_property
            def target(self):

                # not all steps have this information set, for example, towards
                # the end, the onegov.form submission code runs an extra
                # validation, which we ignore, trusting that it all worked
                # out earlier
                if not getattr(self, 'model', None):
                    return None

                return self.request.session.query(ExtendedDirectoryEntry)\
                    .filter_by(id=self.model.meta['directory_entry'])\
                    .first()

            def is_different(self, field):
                # if the target has been removed, stop
                if not self.target:
                    return True

                # after the changes have been applied, use the list of changes
                if self.model.meta.get('changed'):
                    return field.id in self.model.meta['changed']

                # ignore CSRF token
                if field.id == 'csrf_token':
                    return False

                # coordinates fields are provided through extension
                if field.id == 'coordinates':
                    return field.data != self.target.coordinates

                # upload fields differ if they are not empty
                if isinstance(field, UploadField):
                    return field.data and True or False

                return self.target.values.get(field.id) != field.data

            def render_original(self, field):
                prev = field.data

                try:
                    field.data = self.target.values.get(field.id)
                    return super().render_display(field)
                finally:
                    field.data = prev

            def render_display(self, field):
                if self.is_different(field):
                    proposed = super().render_display(field)

                    if not self.target:
                        return proposed

                    if field.id in ('csrf_token', 'coordinates'):
                        return proposed

                    if field.id not in self.target.values:
                        return proposed

                    if isinstance(field, UploadField):
                        return proposed

                    original = self.render_original(field)
                    return render_html_diff(original, proposed)

            def ensure_changes(self):
                if not self.target:
                    return

                for name, field in self._fields.items():
                    if self.is_different(field):
                        return

                self.errors['global-errors'] = [
                    _("Please provide at least one change")]

                return False

        return ChangeRequestForm
