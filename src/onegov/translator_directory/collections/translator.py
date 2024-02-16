from sqlalchemy import desc, and_, or_
from onegov.core.collection import GenericCollection, Pagination
from onegov.core.crypto import random_password
from onegov.gis import Coordinates
from onegov.translator_directory.constants import full_text_max_chars
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory import log
from onegov.user import UserCollection


order_cols = (
    'last_name',
    'drive_distance',
)


class TranslatorCollection(GenericCollection, Pagination):

    batch_size = 10

    def __init__(
            self, app,
            page=0,
            written_langs=None,
            spoken_langs=None,
            monitor_langs=None,
            order_by=None,
            order_desc=False,
            user_role=None,
            search=None,
            guilds=None,
            interpret_types=None,
            state='published',
            admissions=None,
            genders=None
    ):
        super().__init__(app.session())
        self.app = app
        self.page = page
        self.user_role = user_role
        self.search = self.truncate(search, maxchars=full_text_max_chars)
        self.guilds = guilds or []
        self.interpret_types = interpret_types or []
        self.state = state
        self.admissions = admissions or []
        self.genders = genders or []

        if spoken_langs:
            assert isinstance(spoken_langs, list)
        if written_langs:
            assert isinstance(written_langs, list)
        if monitor_langs:
            assert isinstance(monitor_langs, list)

        self.written_langs = written_langs
        self.spoken_langs = spoken_langs
        self.monitor_langs = monitor_langs

        if not order_by or order_by not in order_cols:
            order_by = order_cols[0]

        order_desc = False if order_desc not in (True, False) else order_desc

        self.order_by = order_by
        self.order_desc = order_desc

    def __eq__(self, other):
        return all((
            self.page == other.page,
            self.written_langs == other.written_langs,
            self.spoken_langs == other.spoken_langs,
            self.monitor_langs == other.monitor_langs,
            self.order_by == other.order_by,
            self.order_desc == other.order_desc,
            self.search == other.search,
            self.guilds == other.guilds,
            self.interpret_types == other.interpret_types,
            self.admissions == other.admissions,
            self.genders == other.genders
        ))

    def add(self, update_user=True, **kwargs):
        coordinates = kwargs.pop('coordinates', Coordinates())
        item = super().add(**kwargs)
        item.coordinates = coordinates
        if update_user:
            self.update_user(item, item.email)
        self.session.flush()
        return item

    def delete(self, item):
        self.update_user(item, None)
        self.session.delete(item)
        self.session.flush()

    def update_user(self, item, new_email):
        """ Keep the translator and its user account in sync.

        * Creates a new user account if an email address is set (if not already
          existing).
        * Disable user accounts if an email has been deleted.
        * Change usernames if an email has changed.
        * Make sure used user accounts have the right role.
        * Make sure used user accounts are activated.
        * Make sure the password is changed if activated or disabled.

        """

        old_email = item.email
        users = UserCollection(self.session)
        old_user = users.by_username(old_email)
        new_user = users.by_username(new_email)
        create = False
        enable = None
        disable = []

        if not new_email:
            # email has been unset: disable obsolete users
            disable.extend([old_user, new_user])
        else:
            if new_email == old_email:
                # email has not changed, old_user == new_user
                if not old_user:
                    create = True
                else:
                    enable = old_user
            else:
                # email has changed: ensure user exist
                if old_user and new_user:
                    disable.append(old_user)
                    enable = new_user
                elif not old_user and not new_user:
                    create = True
                else:
                    enable = old_user if old_user else new_user

        if create:
            log.info(f'Creating user {new_email}')
            users.add(
                new_email, random_password(16), role='translator',
                realname=item.full_name
            )

        if enable:
            corrections = {
                'username': new_email,
                'role': 'translator',
                'active': True,
                'source': None,
                'source_id': None
            }
            corrections = {
                attribute: value for attribute, value in corrections.items()
                if getattr(enable, attribute) != value
            }
            if corrections:
                log.info(f'Correcting user {enable.username} to {corrections}')
                for attribute, value in corrections.items():
                    setattr(enable, attribute, value)
                enable.logout_all_sessions(self.app)

        for user in disable:
            if user:
                log.info(f'Deactivating user {user.username}')
                user.active = False
                user.logout_all_sessions(self.app)

    @staticmethod
    def truncate(text, maxchars=25):
        return text[:maxchars] if text and len(text) > maxchars else text

    @property
    def model_class(self):
        return Translator

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    @property
    def order_expression(self):
        order_by = getattr(self.model_class, self.order_by)
        return desc(order_by) if self.order_desc else order_by

    @property
    def by_spoken_lang_expression(self):
        return tuple(
            Translator.spoken_languages.any(id=lang_id)
            for lang_id in self.spoken_langs
        )

    @property
    def by_written_lang_expression(self):
        return tuple(
            Translator.written_languages.any(id=lang_id)
            for lang_id in self.written_langs
        )

    @property
    def by_monitor_lang_expression(self):
        return tuple(
            Translator.monitoring_languages.any(id=lang_id)
            for lang_id in self.monitor_langs
        )

    @property
    def by_search_term_expression(self):
        """Search for any word in any field of the search columns"""
        words = self.search.split(' ')
        cols = self.search_columns
        return tuple(col.ilike(f'%{word}%') for col in cols for word in words)

    @property
    def by_professional_guilds_expression(self):
        keys = (
            'expertise_professional_guilds',
            'expertise_professional_guilds_other'
        )
        return tuple(
            or_(*(Translator.meta[key].contains((v, )) for key in keys))
            for v in self.guilds
        )

    @property
    def by_interpreting_types_expression(self):
        return tuple(
            Translator.meta['expertise_interpreting_types'].contains((v,))
            for v in self.interpret_types
        )

    @property
    def by_admission(self):
        return tuple(
            Translator.admission == admission
            for admission in self.admissions
        )

    @property
    def by_gender(self):
        return tuple(
            Translator.gender == gender
            for gender in self.genders
        )

    def page_by_index(self, index):
        return self.__class__(
            self.app,
            page=index,
            written_langs=self.written_langs,
            spoken_langs=self.spoken_langs,
            monitor_langs=self.monitor_langs,
            user_role=self.user_role,
            search=self.search,
            order_by=self.order_by,
            order_desc=self.order_desc,
            guilds=self.guilds,
            interpret_types=self.interpret_types,
            state=self.state,
            admissions=self.admissions,
            genders=self.genders
        )

    @property
    def search_columns(self):
        """ The columns used for text search. """

        return [
            self.model_class.first_name,
            self.model_class.last_name
        ]

    def query(self):
        query = super().query()

        if self.spoken_langs:
            query = query.filter(and_(*self.by_spoken_lang_expression))

        if self.written_langs:
            query = query.filter(and_(*self.by_written_lang_expression))

        if self.monitor_langs:
            query = query.filter(and_(*self.by_monitor_lang_expression))

        if self.user_role != 'admin':
            query = query.filter(Translator.for_admins_only == False)

        if self.search:
            query = query.filter(or_(*self.by_search_term_expression))

        if self.interpret_types:
            query = query.filter(and_(*self.by_interpreting_types_expression))

        if self.guilds:
            query = query.filter(and_(*self.by_professional_guilds_expression))

        if self.state:
            query = query.filter(Translator.state == self.state)

        if self.admissions:
            query = query.filter(or_(*self.by_admission))

        if self.genders:
            query = query.filter(or_(*self.by_gender))

        query = query.order_by(self.order_expression)
        return query

    def by_form(self, form):
        return self.__class__(
            self.app,
            page=0,
            order_desc=form.order_desc.data,
            written_langs=form.written_langs.data,
            spoken_langs=form.spoken_langs.data,
            order_by=form.order_by.data
        )

    @property
    def available_additional_professional_guilds(self):
        query = self.session.query(
            Translator.meta['expertise_professional_guilds_other']
        )
        return sorted({tag for result in query for tag in result[0]})
