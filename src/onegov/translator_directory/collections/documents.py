from onegov.file import FileCollection


class TranslatorFileCollection(FileCollection):
    supported_content_types = 'all'
    __type = 'application'

    def __init__(self, session, order_by='name'):
        super().__init__(session, type=self.__type, allow_duplicates=False)

        self.order_by = order_by
        self.direction = order_by == 'name' and 'ascending' or 'descending'


class ApplicationFileCollection(TranslatorFileCollection):
    __type = 'application'


class CertificateFileCollection(TranslatorFileCollection):
    __type = 'certificate'


class ClarficationFileCollection(TranslatorFileCollection):
    __type = 'clarification'


class ConfirmationFileCollection(TranslatorFileCollection):
    __type = 'confirmation'


class ComplaintFileCollection(TranslatorFileCollection):
    __type = 'complaint'


class CorrespondenceFileCollection(TranslatorFileCollection):
    __type = 'correspondence'


class MiscFileCollection(TranslatorFileCollection):
    __type = 'misc'



