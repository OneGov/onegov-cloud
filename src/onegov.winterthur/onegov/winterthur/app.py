from onegov.org import OrgApp
from onegov.winterthur.initial_content import create_new_organisation
from onegov.winterthur.theme import WinterthurTheme


class WinterthurApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '0.0.0'

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)


@WinterthurApp.template_directory()
def get_template_directory():
    return 'templates'


@WinterthurApp.setting(section='core', name='theme')
def get_theme():
    return WinterthurTheme()


@WinterthurApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation
