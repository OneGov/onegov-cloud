from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.user import UserCollection
from wtforms.fields import BooleanField, RadioField, SelectField, StringField
from wtforms.fields.html5 import DecimalField
from wtforms.validators import InputRequired


class BillingForm(Form):

    confirm = RadioField(
        label=_("Confirm billing:"),
        default='no',
        choices=[
            ('no', _("No, preview only")),
            ('yes', _("Yes, confirm billing"))
        ]
    )

    sure = BooleanField(
        label=_("I know that this stops all changes including cancellations."),
        default=False,
        depends_on=('confirm', 'yes')
    )

    @property
    def finalize_period(self):
        return self.confirm.data == 'yes' and self.sure.data is True


class InvoiceItemForm(Form):

    target = RadioField(
        label=_("Target"),
        default='all',
        validators=(InputRequired(), ),
        choices=tuple()
    )

    tags = MultiCheckboxField(
        label=_("Tags"),
        validators=(InputRequired(), ),
        depends_on=('target', 'for-users-with-tags'),
        choices=tuple()
    )

    username = SelectField(
        label=_("User"),
        validators=(InputRequired(), ),
        depends_on=('target', 'for-user'),
    )

    description = StringField(
        label=_("Description"),
        validators=(InputRequired(), )
    )

    @property
    def amount(self):
        raise NotImplementedError

    @property
    def text(self):
        return self.description.data

    @property
    def users(self):
        if self.target.data == 'all':
            return tuple(
                username for (username, realname)
                in self.usercollection.usernames if realname
            )

        elif self.target.data == 'for-user':
            return (self.username.data, )

        elif self.target.data == 'for-users-with-tags':
            return self.usercollection.usernames_by_tags(self.tags.data)

        else:
            raise NotImplementedError

    def on_request(self):
        self.target.choices = [
            ('all', _("All")),
            ('for-user', _("For a specific user"))
        ]

        self.load_usernames()
        self.load_user_tags()

        if self.tags.choices:
            self.target.choices.append(
                ('for-users-with-tags', _("For users with tags")))

    @property
    def usercollection(self):
        return UserCollection(self.request.app.session())

    def load_user_tags(self):
        self.tags.choices = tuple(
            (t, t) for t in self.usercollection.tags)

    def load_usernames(self):
        # non-realname accounts cannot have invoices
        self.username.choices = tuple(
            (username, realname) for username, realname
            in self.usercollection.usernames
            if realname
        )


class RebateForm(InvoiceItemForm):

    rebate = DecimalField(
        label=_("Rebate"),
        validators=(InputRequired(), ),
    )

    @property
    def amount(self):
        return -self.rebate.data
