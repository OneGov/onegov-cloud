""" Contains the base application used by other applications. """

import re
import yaml

import base64
import hashlib
import morepath
from collections import defaultdict
from dectate import directive
from email.headerregistry import Address
from functools import wraps
from more.content_security import SELF
from more.content_security import NONE
from more.content_security.core import content_security_policy_tween_factory
from onegov.core import Framework, utils
from onegov.core.framework import default_content_security_policy
from onegov.core.i18n import default_locale_negotiator
from onegov.core.orm import orm_cached
from onegov.core.templates import PageTemplate
from onegov.core.widgets import transform_structure
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.gis import MapboxApp
from onegov.org import directives
from onegov.org.auth import MTANAuth
from onegov.org.initial_content import create_new_organisation
from onegov.org.models import Dashboard
from onegov.org.models import Topic, Organisation, PublicationCollection
from onegov.org.request import OrgRequest
from onegov.org.theme import OrgTheme
from onegov.page import Page, PageCollection
from onegov.pay import PayApp
from onegov.reservation import LibresIntegration
from onegov.search import ElasticsearchApp
from onegov.ticket import TicketCollection
from onegov.ticket import TicketPermission
from onegov.user import UserApp
from onegov.websockets import WebsocketsApp
from purl import URL
from sqlalchemy.orm import noload, undefer
from sqlalchemy.orm.attributes import set_committed_value
from types import MethodType
from webob.exc import WSGIHTTPException, HTTPTooManyRequests


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import (
        Callable, Collection, Iterable, Iterator, Sequence)
    from more.content_security import ContentSecurityPolicy
    from morepath.authentication import Identity, NoIdentity
    from onegov.core.mail import Attachment
    from onegov.core.types import EmailJsonDict, SequenceOrScalar
    from onegov.pay import Price
    from onegov.ticket.collection import TicketCount
    from reg.dispatch import _KeyLookup
    from webob import Response


