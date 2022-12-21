from onegov.org.utils import annotate_html, remove_empty_paragraphs
from onegov.form.fields import HtmlField as HtmlFieldBase


class HtmlField(HtmlFieldBase):
    """A textfield with html with integrated sanitation and annotation,
    cleaning the html and adding extra information including setting the
    image size by querying the database.

    """

    def pre_validate(self, form):
        super(HtmlField, self).pre_validate(form)
        self.data = remove_empty_paragraphs(
            annotate_html(
                self.data, form.request
            )
        )


class HtmlLabel:
    """
    An HTML Label. Wtforms escapes html in labels by default. We have
    several cases where we actually do want the label to contain html.
    """

    def __init__(self, _id, title, date):
        self.id = _id
        self.title = title
        self.date = date

    def __html__(self):
        """ This method will be called by wtforms. """
        return '<div class="title">{}</div><div class="date">{}</div>'.format(
            self.title, self.date
        )

    def __repr__(self):
        """This gets put into the 'value' attribute of 'input' in html """
        return str(self.title)
