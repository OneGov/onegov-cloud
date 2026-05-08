from __future__ import annotations

from onegov.fsi.forms.course import InviteCourseForm


def test_course_invite_form() -> None:
    form = InviteCourseForm(
        data={
            'attendees': '\n'.join((
                'test1@email.com, test2@email.com',
                'newline@email.com'
            ))
        }
    )
    assert form.get_useful_data() == (
        'test1@email.com',
        'test2@email.com',
        'newline@email.com'
    )
