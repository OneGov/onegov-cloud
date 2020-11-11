from datetime import datetime

from sqlalchemy.orm import object_session

from onegov.core import utils
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent, extension_for_content_type, \
    content_type_from_fileobj
from onegov.gis import Coordinates
from onegov.translator_directory.initial_content import create_new_organisation
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as default_common_asset
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.translator_directory.models.voucher import TranslatorVoucherFile
from onegov.translator_directory.request import TranslatorAppRequest
from onegov.translator_directory.theme import TranslatorDirectoryTheme


class TranslatorDirectoryApp(OrgApp):

    send_daily_ticket_statistics = False
    request_class = TranslatorAppRequest

    def es_may_use_private_search(self, request):
        return request.is_admin

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        cfg.setdefault('disable_password_reset', False)
        super().configure_organisation(**cfg)

    @property
    def coordinates(self):
        return self.org.meta.get('translator_directory_home') or Coordinates()

    @coordinates.setter
    def coordinates(self, value):
        self.org.meta['translator_directory_home'] = value or {}

    @property
    def voucher_excel(self):
        return object_session(self.org).query(TranslatorVoucherFile).first()

    @property
    def voucher_excel_file(self):
        return self.voucher_excel and self.voucher_excel.reference.file

    @voucher_excel_file.setter
    def voucher_excel_file(self, value):
        content_type = extension_for_content_type(
            content_type_from_fileobj(value)
        )
        print(content_type)
        year = datetime.now().year
        filename = f'abrechnungsvorlage_{year}.{content_type}'
        if self.voucher_excel:
            self.voucher_excel.reference = as_fileintent(value, filename)
            self.voucher_excel.name = filename
        else:
            file = TranslatorVoucherFile(id=random_token())
            file.reference = as_fileintent(value, filename)
            file.name = filename
            session = object_session(self.org)
            session.add(file)
            session.flush()


@TranslatorDirectoryApp.template_directory()
def get_template_directory():
    return 'templates'


@TranslatorDirectoryApp.static_directory()
def get_static_directory():
    return 'static'


@TranslatorDirectoryApp.setting(section='core', name='theme')
def get_theme():
    return TranslatorDirectoryTheme()


@TranslatorDirectoryApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@TranslatorDirectoryApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.translator_directory', 'locale')
    return [mine] + get_org_i18n_localedirs()


@TranslatorDirectoryApp.webasset_path()
def get_js_path():
    return 'assets/js'


@TranslatorDirectoryApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@TranslatorDirectoryApp.webasset('common')
def get_common_asset():
    yield from default_common_asset()
    yield 'translator_directory.js'
