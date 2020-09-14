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
    'languages_spoken'
)

editor_can_see = member_can_see + (
    'social_sec_number',
    'bank_name',
    'bank_address',
    'account_owner',
    'iban'
)

ADMISSIONS = ('uncertified', 'in_progress', 'certified')
ADMISSIONS_DESC = (_('uncertified'), _('in progress'), _('certified'))
GENDERS = ('M', 'F', 'N')
GENDERS_DESC = (_('masculin'), _('feminin'), 'neutral')
CERTIFICATES = ('ZHAW', 'OGZH')
