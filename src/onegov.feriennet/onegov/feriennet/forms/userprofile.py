from onegov.feriennet import _
from onegov.form import Form
from wtforms import StringField, TextAreaField
from wtforms.fields.html5 import URLField


class UserProfileForm(Form):
    """ Custom userprofile form for feriennet """

    extra_fields = ('name', 'address', 'phone', 'website')

    name = StringField(
        label=_("Name"),
        description=_("Personal-, Society- or Company-Name")
    )

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 4},
    )

    phone = StringField(
        label=_("Phone")
    )

    website = URLField(
        label=_("Website")
    )

    def update_model(self, model):
        model.data = model.data or {}

        for key in self.extra_fields:
            model.data[key] = self.data.get(key)

    def apply_model(self, model):
        modeldata = model.data or {}

        for key in self.extra_fields:
            getattr(self, key).data = modeldata.get(key)
