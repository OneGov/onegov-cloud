from onegov.activity.matching import PreferMotivated
from onegov.activity.matching import PreferInAgeBracket
from onegov.activity.matching import PreferAssociationChildren
from onegov.activity.matching import PreferOrganiserChildren
from onegov.core.utils import Bunch


def test_prefer_motivated():
    motivation_score = PreferMotivated()

    assert motivation_score(Bunch(priority=1)) == 1
    assert motivation_score(Bunch(priority=0)) == 0
    assert motivation_score(Bunch(priority=123)) == 123


def test_prefer_in_age_bracket():
    age_range = None
    attendee_age = None

    age_bracket_score = PreferInAgeBracket(
        get_age_range=lambda b: age_range,
        get_attendee_age=lambda b: attendee_age)

    age_range = (10, 20)
    attendee_age = 10

    assert age_bracket_score(None) == 1.0

    attendee_age = 21
    assert age_bracket_score(None) == 0.9

    attendee_age = 22
    assert age_bracket_score(None) == 0.8

    attendee_age = 23
    assert age_bracket_score(None) == 0.7

    attendee_age = 30
    assert age_bracket_score(None) == 0.0

    attendee_age = 9
    assert age_bracket_score(None) == 0.9

    attendee_age = 8
    assert age_bracket_score(None) == 0.8


def test_prefer_organiser_children():

    is_organiser_child = None

    organiser_child_score = PreferOrganiserChildren(
        get_is_organiser_child=lambda c: is_organiser_child)

    is_organiser_child = True
    assert organiser_child_score(None) == 1.0

    is_organiser_child = False
    assert organiser_child_score(None) == 0.0


def test_prefer_association_children():

    is_association_child = None

    association_child_score = PreferAssociationChildren(
        get_is_association_child=lambda c: is_association_child)

    is_association_child = True
    assert association_child_score(None) == 1.0

    is_association_child = False
    assert association_child_score(None) == 0.0
