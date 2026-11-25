from __future__ import annotations

from datetime import datetime
from onegov.town6.homepage_widgets import parsed_rss


RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Jobs</title>
    <link>http://example.org</link>
    <description>Open positions</description>
    <language>de</language>
    <copyright>ACME</copyright>
    <item>
      <title>Job A</title>
      <description>First</description>
      <guid>1</guid>
      <pubDate>Mon, 06 Sep 2021 16:45:00 +0200</pubDate>
    </item>
    <item>
      <title>Job B</title>
      <description>Second</description>
      <guid>2</guid>
      <pubDate>not a date</pubDate>
    </item>
  </channel>
</rss>
"""


def test_parsed_rss() -> None:
    channel = parsed_rss(RSS)

    assert channel.title == 'Jobs'
    assert channel.link == 'http://example.org'
    assert channel.description == 'Open positions'
    assert channel.language == 'de'
    assert channel.copyright == 'ACME'

    items = list(channel.items)
    assert len(items) == 2

    first, second = items
    assert first.title == 'Job A'
    assert first.guid == '1'
    assert isinstance(first.pubDate, datetime)
    assert first.pubDate.year == 2021

    # an unparseable pubDate becomes None
    assert second.title == 'Job B'
    assert second.pubDate is None
