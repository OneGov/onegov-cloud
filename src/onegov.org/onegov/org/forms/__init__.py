from onegov.org.forms.allocation import (
    DaypassAllocationForm,
    DaypassAllocationEditForm,
    RoomAllocationForm,
    RoomAllocationEditForm
)
from onegov.org.forms.event import EventForm
from onegov.org.forms.form_definition import CustomDefinitionForm
from onegov.org.forms.imageset import ImageSetForm
from onegov.org.forms.newsletter import NewsletterForm, NewsletterSendForm
from onegov.org.forms.page import LinkForm, PageForm
from onegov.org.forms.person import PersonForm
from onegov.org.forms.reset_password import (
    RequestPasswordResetForm,
    PasswordResetForm
)
from onegov.org.forms.reservation import ReservationForm
from onegov.org.forms.resource import (
    ResourceForm,
    ResourceCleanupForm,
    ResourceExportForm
)
from onegov.org.forms.settings import SettingsForm
from onegov.org.forms.signup import SignupForm
from onegov.org.forms.userprofile import UserProfileForm
from onegov.org.forms.user import ManageUserForm, NewUserForm


__all__ = [
    'CustomDefinitionForm',
    'DaypassAllocationEditForm',
    'DaypassAllocationForm',
    'EventForm',
    'ImageSetForm',
    'LinkForm',
    'ManageUserForm',
    'NewsletterForm',
    'NewsletterSendForm',
    'NewUserForm',
    'PageForm',
    'PasswordResetForm',
    'PersonForm',
    'RequestPasswordResetForm',
    'ReservationForm',
    'ResourceCleanupForm',
    'ResourceExportForm',
    'ResourceForm',
    'RoomAllocationEditForm',
    'RoomAllocationForm',
    'SettingsForm',
    'SignupForm',
    'UserProfileForm',
]
