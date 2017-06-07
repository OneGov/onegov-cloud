from onegov.page import Page
from onegov.form import FormDefinition
from onegov.reservation import Resource


class PersonMove(object):
    """ Represents a single move of a linked person. """

    def __init__(self, session, obj, subject, target, direction):
        self.session = session
        self.obj = obj

        # remove the dashes from the uuid
        self.subject = subject.replace('-', '')
        self.target = target.replace('-', '')
        self.direction = direction

    def execute(self):
        self.obj.move_person(
            subject=self.subject,
            target=self.target,
            direction=self.direction
        )

    @classmethod
    def for_url_template(cls, obj):
        return cls(
            session=None,
            obj=obj,
            subject='{subject_id}',
            target='{target_id}',
            direction='{direction}'
        )

    @staticmethod
    def get_implementation(obj):
        # XXX this is not really extendable by other org applications. They
        # need to override this function *and* define new paths for each class
        # they add.
        #
        # To simplify we should create a registry using dectate, which handles
        # the classes for us. We'd only have one path and the PersonMove
        # class would gain a 'type' and a generic 'key' property which we would
        # use to lookup the actual handler for the move.
        #
        # For example:
        #
        # @App.person_move_handler()
        # class PagePersonMoveMapping(object):
        #     def get_object(self, key):
        #        ...
        #     def get_key(self, obj):
        #        ...
        #
        if isinstance(obj, Page):
            return PagePersonMove

        if isinstance(obj, FormDefinition):
            return FormPersonMove

        if isinstance(obj, Resource):
            return ResourcePersonMove

        raise NotImplementedError


class PagePersonMove(PersonMove):
    """ Represents a single move of a linked person on a page. """

    @property
    def key(self):
        return self.obj.id


class FormPersonMove(PersonMove):
    """ Represents a single move of a linked person on a form definition. """

    @property
    def key(self):
        return self.obj.name


class ResourcePersonMove(PersonMove):
    """ Represents a single move of a linked person on a form definition. """

    @property
    def key(self):
        return self.obj.id
