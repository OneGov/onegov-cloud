from copy import deepcopy
from datetime import date, timedelta

from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection

translator_data = dict(
    first_name='Hugo',
    last_name='Benito',
    admission=None,
    withholding_tax='No idea what datatype this is',
    gender='M',
    date_of_birth=date.today(),
    nationality='CH',
    address='Downing Street 5',
    zip_code='4000',
    city='Luzern',
    social_sec_number='1234',
    bank_name='R-BS',
    bank_address='Bullstreet 5',
    account_owner='Hugo Benito',
    email='hugo@benito.com',
    tel_mobile='079 000 00 00',
    tel_office='041 444 44 44',
    tel_private=None,
    availability='always',
    confirm_name_reveal=None,
    date_of_application=date.today() - timedelta(days=100),
    date_of_decision=date.today() - timedelta(days=50),
)


def create_languages(session):
    languages = []
    collection = LanguageCollection(session)
    for lang in ('German', 'French', 'Italian', 'Arabic'):
        languages.append(collection.add(name=lang))
    return languages


def create_translator(session, email=None, **kwargs):
    data = deepcopy(translator_data)
    for key in kwargs:
        if key in data:
            data[key] = kwargs[key]
    if email:
        data['email'] = email

    return TranslatorCollection(session).add(**data)
