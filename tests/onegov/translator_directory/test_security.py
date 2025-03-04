from morepath import Identity
from morepath.authentication import NoIdentity
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.file import File
from onegov.org.models import GeneralFile
from onegov.org.models import GeneralFileCollection
from onegov.org.models import Topic
from onegov.ticket import Ticket
from onegov.ticket import TicketCollection
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
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.mutation import TranslatorMutation
from onegov.translator_directory.models.ticket import AccreditationTicket
from onegov.translator_directory.models.ticket import TranslatorMutationTicket
from onegov.translator_directory.models.translator import Translator
from onegov.user.models import User


def create_user(name, role='anonymous', groups=None):
    return User(
        realname=name,
        username=f'{name}@example.org',
        password_hash='hash',
        role=role,
        groups=groups or [],
    )


def test_security_permissions(translator_app):
    session = translator_app.session()

    # Remove existing users
    session.query(User).delete()

    # Add one user per role
    def create_user(name, role, groups=None):
        result = User(
            realname=name,
            username=f'{name}@example.org',
            password_hash='hash',
            role=role,
            groups=groups or [],
        )
        session.add(result)
        return result

    roles = ('admin', 'editor', 'member', 'anonymous', 'translator')
    users = {}
    for role in roles:
        users[role] = create_user(role, role)

    def permits(user, model, permission):
        identity = NoIdentity()
        if user:
            identity = Identity(
                userid=user.username,
                groupids=frozenset(group.id.hex for group in user.groups),
                role=user.role,
                application_id=translator_app.application_id
            )
        return translator_app._permits(identity, model, permission)

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
    assert_anonymous(None, model)

    # LanguageCertificateCollection
    model = LanguageCertificateCollection(session)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    # TranslatorDocumentCollection
    model = TranslatorDocumentCollection(session, None, None)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # Language
    model = Language()
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    # LanguageCollection
    model = LanguageCollection(session)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    # Translator
    model = Translator()
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    model.for_admins_only = True
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_translator(users['translator'], model)
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model.for_admins_only = False
    model.email = 'translator@example.org'
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_member(users['translator'], model)  # elevated
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    model.for_admins_only = True
    model.email = 'translator@example.org'
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_member(users['translator'], model)  # elevated
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model.for_admins_only = False
    model.email = 'translator@example.org'
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_member(users['translator'], model)  # elevated
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    model.for_admins_only = True
    model.email = 'translator@example.org'
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_member(users['translator'], model)  # elevated
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # TranslatorCollection
    model = TranslatorCollection(translator_app)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    # File
    model = File(published=False)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model = File(published=True)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # GeneralFile
    model = GeneralFile(published=False)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model = GeneralFile(published=True)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    # GeneralFileCollection
    model = GeneralFileCollection(session)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # Topic
    model = Topic('Topic', access='public')
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    model = Topic('Topic', access='secret')
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    model = Topic('Topic', access='private')
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_no_access(users['member'], model)
    assert_no_access(users['translator'], model)
    assert_no_access(users['anonymous'], model)
    assert_no_access(None, model)

    model = Topic('Topic', access='member')
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_no_access(users['anonymous'], model)
    assert_no_access(None, model)

    # Ticket
    model = Ticket()
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # TicketCollection
    model = TicketCollection(session)
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # AccreditationTicket
    model = AccreditationTicket(handler_code='AKK')
    assert_admin(users['admin'], model)
    assert_anonymous(users['editor'], model)  # restricted
    assert_anonymous(users['member'], model)  # restricted
    assert_anonymous(users['translator'], model)  # restricted
    assert_anonymous(users['anonymous'], model)  # restricted
    assert_anonymous(None, model)

    # TranslatorMutationTicket
    model = TranslatorMutationTicket(
        handler_code='TRN',
        handler_data={'handler_data': {'submitter_email': None}}
    )
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model.handler_data['handler_data']['submitter_email'] = \
        'admin@example.org'
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model.handler_data['handler_data']['submitter_email'] = \
        'editor@example.org'
    assert_admin(users['admin'], model)
    assert_anonymous(users['editor'], model)  # elevated
    assert_no_access(users['member'], model)  # restricted
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model.handler_data['handler_data']['submitter_email'] = \
        'member@example.org'
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_anonymous(users['member'], model)  # elevated
    assert_no_access(users['translator'], model)  # restricted
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    model.handler_data['handler_data']['submitter_email'] = \
        'translator@example.org'
    assert_admin(users['admin'], model)
    assert_no_access(users['editor'], model)  # restricted
    assert_no_access(users['member'], model)  # restricted
    assert_anonymous(users['translator'], model)  # elevated
    assert_no_access(users['anonymous'], model)  # restricted
    assert_no_access(None, model)

    # Accreditation
    model = Accreditation(None, None, None)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)

    # TranslatorMutation
    model = TranslatorMutation(None, None, None)
    assert_admin(users['admin'], model)
    assert_editor(users['editor'], model)
    assert_member(users['member'], model)
    assert_translator(users['translator'], model)
    assert_anonymous(users['anonymous'], model)
    assert_anonymous(None, model)
