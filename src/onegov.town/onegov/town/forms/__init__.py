from onegov.town.forms.allocation import (
    DaypassAllocationForm,
    DaypassAllocationEditForm,
    RoomAllocationForm,
    RoomAllocationEditForm
)
from onegov.town.forms.event import EventForm
from onegov.town.forms.form_definition import (
    BuiltinDefinitionForm,
    CustomDefinitionForm
)
from onegov.town.forms.newsletter import NewsletterForm, NewsletterSendForm
from onegov.town.forms.page import LinkForm, PageForm
from onegov.town.forms.person import PersonForm
from onegov.town.forms.reset_password import (
    RequestPasswordResetForm,
    PasswordResetForm
)
from onegov.town.forms.reservation import ReservationForm
from onegov.town.forms.resource import (
    ResourceForm,
    ResourceCleanupForm,
    ResourceExportForm
)
from onegov.town.forms.settings import SettingsForm
from onegov.town.forms.signup import SignupForm
from onegov.town.forms.userprofile import UserProfileForm

__all__ = [
    'BuiltinDefinitionForm',
    'CustomDefinitionForm',
    'DaypassAllocationForm',
    'DaypassAllocationEditForm',
    'EventForm',
    'LinkForm',
    'NewsletterForm',
    'NewsletterSendForm',
    'PageForm',
    'PasswordResetForm',
    'PersonForm',
    'ReservationForm',
    'ResourceForm',
    'ResourceCleanupForm',
    'ResourceExportForm',
    'RequestPasswordResetForm',
    'RoomAllocationForm',
    'RoomAllocationEditForm',
    'SettingsForm',
    'SignupForm',
    'UserProfileForm'
]