class OrgApp(Framework, LibresIntegration, ElasticsearchApp, MapboxApp,
             DepotApp, PayApp, FormApp, UserApp, WebsocketsApp):

    serve_static_files = True
    request_class = OrgRequest

    #: org directives
    homepage_widget = directive(directives.HomepageWidgetAction)
    export = directive(directives.ExportAction)
    userlinks = directive(directives.UserlinkAction)
    directory_search_widget = directive(directives.DirectorySearchWidgetAction)
    event_search_widget = directive(directives.EventSearchWidgetAction)
    settings_view = directive(directives.SettingsView)
    boardlet = directive(directives.Boardlet)

    #: cronjob settings
    send_ticket_statistics = True

    def is_allowed_application_id(self, application_id: str) -> bool:
        """ Stops onegov.server from ever passing the request to the org
        application, if the schema does not exist. This way we can host
        onegov.org in a way that allows all requests to ``*.example.org``.

        If the schema for ``newyork.example.org`` exists, the request is
        handled. If the schema does not exist, the request is not handled.

        Here we basically decide if an org exists or not.

        """
        schema = self.namespace + '-' + application_id

        if schema in self.known_schemas:
            return True

        # block invalid schemas from ever being checked
        if not self.session_manager.is_valid_schema(schema):
            return False

        # if the schema exists, remember it
        if self.session_manager.is_schema_found_on_database(schema):
            self.known_schemas.add(schema)

            return True

        return False

    def configure_application(self, **cfg: Any) -> None:
        super().configure_application(**cfg)
        self.known_schemas = set()

        if self.has_database_connection:
            schema_prefix = self.namespace + '-'

            self.known_schemas = {
                s for s in self.session_manager.list_schemas()
                if s.startswith(schema_prefix)
            }

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = False,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:

        self.enable_user_registration = enable_user_registration
        self.enable_yubikey = enable_yubikey
        self.disable_password_reset = disable_password_reset

    def configure_mtan_hook(self, **cfg: Any) -> None:
        """
        This inserts an mtan hook by wrapping the callable we receive
        from the key lookup on get_view.

        We only need to do this once per application instance and we don't
        risk contaminating other applications, since each instance has
        its own dispatch callable.

        This relies heavily on implementation details of `reg.dispatch_method`
        and is thus a little bit fragile, take care when upgrading to newer
        versions of reg!
        """

        # the method_dispatch wraps the function in MethodType and stores
        # it on the instance, this should be a unique instance of the method
        # per instance, and an unique instance of the function per class
        get_view_meth = self.get_view
        assert isinstance(get_view_meth, MethodType)
        get_view = get_view_meth.__func__  # type:ignore[unreachable]
        assert hasattr(get_view, 'key_lookup')
        key_lookup = get_view.key_lookup
        if not isinstance(key_lookup, KeyLookupWithMTANHook):
            get_view.key_lookup = KeyLookupWithMTANHook(key_lookup)
            # it is annoying we have to do this, but it is how reg binds these
            # function calls to the dynamically generated function body
            get_view.__globals__.update(
                _component_lookup=get_view.key_lookup.component,
                _fallback_lookup=get_view.key_lookup.fallback,
            )

            # we also need to insert ourselves into the dispatch, so that calls
            # to .clean/.add_predicates doesn't remove our wrapper
            # this should be safe, since each class gets its own dispatch
            # but it is ugly that we have to access the dispatch using the
            # __self__ on one of the methods
            dispatch = get_view.clean.__self__
            if not getattr(dispatch, '_mtan_hook_configured', False):
                orig_get_key_lookup = dispatch.get_key_lookup
                dispatch.get_key_lookup = (
                    lambda registry:
                    KeyLookupWithMTANHook(orig_get_key_lookup(registry))
                )
                dispatch.key_lookup = get_view.key_lookup
                dispatch._mtan_hook_configured = True

    @orm_cached(policy='on-table-change:organisations')
    def org(self) -> Organisation:
        # even though this could return no Organisation, this can only
        # occur during setup, until after we added an Organisation, so
        # outside of this very narrow use-case this should always return
        # an organisation, so we pretend that it always does
        return self.session().query(Organisation).first()  # type:ignore

    @orm_cached(policy='on-table-change:pages')
    def root_pages(self) -> tuple[Page, ...]:

        def include(page: Page) -> bool:
            if page.type != 'news':
                return True

            return True if page.children else False

        return tuple(p for p in self.pages_tree if include(p))

    @orm_cached(policy='on-table-change:pages')
    def pages_tree(self) -> tuple[Page, ...]:
        """
        This is the entire pages tree preloaded into the individual
        parent/children attributes. We optimize this as much as possible
        by performing the recursive join in Python, rather than SQL.

        """
        query = PageCollection(self.session()).query(ordered=False)
        query = query.options(
            # we populate these relationship ourselves
            noload(Page.parent),
            noload(Page.children),
            # since we cache this result we should undefer loading the
            # page meta, so we don't need to deserialize it every time
            # this causes a fairly substantial overhead on uncached
            # loads of pages_tree, but it's also a fairly big win
            # once it is cached. There may be call-sites other than
            # homepage_pages that benefit from this. If there aren't
            # we can always go back on this decision
            undefer(Page.meta)
        )
        query = query.order_by(Page.order)

        # first we build a map from parent_ids to their children
        parent_to_child = defaultdict(list)
        for page in query:
            parent_to_child[page.parent_id].append(page)

        # then we populate the children and parent based on this information
        # this should result in no pending modifications, because we use
        # set_committed_value to set them
        for page in (
            page
            for pages in parent_to_child.values()
            for page in pages
        ):
            # even though this is a defaultdict, we need to use get()
            # since otherwise we modifiy the dictionary
            children = parent_to_child.get(page.id, [])
            for child in children:
                set_committed_value(child, 'parent', page)
            set_committed_value(page, 'children', children)

        # we return the root pages which should contain references to all
        # the child pages
        return tuple(p for p in parent_to_child.get(None, []))

    @orm_cached(policy='on-table-change:organisations')
    def homepage_template(self) -> PageTemplate:
        structure = self.org.meta.get('homepage_structure')
        if structure:
            widgets = self.config.homepage_widget_registry.values()
            return PageTemplate(transform_structure(widgets, structure))
        else:
            return PageTemplate('')

    @orm_cached(policy='on-table-change:tickets')
    def ticket_count(self) -> 'TicketCount':
        return TicketCollection(self.session()).get_count()

    @orm_cached(policy='on-table-change:ticket_permissions')
    def ticket_permissions(self) -> dict[str, dict[str | None, list[str]]]:
        result: dict[str, dict[str | None, list[str]]] = {}
        for permission in self.session().query(TicketPermission):
            handler = result.setdefault(permission.handler_code, {})
            group = handler.setdefault(permission.group, [])
            group.append(permission.user_group_id.hex)
        return result

    @orm_cached(policy='on-table-change:pages')
    def homepage_pages(self) -> dict[int, list[Topic]]:

        def visit_topics(
            pages: 'Iterable[Page]',
            root_id: int | None = None
        ) -> 'Iterator[tuple[int, Topic]]':
            for page in pages:
                if isinstance(page, Topic):
                    yield root_id or page.id, page

                yield from visit_topics(
                    page.children,
                    root_id=root_id or page.id
                )

        result = defaultdict(list)
        for root_id, topic in visit_topics(self.root_pages):
            if topic.is_visible_on_homepage:
                result[root_id].append(topic)

        for topics in result.values():
            topics.sort(
                key=lambda p: utils.normalize_for_url(p.title)
            )

        return result

    @orm_cached(policy='on-table-change:files')
    def publications_count(self) -> int:
        return PublicationCollection(self.session()).query().count()

    def prepare_email(
        self,
        reply_to: Address | str | None = None,
        category: Literal['marketing', 'transactional'] = 'marketing',
        receivers: 'SequenceOrScalar[Address | str]' = (),
        cc: 'SequenceOrScalar[Address | str]' = (),
        bcc: 'SequenceOrScalar[Address | str]' = (),
        subject: str | None = None,
        content: str | None = None,
        attachments: 'Iterable[Attachment | StrPath]' = (),
        headers: dict[str, str] | None = None,
        plaintext: str | None = None
    ) -> 'EmailJsonDict':
        """ Wraps :meth:`onegov.core.framework.Framework.prepare_email`,
        setting  the reply_to address by using the reply address from
        the organisation settings.

        """

        reply_to = reply_to or self.org.meta.get('reply_to', None)
        if not reply_to:
            assert self.mail is not None
            reply_to = self.mail[category]['sender']

        if isinstance(reply_to, str):
            reply_to = Address(self.org.title, addr_spec=reply_to)

        return super().prepare_email(
            reply_to=reply_to,
            category=category,
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            subject=subject,
            content=content,
            attachments=attachments,
            headers=headers,
            plaintext=plaintext,
        )

    @property
    def theme_options(self) -> dict[str, Any]:
        return self.org.theme_options or {}

    @property
    def font_family(self) -> str | None:
        return self.theme_options.get('font-family-sans-serif')

    @property
    def custom_event_tags(self) -> list[str] | None:
        return self.cache.get_or_create(
            'custom_event_tags', self.load_custom_event_tags
        )

    def load_custom_event_tags(self) -> list[str] | None:
        fs = self.filestorage
        assert fs is not None
        if not fs.exists('eventsettings.yml'):
            return None

        with fs.open('eventsettings.yml', 'r') as f:
            return yaml.safe_load(f).get('event_tags', None)

    @property
    def allowed_iframe_domains(self) -> list[str]:
        return self.cache.get_or_create(
            'allowed_iframe_domains', self.load_allowed_iframe_domains
        )

    def load_allowed_iframe_domains(self) -> list[str] | None:
        fs = self.filestorage
        assert fs is not None
        if not fs.exists('allowed_iframe_domains.yml'):
            return []

        with fs.open('allowed_iframe_domains.yml', 'r') as f:
            return yaml.safe_load(f).get('allowed_domains', [])

    @property
    def hashed_identity_key(self) -> bytes:
        """ Take the sha-256 because we want a key that is 32 bytes long. """
        hash_object = hashlib.sha256()
        hash_object.update(self.identity_secret.encode('utf-8'))
        short_key = hash_object.digest()
        key_base64 = base64.b64encode(short_key)
        return key_base64

    @property
    def custom_event_form_lead(self) -> str | None:
        return self.cache.get_or_create(
            'custom_event_lead', self.load_custom_event_form_lead
        )

    def load_custom_event_form_lead(self) -> str | None:
        fs = self.filestorage
        assert fs is not None
        if not fs.exists('eventsettings.yml'):
            return None

        with fs.open('eventsettings.yml', 'r') as f:
            return yaml.safe_load(f).get('event_form_lead', None)

    def checkout_button(
        self,
        button_label: str,
        title: str,
        price: 'Price | None',
        email: str,
        locale: str
    ) -> str | None:
        provider = self.default_payment_provider

        if not provider:
            return None

        extra: dict[str, Any] = {}

        if self.org.square_logo_url:
            extra['image'] = self.org.square_logo_url

        return provider.checkout_button(
            label=button_label,
            # FIXME: This is a little suspect, since StripePaymentProvider
            #        would previously have raised an exception for a
            #        missing price, should it really be legal to generate
            #        a checkout button when there is no price?
            amount=price and price.amount or None,
            currency=price and price.currency or None,
            email=email,
            name=self.org.name,
            description=title,
            locale=locale.split('_')[0],
            # FIXME: This seems Stripe specific, so it should probably be
            #        built into that payment provider
            allowRememberMe='false',
            **extra
        )

    def redirect_after_login(
        self,
        identity: 'Identity | NoIdentity',
        request: OrgRequest,  # type:ignore[override]
        default: str
    ) -> str | None:
        """ Returns the path to redirect after login, given the request and
        the default login path, which is usually the current path.

        Returns a path or None, if the default should be used.

        """

        # if we already have a target, we do not change it
        if default != '/':
            return None

        # we redirect to the dashboard…
        dashboard = Dashboard(request)

        # …if available…
        if not dashboard.is_available:
            return None

        # …and accessible…
        permission = self.permission_by_view(dashboard, view_name=None)

        if not self._permits(identity, dashboard, permission):
            return None

        return URL(request.link(dashboard)).path()


