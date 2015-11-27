class PersonMove(object):
    """ Represents a single move of a linked person. """

    def __init__(self, session, page, subject, target, direction):
        self.session = session
        self.page = page
        self.subject = subject
        self.target = target
        self.direction = direction

    @classmethod
    def for_url_template(cls, page):
        return cls(
            session=None,
            page=page,
            subject='{subject_id}',
            target='{target_id}',
            direction='{direction}'
        )

    @property
    def page_id(self):
        return self.page.id

    def execute(self):
        self.page.move_person(
            subject=self.subject,
            target=self.target,
            direction=self.direction
        )
