from morepath import Identity
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.file import File
from onegov.org.models import GeneralFile
from onegov.org.models import GeneralFileCollection
from onegov.translator_directory.collections.certificate import \
    LanguageCertificateCollection
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.collections.language import \
    LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.certificate import \
    LanguageCertificate
from onegov.translator_directory.models.language import Language
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.models.voucher import TranslatorVoucherFile
from onegov.user.models import User


def create_user(name, role='anonymous', group_id=None):
    return User(
        realname=name,
        username=f'{name}@example.org',
        password_hash='hash',
        role=role,
        group_id=group_id
    )


def test_security_permissions(translator_app):
    session = translator_app.session()

    # Remove existing users
    session.query(User).delete()

    # Add one user per role
    def create_user(name, role, group_id=None):
        result = User(
            realname=name,
            username=f'{name}@example.org',
            password_hash='hash',
            role=role,
            group_id=group_id
        )
        session.add(result)
        return result

    roles = ('admin', 'editor', 'member', 'anonymous', 'translator')
    users = {}
    for role in roles:
        users[role] = create_user(role, role)

    def permits(user, model, permission):
        return translator_app._permits(
            Identity(
                userid=user.username,
                groupid=user.group_id.hex if user.group_id else '',
                role=user.role,
                application_id=translator_app.application_id
            ),
            model,
            permission
        )

    def assert_admin(user, model):
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert permits(user, model, Secret)

    def assert_editor(user, model):
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_member(user, model):
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_translator(user, model):
        assert permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_anonymous(user, model):
        assert permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_no_access(user, model):
        assert not permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

        # LanguageCertificate
    model = LanguageCertificate()
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)

    # LanguageCertificateCollection
    model = LanguageCertificateCollection(session)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)

    # TranslatorDocumentCollection
    model = TranslatorDocumentCollection(session, None, None)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted

    # Language
    model = Language()
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)

    # LanguageCollection
    model = LanguageCollection(session)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)

    # Translator
    model = Translator()
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)

    model.for_admins_only = True
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_translator(users['translator'], model)
    assert_no_access(users['anonymous'], model)  # restricted

    model.for_admins_only = False
    model.email = 'translator@example.org'
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_member(users['translator'], model)  # elevated
    assert_anonymous(users['anonymous'], model)

    model.for_admins_only = True
    model.email = 'translator@example.org'
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_member(users['translator'], model)  # elevated
    assert_no_access(users['anonymous'], model)  # restricted

    # TranslatorCollection
    model = TranslatorCollection(session)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)

    # File
    model = File()
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted

    # TranslatorVoucherFile
    model = TranslatorVoucherFile()
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted

    # GeneralFile
    model = GeneralFile()
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted

    # GeneralFileCollection
    model = GeneralFileCollection(session)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
