from onegov.file import File


class ApplicationFile(File):
    """ Anträge """
    __mapper_args__ = {'polymorphic_identity': 'tapplication'}


class CertificateFile(File):
    """ Zertifikate und Diplome """
    __mapper_args__ = {'polymorphic_identity': 'certificate'}


class ClarificationFile(File):
    """ Abklärungen """
    __mapper_args__ = {'polymorphic_identity': 'clarification'}


class ConfirmationFile(File):
    """ Bestätigungen der Koordinationsstelle """
    __mapper_args__ = {'polymorphic_identity': 'confirmation'}


class ComplaintFile(File):
    """  """
    __mapper_args__ = {'polymorphic_identity': 'complaint'}


class CorrespondenceFile(File):
    __mapper_args__ = {'polymorphic_identity': 'correspondence'}


class MiscFile(File):
    """ Diverses """
    __mapper_args__ = {'polymorphic_identity': 'misc'}
