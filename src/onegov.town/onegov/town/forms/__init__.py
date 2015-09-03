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
from onegov.town.forms.login import LoginForm
from onegov.town.forms.page import LinkForm, PageForm
from onegov.town.forms.person import PersonForm
from onegov.town.forms.reset_password import (
    RequestPasswordResetForm,
    PasswordResetForm
)
from onegov.town.forms.reservation import ReservationForm
from onegov.town.forms.resource import ResourceForm, ResourceCleanupForm
from onegov.town.forms.settings import SettingsForm

__all__ = [
    'BuiltinDefinitionForm',
    'CustomDefinitionForm',
    'DaypassAllocationForm',
    'DaypassAllocationEditForm',
    'EventForm',
    'LinkForm',
    'LoginForm',
    'PageForm',
    'PasswordResetForm',
    'PersonForm',
    'ReservationForm',
    'ResourceForm',
    'ResourceCleanupForm',
    'RequestPasswordResetForm',
    'RoomAllocationForm',
    'RoomAllocationEditForm',
    'SettingsForm',
]
