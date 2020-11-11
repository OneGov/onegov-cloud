from onegov.file import File


class TranslatorVoucherFile(File):
    __mapper_args__ = {'polymorphic_identity': 'translator_voucher'}
