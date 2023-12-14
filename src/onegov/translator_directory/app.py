from functools import cached_property
from onegov.core import utils
from onegov.gis import Coordinates
from onegov.translator_directory.initial_content import create_new_organisation
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as default_common_asset
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.org.models import Organisation, GeneralFile, GeneralFileCollection
from onegov.translator_directory.request import TranslatorAppRequest
from onegov.translator_directory.theme import TranslatorDirectoryTheme
from purl import URL
from sqlalchemy import and_


class TranslatorDirectoryApp(OrgApp):

    send_ticket_statistics = False
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

    def redirect_after_login(self, identity, request, default):
        if default != '/' and '/auth/login' not in str(default):
            return None
        return URL(request.class_link(Organisation)).path()

    @property
    def mail_templates(self):
        """ Templates are special docx files which are filled with
        variables. These files are manually uploaded. """
        query = GeneralFileCollection(self.session()).query().filter(
            and_(
                GeneralFile.name.like('Vorlage%'),
                GeneralFile.name.like('%.docx')
            )
        )
        return [f.name for f in query.all()]

    @cached_property
    def mailto_link(self):
        from onegov.translator_directory.models.translator import Translator
        q = self.session().query(Translator).with_entities(
            Translator.email)
        emails = q.distinct().all()
        bcc_addresses = '; '.join(str(email) for (email,) in emails if email)
        mailto_link = f"mailto:?bcc={bcc_addresses}"
        return mailto_link


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
