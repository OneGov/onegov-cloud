Testing a new release
=====================

Before each new big release, the tests described in this document should be run.
Alternatively, only the relevant tests (i.e. the scenarios which appear on the
next election day) should be run before each election day.

1 Automated Tests
-----------------

### Unit-Tests

The unit tests are run automatically after every commit using
[Travis](https://travis-ci.org/OneGov/onegov.election_day).

### Crawler

There is a [crawler](https://github.com/msom/crawler.elections) available which
allows to fetch all subpages of all known instances; run:

```
./run.py production
./run.py test
```

2 POST-Upload
-------------

Results can be uploaded using a POST request and the format of the WabstiCExport
program, see [here](README.md#curl-examples).

3 Manual Tests
--------------

It's important to test the code manually, to see visual flaws etc. One can use this checklist as an orientation what to check:

- [ ] Localization of the page
  - [ ] Does the localization work, i.e. can you switch the languages?
  - [ ] Does it look like everything is translated (especially in the front-end)?
- [ ] Do the overview views look OK?
  - [ ] The front page
  - [ ] The archive pages
  - [ ] Does the sorting work?
  - [ ] The page of an individual date
  - [ ] The JSON views (`json` and `summary`)
  - [ ] The data exports
  - [ ] Can you subsribe/unsubscribe to SMS notifications?
- [ ] Does the backend look OK?
  - [ ] Does the login and logout work?
  - [ ] Does the pagination work?
  - [ ] Can you create/edit/delete elections and votes?
  - [ ] Can you create/edit/delete data sources and mappings?
  - [ ] Can you view/remove the subscribers?
  - [ ] Does the sorting work?
- [ ] Does the (SMS) notification work?
- [ ] Do the (front end) views look OK
  - [ ] On different browsers?
  - [ ] On a mobile?
- [ ] Does the headerless mode work? (`?headerless` / `?headerful`)
- [ ] Do the exception views (not found, unauthorized) work?
- [ ] Are linked communal and cantonal instances working?
  - [ ] Do the results get copied to the other instances (`onegov-election-day fetch`)?
  - [ ] Do the links link to the full view on the other instance?
  - [ ] Are the communal results shown instead of the cantonal total on the communal instance?
- [ ] Do the embedded maps and charts look ok? ([serve them!](https://gist.github.com/willurd/5720255))
  - [ ] Ballot Maps
  - [ ] Candidates Bar Charts
  - [ ] List Bar Charts
  - [ ] List Connection Charts
  - [ ] Panachage Charts
  - [ ] Party Charts
- [ ] Are PDFs and SVGs created? (`onegov-election-day generate-media`)
  - [ ] New Votes and Elections
  - [ ] Changed Votes and Elections
  - [ ] Do the PDFs look ok?
    - [ ] Simple Votes
    - [ ] Complex Votes
    - [ ] Majorz Elections
    - [ ] Proporz Elections with historical party data
    - [ ] Proporz Elections with historical party data
  - [ ] Do the SVGs look ok?
    - [ ] Ballot Maps
    - [ ] Candidates Bar Charts
    - [ ] List Bar Charts
    - [ ] List Connection Charts
    - [ ] Panachage Charts
    - [ ] Party Charts
- [ ] Does the HipChat integration work?
- [ ] Do the upload of results work?
  - [ ] Typcial scenarios for uploading vote results
    - [ ] Upload a simple cantonal vote on a cantonal instance by using the standard format as described in the docs (VS, DC, IC, FS), e.g. for **GR**
      - [ ] Check the empty vote results (RN)
      - [ ] Upload temporary results (RT)
      - [ ] (Upload a roundtrip)
      - [ ] Upload the completed results (RF)
      - [ ] (Upload a roundtrip)
    - [ ] Upload a complex cantonal vote on a cantonal instance by using the standard format as described in the docs (VC, DC, IC, FS), e.g. for **ZG**
      - [ ] Check the empty vote results (RN)
      - [ ] Upload temporary results (RT)
      - [ ] (Upload a roundtrip)
      - [ ] Upload the completed results (RF)
      - [ ] (Upload a roundtrip)
    - [ ] Upload a simple communal vote on a communal instance by using the standard format as described in the docs (VS, DM, IM, FS), e.g. for **Wil**
      - [ ] Check the empty vote results (RN)
      - [ ] Upload temporary results (RT)
      - [ ] (Upload a roundtrip)
      - [ ] Upload the completed results (RF)
      - [ ] (Upload a roundtrip)
      - [ ] Check if the results have been fetched on the connected cantonal instance (e.g. **SG**)
    - [ ] Upload a simple, federal vote on a cantonal instance using the wabsti format (VS, DC, IC, FW), e.g. for **SG**
      - [ ] Check the empty vote results (RN)
      - [ ] Upload temporary results (RT)
      - [ ] (Upload a roundtrip)
      - [ ] Upload the completed results (RF)
      - [ ] (Upload a roundtrip)
      - [ ] Check if the results have been fetched on the connected communal instance (e.g. **Wil**)
  - [ ] Typical scenarios for uploading election results
    - [ ] *ToDo: Define typical scenarios*
    - [ ] Does a round trip produce the same results?
      - [ ] For RT and RF of the above variants


### Upload Dimensions

There are a lot of different possiblities to upload results, here are the typical dimension which should be considered for testing:

- Common

  - Instance
    - **IC**: Cantonal instance
    - **IM**: Communal instance
      - **IMM**: Communal instance with a map
      - **IMN**: Communal instance without a map
  - Domain
    - **DF**: Federal election or vote
    - **DC**: Cantonal election or vote
    - **DM**: Communal election or vote
  - Results
    - **RN**: No results
    - **RT**: Temporary results
    - **RF**: Full results

- Votes

  - Type
    - **VS**: Simple votes
    - **VC**: Complex votes
  - Upload format
    - **FS**: Standard format
    - **FI**: Internal format
    - **FW**: Wabsti format

- Election

  - Type

    - **EM**: Majorz elections
    - **EP**: Proporz elections

  - Upload format

    - **FI**: Internal format
    - **FW**: Wabsti format
    - **FM**: SESAM format

  - Party results

    - **PR**: Contains party results
    - **PN**: No party results

  - Missing Parts (FW only!)

    - **ML**: Missing list connection (EP + FW)
    - **MC**: Missing candidates (EP + FW)
    - **MS**: Missing statistics (EP + FW)
    - **MS**: Missing completed flag (EP + FW)
    - **MS**: Missing majority (EM + FW/FM)

    ​
