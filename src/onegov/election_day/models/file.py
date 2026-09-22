from onegov.file import File


class BallotFile(File):

    __mapper_args__ = {'polymorphic_identity': 'ballot_file'}
