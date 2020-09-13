
from sqlalchemy import desc, and_, or_
from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.translator import Translator

order_cols = (
    'last_name',
    'drive_distance',
)


class TranslatorCollection(GenericCollection, Pagination):

    batch_size = 10

    def __init__(
            self, session,
            page=0,
            written_langs=None,
            spoken_langs=None,
            order_by=None,
            order_desc=False,
            user_role=None,
            search=None
    ):
        super().__init__(session)
        self.page = page
        self.user_role = user_role
        self.search = self.truncate(search)

        if spoken_langs:
            assert isinstance(spoken_langs, list)
        if written_langs:
            assert isinstance(written_langs, list)

        self.written_langs = written_langs
        self.spoken_langs = spoken_langs

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
            self.order_by == other.order_by,
            self.order_desc == other.order_desc,
            self.search == other.search
        ))

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
    def by_search_term_expression(self):
        """Search for any word in any field of the search columns"""
        words = self.search.split(' ')
        cols = self.search_columns
        return tuple(col.ilike(f'%{word}%') for col in cols for word in words)

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            page=index,
            written_langs=self.written_langs,
            spoken_langs=self.spoken_langs,
            order_by=self.order_by,
            order_desc=self.order_desc
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

        if self.user_role != 'admin':
            query = query.filter(Translator.for_admins_only == False)

        if self.search:
            query = query.filter(or_(*self.by_search_term_expression))

        query = query.order_by(self.order_expression)
        return query

    def by_form(self, form):
        return self.__class__(
            self.session,
            page=0,
            order_desc=form.order_desc.data,
            written_langs=form.written_langs.data,
            spoken_langs=form.spoken_langs.data,
            order_by=form.order_by.data
        )