@OrgApp.webasset_path()
def get_shared_assets_path() -> str:
    return utils.module_path('onegov.shared', 'assets/js')


@OrgApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH', 'fr_CH'}


@OrgApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.org', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@OrgApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@OrgApp.setting(section='i18n', name='locale_negotiator')
def get_locale_negotiator(
) -> 'Callable[[Sequence[str], OrgRequest], str | None]':
    def locale_negotiator(
        locales: 'Sequence[str]',
        request: OrgRequest
    ) -> str | None:

        if request.app.org:
            locales = request.app.org.locales or get_i18n_default_locale()

            if isinstance(locales, str):
                locales = (locales, )

            return default_locale_negotiator(locales, request) or locales[0]
        else:
            return default_locale_negotiator(locales, request)
    return locale_negotiator


@OrgApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@OrgApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@OrgApp.setting(section='core', name='theme')
def get_theme() -> OrgTheme:
    return OrgTheme()


@OrgApp.setting(section='content_security_policy', name='default')
def org_content_security_policy() -> 'ContentSecurityPolicy':
    policy = default_content_security_policy()

    policy.child_src.add(SELF)
    policy.child_src.add('https://*.youtube.com')
    policy.child_src.add('https://*.vimeo.com')
    policy.child_src.add('https://*.infomaniak.com')
    policy.child_src.add('https://checkout.stripe.com')

    policy.connect_src.add(SELF)
    policy.connect_src.add('https://checkout.stripe.com')
    policy.connect_src.add('https://*.google-analytics.com')
    policy.connect_src.add('https://stats.g.doubleclick.net')
    policy.connect_src.add('https://map.geo.bs.ch')
    policy.connect_src.add('https://wmts.geo.bs.ch')
    policy.connect_src.add('https://maps.zg.ch')
    policy.connect_src.add('https://api.mapbox.com')
    policy.connect_src.add('https://stats.seantis.ch')
    policy.connect_src.add('https://geodesy.geo.admin.ch')
    policy.connect_src.add('https://wms.geo.admin.ch/')

    policy.connect_src.add('https://*.projuventute.ch')
    policy.connect_src.add('https://cdn.jsdelivr.net')
    policy.connect_src.add('https://*.usercentrics.eu')

    policy.script_src.add('https:')

    return policy


@OrgApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> 'Callable[[OrgApp, str], Organisation]':
    return create_new_organisation


@OrgApp.setting(section='org', name='status_mail_roles')
def get_status_mail_roles() -> 'Collection[str]':
    return ('admin', 'editor')


@OrgApp.setting(section='org', name='ticket_manager_roles')
def get_ticket_manager_roles() -> 'Collection[str]':
    return ('admin', 'editor')


@OrgApp.setting(section='org', name='require_complete_userprofile')
def get_require_complete_userprofile() -> bool:
    return False


@OrgApp.setting(section='org', name='is_complete_userprofile')
def get_is_complete_userprofile_handler(
) -> 'Callable[[OrgRequest, str], bool]':

    def is_complete_userprofile(request: OrgRequest, username: str) -> bool:
        return True

    return is_complete_userprofile


@OrgApp.setting(section='org', name='default_directory_search_widget')
def get_default_directory_search_widget() -> None:
    return None


@OrgApp.setting(section='org', name='default_event_search_widget')
def get_default_event_search_widget() -> None:
    return None


@OrgApp.setting(section='org', name='public_ticket_messages')
def get_public_ticket_messages() -> 'Collection[str]':
    """ Returns a list of message types which are availble on the ticket
    status page, visible to anyone that knows the unguessable url.

    """

    # do *not* add ticket_note here, those are private!
    return (
        'directory',
        'event',
        'payment',
        'reservation',
        'submission',
        'ticket',
        'ticket_chat',
        'translator_mutation'
    )


