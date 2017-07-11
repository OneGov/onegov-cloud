from onegov.org.utils import annotate_html
from onegov.form.fields import HtmlField as HtmlFieldBase


class HtmlField(HtmlFieldBase):
    """ A textfield with html with integrated sanitation and annotation,
    cleaning the html and adding extra information including setting the
    image size by querying the database.

    """

    def pre_validate(self, form):
        super(HtmlField, self).pre_validate(form)
        self.data = annotate_html(self.data, form.request)
