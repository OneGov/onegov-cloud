from onegov.ballot import Election, Vote


def add_last_modified_header(response, last_modified):
    """ Adds the give date to the response as Last-Modified header. """

    if last_modified:
        response.headers.add(
            'Last-Modified',
            last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
        )


def get_election_summary(election, request):
    """ Returns some basic informations about the given election as a JSON
    seriazable dict. """

    return {
        'date': election.date.isoformat(),
        'domain': election.domain,
        'last_modified': election.last_result_change.isoformat(),
        'progress': {
            'counted': election.counted_municipalities or 0,
            'total': election.total_municipalities or 0
        },
        'title': election.title_translations,
        'type': 'election',
        'url': request.link(election),
    }


def get_vote_summary(vote, request):
    """ Returns some basic informations about the given vote as a JSON
    seriazable dict. """

    divider = len(vote.ballots) or 1

    return {
        'answer': vote.answer or "",
        'date': vote.date.isoformat(),
        'domain': vote.domain,
        'last_modified': vote.last_result_change.isoformat(),
        'nays_percentage': vote.nays_percentage,
        'progress': {
            'counted': (vote.progress[0] or 0) / divider,
            'total': (vote.progress[1] or 0) / divider
        },
        'title': vote.title_translations,
        'type': 'vote',
        'url': request.link(vote),
        'yeas_percentage': vote.yeas_percentage,
    }


def get_summary(item, request):
    """ Returns some basic informations about the given election/vote as a JSON
    seriazable dict. """
    if isinstance(item, Election):
        return get_election_summary(item, request)

    if isinstance(item, Vote):
        return get_vote_summary(item, request)

    raise NotImplementedError(
        "get_summary can't handle type {}".format(type(item))
    )


def get_summaries(items, request):
    """ Converts the given list of election/votes to a JSON seriazable
    list of summaries.

    """

    return [get_summary(item, request) for item in items]


def get_archive_links(archive, request):
    """ Returns a JSON seriazable dict of available archive links. """

    return {
        str(year): request.link(archive.for_date(year))
        for year in archive.get_years()
    }