@OrgApp.setting(section='org', name='disabled_extensions')
def get_disabled_extensions() -> 'Collection[str]':
    return ()


@OrgApp.tween_factory(under=content_security_policy_tween_factory)
def enable_iframes_tween_factory(
    app: OrgApp,
    handler: 'Callable[[OrgRequest], Response]'
) -> 'Callable[[OrgRequest], Response]':

    no_iframe_paths = (
        r'/auth/.*',
        r'/manage/.*'
    )
    no_iframe_paths_re = re.compile(rf"({'|'.join(no_iframe_paths)})")

    iframe_paths = (
        r'/events/.*',
        r'/event/.*',
        r'/news/.*',
        r'/directories/.*',
        r'/resources/.*',
        r'/resource/.*',
        r'/topics/.*',
    )
    iframe_paths_re = re.compile(rf"({'|'.join(iframe_paths)})")

    def enable_iframes_tween(
        request: OrgRequest
    ) -> 'Response':
        """ Enables iframes. """

        result = handler(request)

        # Allow iframes for other pages for certain paths
        if no_iframe_paths_re.match(request.path_info or '/'):
            request.content_security_policy.frame_ancestors = {NONE}
        elif iframe_paths_re.match(request.path_info or '/'):
            request.content_security_policy.frame_ancestors.add('http://*')
            request.content_security_policy.frame_ancestors.add('https://*')

        # Allow certain domains as iframes on our pages
        for domain in (app.allowed_iframe_domains or []):
            request.content_security_policy.child_src.add(domain)

        return result

    return enable_iframes_tween


@OrgApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@OrgApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@OrgApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@OrgApp.webasset('sortable')
def get_sortable_asset() -> 'Iterator[str]':
    yield 'sortable.js'
    yield 'sortable_custom.js'


@OrgApp.webasset('fullcalendar')
def get_fullcalendar_asset() -> 'Iterator[str]':
    yield 'fullcalendar.css'
    yield 'fullcalendar.js'
    yield 'fullcalendar.de.js'
    yield 'fullcalendar.fr.js'
    yield 'reservationcalendar.jsx'
    yield 'reservationcalendar_custom.js'


@OrgApp.webasset('reservationlist')
def get_reservation_list_asset() -> 'Iterator[str]':
    yield 'reservationlist.jsx'
    yield 'reservationlist_custom.js'


@OrgApp.webasset('code_editor')
def get_code_editor_asset() -> 'Iterator[str]':
    yield 'ace.js'
    yield 'ace-mode-form.js'
    yield 'ace-mode-markdown.js'
    yield 'ace-mode-xml.js'
    yield 'ace-mode-yaml.js'
    yield 'ace-theme-tomorrow.js'
    yield 'formcode'
    yield 'code_editor.js'


@OrgApp.webasset('editor')
def get_editor_asset() -> 'Iterator[str]':
    yield 'bufferbuttons.js'
    yield 'definedlinks.js'
    yield 'filemanager.js'
    yield 'imagemanager.js'
    yield 'table.js'
    yield 'redactor.de.js'
    yield 'redactor.fr.js'
    yield 'redactor.it.js'
    yield 'input_with_button.js'
    yield 'editor.js'


@OrgApp.webasset('timeline')
def get_timeline_asset() -> 'Iterator[str]':
    yield 'react-transition-group.js'
    yield 'timeline.jsx'


# do NOT minify the redactor, or the copyright notice goes away, which
# is something we are not allowed to do per our license
@OrgApp.webasset('redactor', filters={'js': None})
def get_redactor_asset() -> 'Iterator[str]':
    yield 'redactor.js'
    yield 'redactor.css'


@OrgApp.webasset('upload')
def get_upload_asset() -> 'Iterator[str]':
    yield 'upload.js'


@OrgApp.webasset('editalttext')
def get_editalttext_asset() -> 'Iterator[str]':
    yield 'editalttext.js'


@OrgApp.webasset('prompt')
def get_prompt() -> 'Iterator[str]':
    yield 'prompt.jsx'


