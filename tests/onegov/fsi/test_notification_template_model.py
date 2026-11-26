from __future__ import annotations

import pytest

from onegov.fsi.models.course_notification_template import (
    CourseInvitationTemplate,
    CourseNotificationTemplate,
    GERMAN_TYPE_TRANSLATIONS,
    NOTIFICATION_TYPES,
    get_template_default,
    template_name,
    template_type_choices,
)


class FakeRequest:
    def translate(self, text: str) -> str:
        return f'T:{text}'


def test_template_type_choices_without_request() -> None:
    choices = template_type_choices()
    # each choice is (type, translation)
    assert tuple(value for value, _ in choices) == NOTIFICATION_TYPES


def test_template_type_choices_with_request() -> None:
    choices = template_type_choices(FakeRequest())  # type: ignore[arg-type]
    assert all(label.startswith('T:') for _, label in choices)


def test_get_template_default() -> None:
    assert get_template_default(None, 'info') == \
        GERMAN_TYPE_TRANSLATIONS['info']
    assert get_template_default(None, 'invitation') == \
        GERMAN_TYPE_TRANSLATIONS['invitation']


def test_get_template_default_from_context() -> None:
    class Ctx:
        current_parameters = {'type': 'reminder'}

    assert get_template_default(Ctx()) == GERMAN_TYPE_TRANSLATIONS['reminder']


def test_template_name() -> None:
    assert template_name('invitation') is not None
    assert template_name('info') is not None

    # translated through the request
    translated = template_name('info', FakeRequest())  # type: ignore[arg-type]
    assert translated.startswith('T:')


def test_template_name_invalid() -> None:
    with pytest.raises(AssertionError):
        template_name('bogus')  # type: ignore[arg-type]


def test_course_invitation_template() -> None:
    template = CourseInvitationTemplate()
    assert template.type == 'invitation'
    assert template.text is None
    assert template.subject == GERMAN_TYPE_TRANSLATIONS['invitation']


def test_notification_template_text_html() -> None:
    template = CourseNotificationTemplate(type='info', text='one\n\ntwo')
    html = template.text_html
    assert html is not None
    assert str(html) == '<p>one</p> <p>two</p>'

    assert CourseNotificationTemplate(type='info').text_html is None


def test_notification_template_duplicate() -> None:
    original = CourseNotificationTemplate(
        type='reminder', subject='Subj', text='body')
    copy = original.duplicate()
    assert copy is not original
    assert copy.id != original.id
    assert copy.type == 'reminder'
    assert copy.subject == 'Subj'
    assert copy.text == 'body'
