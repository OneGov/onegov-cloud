from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.quill import QuillField
from onegov.swissvotes import _
from onegov.swissvotes.models import TranslatablePage
from wtforms import StringField
from wtforms.validators import InputRequired


class PageForm(Form):

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    content = QuillField(
        label=_("Content"),
        tags=('strong', 'em', 'a', 'h3', 'ol', 'ul', 'blockquote'),
        validators=[
            InputRequired()
        ]
    )

    @property
    def id(self):
        """ An ID based on the title. """

        id = normalize_for_url(self.title.data or 'page')
        query = self.request.session.query(TranslatablePage)
        while query.filter_by(id=id).first():
            id = increment_name(id)
        return id

    def update_model(self, model):
        model.title = self.title.data
        model.content = self.content.data
        model.id = model.id or self.id

    def apply_model(self, model):
        self.title.data = model.title
        self.content.data = model.content
