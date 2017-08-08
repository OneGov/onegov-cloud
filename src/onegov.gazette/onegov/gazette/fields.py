from onegov.form.fields import HtmlField as HtmlFieldBase
from bleach.sanitizer import Cleaner

cleaner = Cleaner(
    tags=['br', 'em', 'p', 'strong'],
    attributes={},
    strip=True
)


class HtmlField(HtmlFieldBase):
    """ A textfield with html with integrated sanitation.

    We need a much stricter sanitation than the normal editor uses.

    """

    def pre_validate(self, form):
        self.data = cleaner.clean(self.data)
