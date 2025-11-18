from __future__ import annotations

from decimal import Decimal
from onegov.translator_directory import _

full_text_max_chars = 25
member_can_see = (
    'first_name',
    'last_name',
    'pers_id',
    'admission',
    'withholding_tax',
    'self_employed',
    'gender',
    'date_of_birth',
    'nationalities',
    'coordinates',
    'address',
    'zip_code',
    'city',
    'hometown',
    'drive_distance',
    'email',
    'tel_mobile',
    'tel_private',
    'tel_office',
    'availability',
    'mother_tongues',
    'spoken_languages',
    'written_languages',
    'monitoring_languages',
    'expertise_interpreting_types',
    'expertise_professional_guilds',
    'expertise_professional_guilds_other',
    'expertise_professional_guilds_all'
)

editor_can_see = (
    *member_can_see,
    'social_sec_number',
    'bank_name',
    'bank_address',
    'account_owner',
    'iban'
)

translator_can_see = (
    *editor_can_see,
    'profession',
    'occupation',
    'operation_comments',
    'confirm_name_reveal',
    'date_of_application',
    'date_of_decision',
    'proof_of_preconditions',
    'agency_references',
    'education_as_interpreter',
    'certificates',
    'comments'
)

field_order = (
    'first_name',
    'last_name',
    'pers_id',
    'admission',
    'withholding_tax',
    'self_employed',
    'gender',
    'date_of_birth',
    'nationalities',
    'coordinates',
    'address',
    'zip_code',
    'city',
    'drive_distance',
    'social_sec_number',
    'bank_name',
    'bank_address',
    'account_owner',
    'iban',
    'email',
    'tel_private',
    'tel_mobile',
    'tel_office',
    'availability',
    'expertise_interpreting_types',
    'expertise_professional_guilds',
    'expertise_professional_guilds_other',
    'expertise_professional_guilds_all',
    'operation_comments',
    'confirm_name_reveal',
    'date_of_application',
    'date_of_decision',
    'mother_tongues',
    'spoken_languages',
    'written_languages',
    'monitoring_languages',
    'profession',
    'occupation',
    'proof_of_preconditions',
    'agency_references',
    'education_as_interpreter',
    'certificates',
    'comments',
    'for_admins_only',
    'user',
)

ADMISSIONS = {
    'uncertified': _('uncertified'),
    'in_progress': _('in progress'),
    'certified': _('certified')
}

GENDERS = {'M': _('masculin'), 'F': _('feminin'), 'N': _('neutral')}
GENDER_MAP = {
    'M': _('male'),
    'F': _('female'),
    'N': _('neutral')
}

CERTIFICATES = ('ZHAW', 'OGZH')

# Static form choices, we don't know how the app will be further developed
PROFESSIONAL_GUILDS = {
    'nutrition_agriculture': _('Nutrition and agriculture'),
    'economy': _('Economy'),
    'art_leisure': _('Art and leisure'),
    'business_economics': _('Business economics'),
    'banking_finance': _('Banking and finance'),
    'social_science': _('Social science'),
    'industry_service_sector': _('Industry and service sector'),
    'engineering': _('Engineering'),
    'internation_relations': _('International relations and organisations'),
    'law_insurance': _('Law and insurance industry'),
    'military': _('Military'),
    'medicine': _('Medicine')
}

INTERPRETING_TYPES = {
    'simultaneous': _('Simultaneous interpreting'),
    'consecutive': _('Consecutive interpreting'),
    'negotiation': _('Negotiation interpreting'),
    'whisper': _('Whisper interpreting'),
}

# SHPOL ====
TIME_REPORT_INTERPRETING_TYPES = {
    'telephonic': _('telephonic'),
    'on-site': _('On Site'),
}
HOURLY_RATE_CERTIFIED = Decimal('90.00')
HOURLY_RATE_UNCERTIFIED = Decimal('75.00')

TIME_REPORT_SURCHARGE_LABELS = {
    'night_work': 'Zuschlag Nacht',
    'weekend_holiday': 'Zuschlag WE',
    'urgent': _('Exceptionally urgent'),
}
# ====

TRANSLATOR_FA_ICON = 'translator'
