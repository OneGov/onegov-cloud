from cached_property import cached_property
from onegov.form import Form, FormDefinition
from onegov.org import _
from wtforms.fields import BooleanField, RadioField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import NumberRange, InputRequired, ValidationError


class FormRegistrationWindowForm(Form):
    """ Form to edit registration windows. """

    start = DateField(
        label=_("Start"),
        validators=[InputRequired()]
    )

    end = DateField(
        label=_("End"),
        validators=[InputRequired()]
    )

    limit_attendees = RadioField(
        label=_("Limit the number of attendees"),
        fieldset=_("Attendees"),
        choices=[
            ('yes', _("Yes, limit the number of attendees")),
            ('no', _("No, allow an unlimited number of attendees"))
        ],
        default='yes'
    )

    limit = IntegerField(
        label=_("Number of attendees"),
        fieldset=_("Attendees"),
        depends_on=('limit_attendees', 'yes'),
        validators=(NumberRange(min=1, max=None), )
    )

    waitinglist = RadioField(
        label=_("Waitinglist"),
        fieldset=_("Attendees"),
        depends_on=('limit_attendees', 'yes'),
        choices=[
            ('yes', _("Yes, allow for more submissions than available spots")),
            ('no', _("No, ensure that all submissions can be confirmed"))
        ],
        default='yes'
    )

    stop = BooleanField(
        label=_("Do not accept any submissions"),
        fieldset=_("Advanced"),
        default=False
    )

    def process_obj(self, obj):
        super().process_obj(obj)
        self.waitinglist.data = obj.overflow and 'yes' or 'no'
        self.limit_attendees.data = obj.limit and 'yes' or 'no'
        self.limit.data = obj.limit or ''
        self.stop.data = not obj.enabled

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.overflow = self.waitinglist.data == 'yes'
        obj.limit = self.limit_attendees.data == 'yes' and self.limit.data or 0
        obj.enabled = not self.stop.data

    @cached_property
    def claimed_spots(self):
        return self.model.claimed_spots

    @cached_property
    def requested_spots(self):
        return self.model.requested_spots

    def validate_limit(self, field):

        # new registration windows do not need to enforce limits
        if isinstance(self.model, FormDefinition):
            return

        # nor do unlimited registration windows
        if not self.limit_attendees.data:
            return

        if self.limit.data < self.claimed_spots:
            raise ValidationError(_(
                "The limit cannot be lower than the already confirmed "
                "number of attendees (${claimed_spots})",
                mapping={
                    'claimed_spots': self.claimed_spots
                }
            ))

        # without a waitinglist we guarantee that all people who sent in
        # an attendance request are getting a spot (unless they are maunally
        # cancelled), so we need to take requested spots into account
        if self.waitinglist.data == 'yes':
            return

        if self.limit.data < (self.requested_spots + self.claimed_spots):
            raise ValidationError(_(
                "The limit cannot be lower than the already confirmed "
                "number attendees (${claimed_spots}) and the number of "
                "pending requests (${pending_requests}). Either enable the "
                "waiting list, process the pending requests or increase the "
                "limit. ",
                mapping={
                    'claimed_spots': self.claimed_spots,
                    'pending_requests': self.requested_spots
                }
            ))
