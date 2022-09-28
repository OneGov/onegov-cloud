Elections & votes web application
=================================

Introduction
------------

On election Sunday results will be published regularly on individual elections and votings. With the new *elections & votes* web application, this is done via a web interface, which accepts CSV (UTF-8) or Excel (XLS / XLSX) files with provisional or definitive results. For Excel files, either the first worksheet, or, if available, the worksheet named "results" will be used.

Depending on the election / vote and format, a different number of files is required. Each of these files, irrespective of the file format, consists of a header and any number of result rows. The header contains the name of the columns and is *mandatory*.

This document describes the format of these CSV/Excel files.

Content
-------

1. [Format Specification Elections](format_election_en.md)
2. [Format Specification Votes](format_vote_en.md)
