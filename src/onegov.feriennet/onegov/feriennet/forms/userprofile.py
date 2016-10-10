from onegov.feriennet import _
from onegov.form import Form
from wtforms import StringField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.validators import URL


class UserProfileForm(Form):
    """ Custom userprofile form for feriennet """

    extra_fields = ('address', 'email', 'phone', 'website')

    realname = StringField(
        label=_("Name"),
        description=_("Personal-, Society- or Company-Name")
    )

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 4},
    )

    email = StringField(
        label=_("Public E-Mail Address"),
        description=_("If different than username")
    )

    phone = StringField(
        label=_("Phone")
    )

    website = URLField(
        label=_("Website"),
        validators=[URL()]
    )

    def populate_obj(self, model):
        super().populate_obj(model)

        model.data = model.data or {}
        model.realname = self.realname.data

        for key in self.extra_fields:
            model.data[key] = self.data.get(key)

    def process_obj(self, model):
        super().process_obj(model)

        modeldata = model.data or {}
        self.realname.data = model.realname

        for key in self.extra_fields:
            getattr(self, key).data = modeldata.get(key)
