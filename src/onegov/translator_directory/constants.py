from onegov.translator_directory import _

full_text_max_chars = 25
member_can_see = (
    'first_name',
    'last_name',
    'pers_id',
    'admission',
    'withholding_tax',
    'gender',
    'date_of_birth',
    'nationality',
    'address',
    'zip_code',
    'city',
    'drive_distance',
    'email',
    'tel_mobile',
    'tel_private',
    'tel_office',
    'availability',
    'mother_tongues',
    'languages_written',
    'languages_spoken',
    'expertise_interpreting_types',
    'expertise_professional_guilds'
)

editor_can_see = member_can_see + (
    'social_sec_number',
    'bank_name',
    'bank_address',
    'account_owner',
    'iban'
)

ADMISSIONS = {
    'uncertified': _('uncertified'),
    'in_progress': _('in progress'),
    'certified': _('certified')
}

GENDERS = {'M': _('masculin'), 'F': _('feminin'), 'N': _('neutral')}
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
    'military': _('Military')
}

INTERPRETING_TYPES = {
    'simultaneous': _('Simultaneous interpreting'),
    'consecutive': _('Consecutive interpreting'),
    'negotiation': _('Negotiation interpreting'),
    'whisper': _('Whisper interpreting'),
    'written': _('Written translations')
}