@OrgApp.webasset('photoswipe')
def get_photoswipe_asset() -> 'Iterator[str]':
    yield 'photoswipe.css'
    yield 'photoswipe-skin.css'
    yield 'photoswipe.js'
    yield 'photoswipe-ui.js'
    yield 'photoswipe-custom.js'


@OrgApp.webasset('tags-input')
def get_tags_input() -> 'Iterator[str]':
    yield 'tags-input.js'
    yield 'tags-input-setup.js'


@OrgApp.webasset('filedigest')
def get_filehash() -> 'Iterator[str]':
    yield 'asmcrypto-lite.js'
    yield 'filedigest.js'


@OrgApp.webasset('monthly-view')
def get_monthly_view() -> 'Iterator[str]':
    yield 'daypicker.js'
    yield 'monthly-view.jsx'


@OrgApp.webasset('common')
def get_common_asset() -> 'Iterator[str]':
    yield 'global.js'
    yield 'polyfills.js'
    yield 'jquery.datetimepicker.css'
    yield 'locale.js'
    yield 'modernizr.js'
    yield 'clipboard.js'
    yield 'jquery.js'
    yield 'foundation.js'
    yield 'foundation.alert.js'
    yield 'foundation.dropdown.js'
    yield 'foundation.orbit.js'
    yield 'foundation.reveal.js'
    yield 'foundation.topbar.js'
    yield 'intercooler.js'
    yield 'underscore.js'
    yield 'react.min.js'
    yield 'react-dom.min.js'
    yield 'create-react-class.min.js'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'typeahead.jsx'
    yield 'moment.js'
    yield 'moment.de-ch.js'
    yield 'moment.fr-ch.js'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'many.jsx'
    yield 'pay'
    yield 'jquery.mousewheel.js'
    yield 'jquery.popupoverlay.js'
    yield 'jquery.load.js'
    yield 'videoframe.js'
    yield 'url.js'
    yield 'date-range-selector.js'
    yield 'lazyalttext.js'
    yield 'lazysizes.js'
    yield 'toggle.js'
    yield 'common.js'
    yield '_blank.js'
    yield 'forms.js'
    yield 'internal_link_check.js'
    yield 'tickets.js'
    yield 'items_selectable.js'
    yield 'notifications.js'
    yield 'foundation.accordion.js'


@OrgApp.webasset('fontpreview')
def get_fontpreview_asset() -> 'Iterator[str]':
    yield 'fontpreview.js'


@OrgApp.webasset('scroll-to-username')
def get_scroll_to_username_asset() -> 'Iterator[str]':
    yield 'scroll_to_username.js'


@OrgApp.webasset('all_blank')
def get_all_blank_asset() -> 'Iterator[str]':
    yield 'all_blank.js'


def wrap_with_mtan_hook(
    func: 'Callable[[OrgApp, Any, OrgRequest], Any]'
) -> 'Callable[[OrgApp, Any, OrgRequest], Any]':

    @wraps(func)
    def wrapped(self: OrgApp, obj: Any, request: OrgRequest) -> Any:
        response = func(self, obj, request)
        if (
            # only do the mTAN redirection stuff if the original view didn't
            # return a client or server error
            not (
                isinstance(response, WSGIHTTPException)
                and response.code >= 400
            )
            and getattr(obj, 'access', None) in ('mtan', 'secret_mtan')
            # managers don't require mtan authentication
            and not request.is_manager
        ):

            # no active mtan session, redirect to mtan auth view
            if not request.active_mtan_session:
                auth = MTANAuth(self, request.path_url)
                return morepath.redirect(request.link(auth, name='request'))

            # access limit exceeded
            if request.mtan_access_limit_exceeded:
                return HTTPTooManyRequests()

            # record access
            request.mtan_accesses.add(url=request.path_url)

        return response

    return wrapped


class KeyLookupWithMTANHook:
    def __init__(self, key_lookup: '_KeyLookup'):
        self.key_lookup = key_lookup

    def component(
        self,
        key: 'Sequence[Any]'
    ) -> 'Callable[..., Any] | None':

        result = self.key_lookup.component(key)
        if result is None:
            return None
        return wrap_with_mtan_hook(result)

    def fallback(
        self,
        key: 'Sequence[Any]'
    ) -> 'Callable[..., Any] | None':

        result = self.key_lookup.fallback(key)
        if result is None:
            return None
        return wrap_with_mtan_hook(result)

    def all(
        self,
        key: 'Sequence[Any]'
    ) -> 'Iterator[Callable[..., Any]]':
        return self.key_lookup.all(key)
