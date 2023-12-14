from itertools import groupby

from functools import cached_property


# This can be changed anytime without making further changes
# We assume - like for the Excel - that we will not add other languages in
# the future and do not use translations strings here
from onegov.file import File, FileCollection
from onegov.translator_directory.models.translator import Translator

DEFAULT_DOCUMENT_CATEGORIES = (
    'Antrag',
    'Diplome und Zertifikate',
    'Abklärungen',
    'Bestätigungen der Koordinationsstelle',
    'Beschwerden',
    'Korrespondenz',
    'Diverses'
)


class TranslatorDocumentCollection(FileCollection):

    supported_content_types = 'all'

    def __init__(self, session, translator_id, category):
        super().__init__(session, type="*", allow_duplicates=True)

        self.translator_id = translator_id
        self.category = category or DEFAULT_DOCUMENT_CATEGORIES[0]

    @cached_property
    def translator(self):
        return self.session.query(Translator).filter_by(
            id=self.translator_id).first()

    @cached_property
    def unique_categories(self):
        """Returns a list of the defined default categories and the ones in
        the database."""
        q = self.session.query(File.note).filter(File.note != None)
        from_files = tuple(f.note for f in q.distinct())
        return sorted(set(from_files + DEFAULT_DOCUMENT_CATEGORIES))

    @property
    def files_by_category(self):
        files = sorted(self.translator.files, key=lambda f: f.note or '')
        return tuple(
            (category, tuple(files))
            for category, files in groupby(files, key=lambda f: f.note)
        ) if files else ()
