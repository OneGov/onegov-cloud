from onegov.org.forms import SearchForm
from wtforms import DateField
from wtforms.validators import Optional


class LandsgemeindeSearchForm(SearchForm):

    start = DateField(
        validators=[Optional()]
    )

    end = DateField(
        validators=[Optional()]
    )
