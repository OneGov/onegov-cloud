from __future__ import annotations

from onegov.org.forms.allocation import AllocationRuleForm
from onegov.org.forms.allocation import DaypassAllocationEditForm
from onegov.org.forms.allocation import DaypassAllocationForm
from onegov.org.forms.allocation import RoomAllocationEditForm
from onegov.org.forms.allocation import RoomAllocationForm
from onegov.org.forms.citizen_login import CitizenLoginForm
from onegov.org.forms.citizen_login import ConfirmCitizenLoginForm
from onegov.org.forms.commission import CommissionForm
from onegov.org.forms.directory import DirectoryForm
from onegov.org.forms.directory import DirectoryImportForm
from onegov.org.forms.event import EventForm
from onegov.org.forms.event import EventImportForm
from onegov.org.forms.form_definition import FormDefinitionForm
from onegov.org.forms.form_export import FormSubmissionsExport
from onegov.org.forms.form_registration import FormRegistrationWindowForm
from onegov.org.forms.generic import ExportForm, DateRangeForm
from onegov.org.forms.imageset import ImageSetForm
from onegov.org.forms.invoice import ManualInvoiceItemForm
from onegov.org.forms.meeting import MeetingForm
from onegov.org.forms.mtan import PublicMTANForm
from onegov.org.forms.mtan import PublicRequestMTANForm
from onegov.org.forms.newsletter import NewsletterForm
from onegov.org.forms.newsletter import NewsletterSendForm
from onegov.org.forms.newsletter import NewsletterTestForm
from onegov.org.forms.page import LinkForm, PageForm, IframeForm
from onegov.org.forms.parliamentarian import ParliamentarianForm
from onegov.org.forms.parliamentarian_role import ParliamentarianRoleForm
from onegov.org.forms.parliamentary_group import ParliamentaryGroupForm
from onegov.org.forms.payments import PaymentSearchForm
from onegov.org.forms.payments import TicketInvoiceSearchForm
from onegov.org.forms.person import PersonForm
from onegov.org.forms.reservation import AddReservationForm
from onegov.org.forms.reservation import FindYourSpotForm
from onegov.org.forms.reservation import KabaEditForm
from onegov.org.forms.reservation import ReservationAdjustmentForm
from onegov.org.forms.reservation import ReservationForm
from onegov.org.forms.resource import ResourceCleanupForm
from onegov.org.forms.resource import ResourceExportForm
from onegov.org.forms.resource import ResourceForm
from onegov.org.forms.resource_recipient import ResourceRecipientForm
from onegov.org.forms.search import SearchForm
from onegov.org.forms.settings import AnalyticsSettingsForm
from onegov.org.forms.settings import FooterSettingsForm
from onegov.org.forms.settings import GeneralSettingsForm
from onegov.org.forms.settings import HolidaySettingsForm
from onegov.org.forms.settings import HomepageSettingsForm
from onegov.org.forms.settings import MapSettingsForm
from onegov.org.forms.settings import ModuleSettingsForm
from onegov.org.forms.signup import SignupForm
from onegov.org.forms.survey_submission import SurveySubmissionWindowForm
from onegov.org.forms.text_module import TextModuleForm
from onegov.org.forms.ticket import (
    InternalTicketChatMessageForm, ExtendedInternalTicketChatMessageForm)
from onegov.org.forms.ticket import TicketAssignmentForm
from onegov.org.forms.ticket import TicketChangeTagForm
from onegov.org.forms.ticket import TicketChatMessageForm
from onegov.org.forms.ticket import TicketNoteForm
from onegov.org.forms.user import ManageUserForm
from onegov.org.forms.user import ManageUserGroupForm
from onegov.org.forms.user import NewUserForm
from onegov.org.forms.userprofile import UserProfileForm


__all__ = (
    'AddReservationForm',
    'AllocationRuleForm',
    'AnalyticsSettingsForm',
    'CitizenLoginForm',
    'ConfirmCitizenLoginForm',
    'CommissionForm',
    'DateRangeForm',
    'DaypassAllocationEditForm',
    'DaypassAllocationForm',
    'DirectoryForm',
    'DirectoryImportForm',
    'EventForm',
    'EventImportForm',
    'ExportForm',
    'FindYourSpotForm',
    'FooterSettingsForm',
    'FormDefinitionForm',
    'FormRegistrationWindowForm',
    'FormSubmissionsExport',
    'GeneralSettingsForm',
    'HolidaySettingsForm',
    'HomepageSettingsForm',
    'IframeForm',
    'ImageSetForm',
    'InternalTicketChatMessageForm',
    'ExtendedInternalTicketChatMessageForm',
    'KabaEditForm',
    'LinkForm',
    'ManageUserForm',
    'ManageUserGroupForm',
    'ManualInvoiceItemForm',
    'MapSettingsForm',
    'MeetingForm',
    'ModuleSettingsForm',
    'NewsletterForm',
    'NewsletterSendForm',
    'NewsletterTestForm',
    'NewUserForm',
    'PageForm',
    'ParliamentarianForm',
    'ParliamentarianRoleForm',
    'ParliamentaryGroupForm',
    'PaymentSearchForm',
    'PersonForm',
    'PublicMTANForm',
    'PublicRequestMTANForm',
    'ReservationAdjustmentForm',
    'ReservationForm',
    'ResourceCleanupForm',
    'ResourceExportForm',
    'ResourceForm',
    'ResourceRecipientForm',
    'RoomAllocationEditForm',
    'RoomAllocationForm',
    'SearchForm',
    'SignupForm',
    'SurveySubmissionWindowForm',
    'TextModuleForm',
    'TicketAssignmentForm',
    'TicketChangeTagForm',
    'TicketChatMessageForm',
    'TicketInvoiceSearchForm',
    'TicketNoteForm',
    'UserProfileForm',
)
