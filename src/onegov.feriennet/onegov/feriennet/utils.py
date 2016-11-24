from onegov.activity.matching import PreferAdminChildren
from onegov.activity.matching import PreferInAgeBracket
from onegov.activity.matching import PreferOrganiserChildren
from onegov.activity.matching import Scoring


def scoring_from_match_settings(session, match_settings):
    match_settings = match_settings or {}

    scoring = Scoring()

    if match_settings.get('prefer_in_age_bracket'):
        scoring.criteria.append(
            PreferInAgeBracket.from_session(session))

    if match_settings.get('prefer_organiser'):
        scoring.criteria.append(
            PreferOrganiserChildren.from_session(session))

    if match_settings.get('prefer_admins'):
        scoring.criteria.append(
            PreferAdminChildren.from_session(session))

    return scoring
