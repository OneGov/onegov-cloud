# Changes

## 2026.33

`2026-06-19` | [720d0843df...e3076b731f](https://github.com/OneGov/onegov-cloud/compare/720d0843df^...e3076b731f)

**Upgrade hints**
- `onegov-org --select /onegov_town6/* fix-submission-file-sizes`
### Core

##### Replaces `editdistance` with `rapidfuzz`

`editdistance` is no longer maintained and has some known bugs that
never got fixed.

`Bugfix` | [40cf4a56c6](https://github.com/onegov/onegov-cloud/commit/40cf4a56c6a749a5cf085cf70bc3aac45a738179)

##### Cleans up stale dependencies

`Bugfix` | [e740698bef](https://github.com/onegov/onegov-cloud/commit/e740698bef01c11a9ff5b74a8e4956345ae60686)

##### Avoids unnecessary copy when converting XLS(X) files to CSV

`Performance` | [ccbb81079b](https://github.com/onegov/onegov-cloud/commit/ccbb81079b3eb3311abcccd57ccc602ad83772cd)

### Form

##### Update image size information in submission after potential resizing

`Feature` | [OGC-3199](https://linear.app/onegovcloud/issue/OGC-3199) | [61752c305e](https://github.com/onegov/onegov-cloud/commit/61752c305e79c6aefb0a24bb46ac294ec94c0fbe)

### Foundation

##### Replaces `libsass` with dart sass binary.

`Feature` | [OGC-3071](https://linear.app/onegovcloud/issue/OGC-3071) | [d125e1c894](https://github.com/onegov/onegov-cloud/commit/d125e1c89482bb9ef61f91fc7a2959ee41429dd4)

### Org

##### Use display name for Ticket handler codes.

`Feature` | [OGC-3216](https://linear.app/onegovcloud/issue/OGC-3216) | [720d0843df](https://github.com/onegov/onegov-cloud/commit/720d0843df3211cbe5494c72f3207acad2fbcadc)

##### Replace assert current_user is not None with a Sentry warning and HTTPForbidden

Adds OrgRequest.get_current_user() which captures a Sentry warning and raises HTTPForbidden when current_user is None despite a valid session. Replaces all bare asserts across feriennet, org, town6 and translator_directory.

`Feature` | [HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7467148569/](#HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7467148569/) | [a893216970](https://github.com/onegov/onegov-cloud/commit/a893216970b2006c218299cd68d7a774fee64d3e)

##### Descriptive subjects with resource, date and activity.

Subjects now show resource name, reservation date(s), and activity type
(e.g. "Turnhalle - 15.06.2026 - Anfrage") instead of generic text.
Threading via Message-ID/In-Reply-To/References already groups emails
in mail clients.

`Feature` | [OGC-2158](https://linear.app/onegovcloud/issue/OGC-2158) | [ed0d8a4526](https://github.com/onegov/onegov-cloud/commit/ed0d8a452669b679db0e6b0d18f6ed550498be22)

##### Makes resource notification delivery time configurable

`Feature` | [OGC-3205](https://linear.app/onegovcloud/issue/OGC-3205) | [e3076b731f](https://github.com/onegov/onegov-cloud/commit/e3076b731ffec8c1414fa7165a09b10421c8c27a)

### People

##### Fix potential crash in `PersonCollection.people_by_organization`

`Bugfix` | [ONEGOV-CLOUD-5FT](https://seantis-gmbh.sentry.io/issues/?query=ONEGOV-CLOUD-5FT) | [5e1c1dfd83](https://github.com/onegov/onegov-cloud/commit/5e1c1dfd832e74e5e030a25ffced803cd1d7243b)

### Reservation

##### Fixes raises 500 when sibling slot was deleted

Catch InvalidReservationToken and InvalidReservationError from libres in the adjust_reservation view and show a user-visible error instead of an unhandled 500.

Triggered by a bug in libres where rejecting one reservation on a partly_available allocation deleted the sibling reservation's slot. The view-level catch acts as a fallback for any pre-existing inconsistent data.

`Bugfix` | [HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7543641349](#HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7543641349) | [65f4149f21](https://github.com/onegov/onegov-cloud/commit/65f4149f21c12be52a93d73b1233ddf28741fa96)

## 3

`2026-06-18` | [3d714d485a...31dffd169f](https://github.com/OneGov/onegov-cloud/compare/3d714d485a^...31dffd169f)

## 2

`2026-06-15` | [092d68c15c...092d68c15c](https://github.com/OneGov/onegov-cloud/compare/092d68c15c^...092d68c15c)

## 1

`2026-06-15` | [0e89ad461d...0f64092db1](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...0f64092db1)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

## 2026.32

`2026-06-15` | [8f95a83b07...c3dae2d191](https://github.com/OneGov/onegov-cloud/compare/8f95a83b07^...c3dae2d191)

**Upgrade hints**
- onegov-translator --select /translator_directory/* strip-whitespace-from-names
### Agency

##### Skip agencies with no portrait during link check

`Bugfix` | [HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7541280427](#HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7541280427) | [f3347bed56](https://github.com/onegov/onegov-cloud/commit/f3347bed565df36101b8fe75a941690bfacf88d3)

### Directory

##### Replaces DuplicateEntry error with an automated increased suffix as name

`Feature` | [OGC-3178](https://linear.app/onegovcloud/issue/OGC-3178) | [3fc05807de](https://github.com/onegov/onegov-cloud/commit/3fc05807de2fc993020b611921e773ac44e50d7b)

##### Derive populate_obj exclude set from directory structure fields

Previously the exclude fields were derived by field type and some needed to be added explicitly

`Bugfix` | [OGC-3195](https://linear.app/onegovcloud/issue/OGC-3195) | [8f95a83b07](https://github.com/onegov/onegov-cloud/commit/8f95a83b07d146481293cc8ce736f374ea3f64e4)

### Election Day

##### SEO and Open Graph for WAB applications

`Feature` | [OGC-3169](https://linear.app/onegovcloud/issue/OGC-3169) | [250e96c455](https://github.com/onegov/onegov-cloud/commit/250e96c455ff61b4d2f9ac0b25569659142f93ba)

### Form

##### Emits error for field with no type definition in formcode

`Bugfix` | [HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7538527054](#HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7538527054) | [d88a4f1bd4](https://github.com/onegov/onegov-cloud/commit/d88a4f1bd4b242b297e6300fb26213d1412dbb5c)

### Landsgemeinde

##### Add title to vota

Add title before vota list

`Feature` | [OGC-3137](https://linear.app/onegovcloud/issue/OGC-3137) | [bea7352b0c](https://github.com/onegov/onegov-cloud/commit/bea7352b0c010c1232ffd184bf675d2fe18fd91b)

##### Hide vota in draft state

`Bugfix` | [OGC-3130](https://linear.app/onegovcloud/issue/OGC-3130) | [4135f35751](https://github.com/onegov/onegov-cloud/commit/4135f35751d99623119651f252c1881b87f65619)

### Org

##### Add internal comments feature.

`Feature` | [OGC-3154](https://linear.app/onegovcloud/issue/OGC-3154) | [9349222ce3](https://github.com/onegov/onegov-cloud/commit/9349222ce34bdcb65f0f3fc0d31914e7d1fc4c3f)

##### Strip leading/trailing whitespace from person name fields

Adds StripWhitespaceMixin to Person, Translator, Volunteer, and CourseAttendee so whitespaces get stripped on assignment.

`Feature` | [OGC-3142](https://linear.app/onegovcloud/issue/OGC-3142) | [9136d3b1e7](https://github.com/onegov/onegov-cloud/commit/9136d3b1e7900605dbf87e51eba8f86d4a3bb33f)

##### Fix reservation form crashing on expired session

Move remove_expired_reservation_sessions to run before bound_reservations so an expired session yields a clean 403 instead of potentially crashing when the template accesses attributes of a detached SQLAlchemy object.

`Bugfix` | [HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7432727459/ACTIVITY/](#HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7432727459/ACTIVITY/) | [1a9116d28c](https://github.com/onegov/onegov-cloud/commit/1a9116d28c791dc28556ff49d21d55984597ebb1)

##### Improvements to visual appearance internal comments.

`Bugfix` | [OGC-3164](https://linear.app/onegovcloud/issue/OGC-3164) | [235f291e87](https://github.com/onegov/onegov-cloud/commit/235f291e8749830cca6f8e8b2b13053eab17c7d8)

### Pdf

##### Fix mypy errors for pdfrw PdfReader import.

pdfrw now has type stubs, so import-untyped is no longer the correct
ignore code; use attr-defined since PdfReader is not exposed at the
package's top level in those stubs.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

`Other` | [1298f2e72c](https://github.com/onegov/onegov-cloud/commit/1298f2e72c4e896ce2fee7bf08ca6e1ea42a16c8)

### Town6

##### Fix scrollable when scrolling up

`Bugfix` | [OGC-3111](https://linear.app/onegovcloud/issue/OGC-3111) | [72a31fe12d](https://github.com/onegov/onegov-cloud/commit/72a31fe12d6b9ff495639914260be3e285448086)

## 6

`2026-06-15` | [4fb3e10c7a...38fc3243ac](https://github.com/OneGov/onegov-cloud/compare/4fb3e10c7a^...38fc3243ac)

## 5

`2026-06-12` | [d30045dd5d...debccc31d7](https://github.com/OneGov/onegov-cloud/compare/d30045dd5d^...debccc31d7)

## 4

`2026-06-08` | [bfbe5fd890...59fb46c43b](https://github.com/OneGov/onegov-cloud/compare/bfbe5fd890^...59fb46c43b)

### Core

##### Avoids `BrowserSession.pop` causing changes for non-existent keys

This also cleans up some old sharp corners in the API

`Bugfix` | [5d1ad99e55](https://github.com/onegov/onegov-cloud/commit/5d1ad99e5583327b556f595e426a59800e9c98a4)

### Org

##### Adds keywords (e.g. synonyms) to topics/pages. Keywords are also in the search index.

`Feature` | [OGC-3155](https://linear.app/onegovcloud/issue/OGC-3155) | [b718f04d1d](https://github.com/onegov/onegov-cloud/commit/b718f04d1d6239ae287030f68c3948190602335a)

### Pas

##### Don't show parliamentarian name in email.

`Bugfix` | [OGC-3202](https://linear.app/onegovcloud/issue/OGC-3202) | [eb9d4c8af7](https://github.com/onegov/onegov-cloud/commit/eb9d4c8af7b9211abf4f082dc10a60235e67b43f)

## 3

`2026-06-08` | [0e89ad461d...f728803369](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...f728803369)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

## 2026.31

`2026-06-05` | [bfbe5fd890...8da184cd73](https://github.com/OneGov/onegov-cloud/compare/bfbe5fd890^...8da184cd73)

### Core

##### Avoids `BrowserSession.pop` causing changes for non-existent keys

This also cleans up some old sharp corners in the API

`Bugfix` | [5d1ad99e55](https://github.com/onegov/onegov-cloud/commit/5d1ad99e5583327b556f595e426a59800e9c98a4)

### Org

##### Adds keywords (e.g. synonyms) to topics/pages. Keywords are also in the search index.

`Feature` | [OGC-3155](https://linear.app/onegovcloud/issue/OGC-3155) | [b718f04d1d](https://github.com/onegov/onegov-cloud/commit/b718f04d1d6239ae287030f68c3948190602335a)

### Pas

##### Don't show parliamentarian name in email.

`Bugfix` | [OGC-3202](https://linear.app/onegovcloud/issue/OGC-3202) | [eb9d4c8af7](https://github.com/onegov/onegov-cloud/commit/eb9d4c8af7b9211abf4f082dc10a60235e67b43f)

## 2

No changes since last release

## results

`2026-06-03` | [8b4fe610f6...10c72309d2](https://github.com/OneGov/onegov-cloud/compare/8b4fe610f6^...10c72309d2)

### Core

##### Replace N+1 has_table queries with single get_table_names on schema init

The fix fetches all existing table names in the schema with a single Inspector.get_table_names() call, then passes only the missing tables to create_all(..., checkfirst=False), reducing from O(n) to O(1)

`Performance` | [HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7357002739/](#HTTPS://SEANTIS-GMBH.SENTRY.IO/ISSUES/7357002739/) | [8b4fe610f6](https://github.com/onegov/onegov-cloud/commit/8b4fe610f6721407587f9b0c50fb71977071152e)

### Directory

##### Exclude all property names from the wtforms setattr loop

`Bugfix` | [OGC-3195](https://linear.app/onegovcloud/issue/OGC-3195) | [f23b9262a2](https://github.com/onegov/onegov-cloud/commit/f23b9262a2b1aee24d6685a72d268a3ce848759b)

##### Explicitly include coordinates property in wtforms setattr loop

`Bugfix` | [OGC-3195](https://linear.app/onegovcloud/issue/OGC-3195) | [a99ca6283e](https://github.com/onegov/onegov-cloud/commit/a99ca6283e74801b8196b258d709ede17df19d11)

### Onboarding

##### Fixes town assistant.

`Bugfix` | [OGC-2727](https://linear.app/onegovcloud/issue/OGC-2727) | [ec6fb0591b](https://github.com/onegov/onegov-cloud/commit/ec6fb0591bac676680a2c186076ee3aa565c22da)

### Org

##### Remove obsolete description from page form

`Feature` | [NONE](#NONE) | [a7186f9813](https://github.com/onegov/onegov-cloud/commit/a7186f981363c8fad3e25c9d7c47c460f7f52f3a)

##### Fixes event search index corrupted after fetch.

The fetch CLI switches schemas multiple times in a loop (remote → local
per source key), violating the session_manager's own design contract:
"we only set the schema once per request". Any ORM flush during the
schema-switch window would send indexing signals tagged with the wrong
schema.

Wrap `from_import()` and the submit/publish/ticket block in
`disable_change_signals()`, then explicitly index each added/updated
published event after signals are restored.

`Bugfix` | [OGC-3101](https://linear.app/onegovcloud/issue/OGC-3101) | [7c3b4503f1](https://github.com/onegov/onegov-cloud/commit/7c3b4503f12a51255088e6728fb547a03f71d647)

### Town6

##### Change label for all posts on homepage

This changes All articles to All posts

`Feature` | [OGC-3181](https://linear.app/onegovcloud/issue/OGC-3181) | [51023e9c40](https://github.com/onegov/onegov-cloud/commit/51023e9c40fec0ca65534a0052f414aea97a7060)

### Winterthur

##### Add iframe back button to directory entries and update it for events

`Feature` | [OGC-3176](https://linear.app/onegovcloud/issue/OGC-3176) | [23ce66cdfd](https://github.com/onegov/onegov-cloud/commit/23ce66cdfdd83533da9c893527abb0f5f8b4a151)

## results

`2026-06-01` | [0e89ad461d...2a3b57e288](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...2a3b57e288)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Core

##### Fix ruff F811 errors [skip-ci]

`Bugfix` | [NONE](#NONE) | [3225e9fca1](https://github.com/onegov/onegov-cloud/commit/3225e9fca18ff43858a886e20e1b5a5cc7accdcf)

### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

### Town

##### Sortable fix

The view now scrolls when dragging an item to the list edge.

`Feature` | [OGC-3111](https://linear.app/onegovcloud/issue/OGC-3111) | [cdf0b667e6](https://github.com/onegov/onegov-cloud/commit/cdf0b667e63a2288077901fe8ec818b56b569e08)

## pro

`2026-05-28` | [8473c039e7...939f12381f](https://github.com/OneGov/onegov-cloud/compare/8473c039e7^...939f12381f)

### Feriennet

##### Volunteer Ticket

Volunteer registrations now create a ticket. The states can be changed in the ticket and mails are sent for registration and finalization.

`Feature` | [PRO-1418](https://linear.app/projuventute/issue/PRO-1418) | [9bd8288850](https://github.com/onegov/onegov-cloud/commit/9bd8288850b9f4273dc47385412647f4f795302b)

## 2026.30

`2026-05-28` | [11fc058f63...11fc058f63](https://github.com/OneGov/onegov-cloud/compare/11fc058f63^...11fc058f63)

## 2026.29

`2026-05-28` | [d73849d377...7e3e5ef99d](https://github.com/OneGov/onegov-cloud/compare/d73849d377^...7e3e5ef99d)

### Core

##### Turns the browser session into a `transaction` data manager

This avoids aborted/retried transactions from emitting changes to the
browser session, which could result in success messages being displayed
after a failed transaction or similar weird edge-cases.

`Bugfix` | [OGC-3182](https://linear.app/onegovcloud/issue/OGC-3182) | [45e660da37](https://github.com/onegov/onegov-cloud/commit/45e660da3796474ae990d672b0404b006c9e3377)

##### Switch from requests to niquests

`Performance` | [OGC-3166](https://linear.app/onegovcloud/issue/OGC-3166) | [51245bbbae](https://github.com/onegov/onegov-cloud/commit/51245bbbaec2637d3adc647bfc5e645b122bb570)

### Feriennet

##### Add CLI to delete activities

`Feature` | [PRO-1489](https://linear.app/projuventute/issue/PRO-1489) | [48829840f9](https://github.com/onegov/onegov-cloud/commit/48829840f982e66c12475b4c176e0543b426cd2a)

### Pas

##### Show allowances in overview.

`Feature` | [OGC-3191](https://linear.app/onegovcloud/issue/OGC-3191) | [4bad880286](https://github.com/onegov/onegov-cloud/commit/4bad88028668f1e6544b3211812555a77bfc6433)

##### Restore abschluss guard for attendance creation.

Commit da2a45a99 accidentally removed the check that prevents adding
attendances after abschluss was set for a settlement run.

`Bugfix` | [OGC-3188](https://linear.app/onegovcloud/issue/OGC-3188) | [f3859c0706](https://github.com/onegov/onegov-cloud/commit/f3859c0706b6921d7afee31fdba693c4cc65225b)

##### Change email message content slightly as per feedback.

`Bugfix` | [OGC-3186](https://linear.app/onegovcloud/issue/OGC-3186) | [5dadd6d491](https://github.com/onegov/onegov-cloud/commit/5dadd6d491b41b123c911dac9d274ab650764b41)

##### Use `created` date in email.

`Bugfix` | [e5295183b6](https://github.com/onegov/onegov-cloud/commit/e5295183b6daab04e868e86c5659a08e08bf8dee)

### Reservation

##### Adds additional DB indexes to speed up some queries

This should help with cleanups on resources with a lot of allocations
on a very long time frame.

`Performance` | [OGC-3183](https://linear.app/onegovcloud/issue/OGC-3183) | [62a08f26a5](https://github.com/onegov/onegov-cloud/commit/62a08f26a5a2553da7bdefd9718629bce98c2d07)

### Search

##### Propagate errors while updating or deleting search index

Under high load (e.g. Feriennet opening days) concurrent bookings can trigger PostgreSQL serialization failures inside the search indexer's savepoint. Previously these were silently swallowed, leaving the outer transaction dead (booking lost) while the confirmation email was still dispatched.

`Bugfix` | [PRO-1545](https://linear.app/projuventute/issue/PRO-1545) | [edf9a3830f](https://github.com/onegov/onegov-cloud/commit/edf9a3830f31b46e2b1ab4370622458ad4d717d7)

### Swissvotes

##### New Design

New design for the page.

`Feature` | [SWI-62](https://linear.app/swissvotes/issue/SWI-62) | [f5646554d5](https://github.com/onegov/onegov-cloud/commit/f5646554d57f14cd02a760504c0b7a7195c508a3)

## 2026.28

`2026-05-22` | [18c0a5a741...3de3c91a7d](https://github.com/OneGov/onegov-cloud/compare/18c0a5a741^...3de3c91a7d)

### Org

##### Tag name

Fix view of tag names

`Bugfix` | [OGC-3083](https://linear.app/onegovcloud/issue/OGC-3083) | [18c0a5a741](https://github.com/onegov/onegov-cloud/commit/18c0a5a7418b2fbf9773fc78d8a1d30a8ea4d208)

##### Fix migrate links tool

Use re.subn to count URL occurrences per field (not just whether a field changed), and wrap the
substituted value in Markup when the original was Markup to prevent double-escaping HTML
entities.

`Bugfix` | [OGC-3003](https://linear.app/onegovcloud/issue/OGC-3003) | [c9f046568a](https://github.com/onegov/onegov-cloud/commit/c9f046568adb2d791f8dd3b38a821792a9478989)

### Pas

##### Restrict attendance forms to active members.

Bulk-add and edit forms previously showed all active parliamentarians
regardless of Kantonsrat membership. Now filters using org_type metadata
set by the KUB importer, ensuring inactive members do not appear.

`Bugfix` | [OGC-2949](https://linear.app/onegovcloud/issue/OGC-2949) | [38c4e9b04c](https://github.com/onegov/onegov-cloud/commit/38c4e9b04ce29d804a7923694c2f5c74aee919c2)

### Swi

##### Ignore empty policy area

`Bugfix` | [SWI-63](https://linear.app/swissvotes/issue/SWI-63) | [bd370d252e](https://github.com/onegov/onegov-cloud/commit/bd370d252ef6e1ad240ad4f6152206c1b777b19e)

## pro

`2026-05-21` | [2afeb1b9eb...2afeb1b9eb](https://github.com/OneGov/onegov-cloud/compare/2afeb1b9eb^...2afeb1b9eb)

## pro2

`2026-05-21` | [8473c039e7...d8fa70b4e2](https://github.com/OneGov/onegov-cloud/compare/8473c039e7^...d8fa70b4e2)

### Core

##### Allows tenant-specific email senders to be configured

`Feature` | [OGC-3078](https://linear.app/onegovcloud/issue/OGC-3078) | [1376192f24](https://github.com/onegov/onegov-cloud/commit/1376192f2494cbe775440f13d6d12efcfe0dcba7)

##### Moves `sentry_tween_factory` over `transaction_tween_factory`

This way retries on retryable transaction errors properly show up as
one transaction, instead of separate transactions for each try.

`Bugfix` | [ONEGOV-CLOUD-5FN](https://seantis-gmbh.sentry.io/issues/?query=ONEGOV-CLOUD-5FN) | [fff59eb635](https://github.com/onegov/onegov-cloud/commit/fff59eb6354514784f67ab51d7c79bd1b8530582)

### Feriennet

##### Volunteer Ticket

Volunteer registrations now create a ticket. The states can be changed in the ticket and mails are sent for registration and finalization.

`Feature` | [PRO-1418](https://linear.app/projuventute/issue/PRO-1418) | [9bd8288850](https://github.com/onegov/onegov-cloud/commit/9bd8288850b9f4273dc47385412647f4f795302b)

### Landsgemeinde

##### Adds tests to cover all state changes

`Feature` | [OGC-3129](https://linear.app/onegovcloud/issue/OGC-3129) | [ade1a797f8](https://github.com/onegov/onegov-cloud/commit/ade1a797f850811f568cde4901f91e4c3b18e305)

### Org

##### Uses plain search when searching terms returned by suggestions

`Bugfix` | [OGC-3029](https://linear.app/onegovcloud/issue/OGC-3029) | [b9d7678891](https://github.com/onegov/onegov-cloud/commit/b9d76788919406c69fcb7d71672f0521165d74bf)

### Pay

##### Sorts invoice items by their creation date for a more stable order

`Feature` | [OGC-3127](https://linear.app/onegovcloud/issue/OGC-3127) | [e10f0f83a2](https://github.com/onegov/onegov-cloud/commit/e10f0f83a289cebb74d3f148a383ba485d0bf174)

## 2026.27

`2026-05-15` | [51a224b031...307026ef4b](https://github.com/OneGov/onegov-cloud/compare/51a224b031^...307026ef4b)

### Activity

##### Adds additional indexes to speed up activity filters

`Performance` | [b2163c497a](https://github.com/onegov/onegov-cloud/commit/b2163c497a4bd0c8443475e6705fcc184d787595)

### Event

##### Adds additional indexes to speed up some occurrence filters

`Performance` | [4997ade328](https://github.com/onegov/onegov-cloud/commit/4997ade328542c9c84b5e97408e9f589b7e228d9)

### Feriennet

##### Volunteer Ticket

Volunteer registrations now create a ticket. The states can be changed in the ticket and mails are sent for registration and finalization.

`Feature` | [PRO-1418](https://linear.app/projuventute/issue/PRO-1418) | [5f247e5a49](https://github.com/onegov/onegov-cloud/commit/5f247e5a491640f7a936682f74a43d5852c5012d)

### Landsgemeinde

##### Sort vota within agenda item after vota.number

`Bugfix` | [OGC-3132](https://linear.app/onegovcloud/issue/OGC-3132) | [8c22b49459](https://github.com/onegov/onegov-cloud/commit/8c22b49459ac731b7c986f7b1f066aa30ccd92f7)

### Newsletter

##### Default daily newsletter checkbox is now set by default

`Feature` | [OGC-3027](https://linear.app/onegovcloud/issue/OGC-3027) | [920594cc77](https://github.com/onegov/onegov-cloud/commit/920594cc77b3074b503a97a46f5474bdae56936c)

### Org

##### Adds API endpoints for forms, resources, people and RIS

Co-authored-by: Christof Weickhardt <christof.weickhardt@seantis.ch>

`Feature` | [OGC-2905](https://linear.app/onegovcloud/issue/OGC-2905) | [f604f0c12c](https://github.com/onegov/onegov-cloud/commit/f604f0c12c4ed137e209810ed153536af7267c96)

##### Fix typos in user texts

`Bugfix` | [NONE](#NONE) | [51a224b031](https://github.com/onegov/onegov-cloud/commit/51a224b0316409ba7245def0612ab79726ec04e1)

##### Adds fallback mimetype for audio files

`Bugfix` | [OGC-3061](https://linear.app/onegovcloud/issue/OGC-3061) | [818ecf1443](https://github.com/onegov/onegov-cloud/commit/818ecf1443d9c8a80076e882cc8a5011f14b7369)

### Pas

##### Emit warning message if no user -> parliamentarian account.

`Feature` | [3a42f23e20](https://github.com/onegov/onegov-cloud/commit/3a42f23e20f122a7fedb8e7b7389ff8df0a765e1)

##### Parliamentarians see subset of commissions they are part of.

`Feature` | [03a3b42189](https://github.com/onegov/onegov-cloud/commit/03a3b421890e3840cccec78457ca41aecca61f8b)

##### Add bulk ZIP download for all parliamentarian PDFs

Adds a "All Parliamentarians (ZIP)" link to the settlement run
export page, allowing all individual parliamentarian settlement
PDFs to be downloaded in a single ZIP file.

`Feature` | [ed1682cd1c](https://github.com/onegov/onegov-cloud/commit/ed1682cd1c71cbf6beedb92e5cee17334ccd4eb9)

##### Use commission name in Abschluss email subject

When closing a commission, the notification email subject showed
the parliamentarian's name instead of the commission name.

`Bugfix` | [492c4a2657](https://github.com/onegov/onegov-cloud/commit/492c4a2657e309833eae2b2d36cde78cc53d10eb)

##### Fix date position in letter.

`Bugfix` | [67ff5b4ecc](https://github.com/onegov/onegov-cloud/commit/67ff5b4eccfca475d9d34fc21fad45b47a206bbe)

### Pay

##### Adds additional indexes to payments and invoices for faster queries

`Performance` | [8080142231](https://github.com/onegov/onegov-cloud/commit/80801422314e627e85f74b475595a9747a0dff2d)

### Search

##### Adds `--skip-ok` flag to `onegov-search index-status`

This allows for a more compact view of problematic schemas/tables

`Feature` | [b907b27dcc](https://github.com/onegov/onegov-cloud/commit/b907b27dccc558a2cb2d245380159e2f40d95e76)

## results

`2026-05-08` | [0e89ad461d...5ba6afa9a0](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...5ba6afa9a0)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

## 2026.26

`2026-05-08` | [be2e918e51...df0fd2840e](https://github.com/OneGov/onegov-cloud/compare/be2e918e51^...df0fd2840e)

### Agency

##### Fix display bug of people cards in safari

`Bugfix` | [OGC-3109](https://linear.app/onegovcloud/issue/OGC-3109) | [107321312a](https://github.com/onegov/onegov-cloud/commit/107321312afed644358a181721ddb2dc7b80a941)

### Event

##### Makes an upgrade task more robust.

In certain edge cases `values` can be None.

`Bugfix` | [1c20dcece2](https://github.com/onegov/onegov-cloud/commit/1c20dcece2d1622f03df20a03b8efa1a851df0a0)

### Fsi

##### Auto send email if state changed.

`Feature` | [OGC-3136](https://linear.app/onegovcloud/issue/OGC-3136) | [23674f9cf3](https://github.com/onegov/onegov-cloud/commit/23674f9cf32aca2413ceb68abb26a01290cf56a0)

### Landsgemeinde

##### Moves vota above text in agenda item view.

`Feature` | [OGC-3133](https://linear.app/onegovcloud/issue/OGC-3133) | [42efb8e4e2](https://github.com/onegov/onegov-cloud/commit/42efb8e4e23b1b9ef2c5e678d8e558f832b12ffd)

##### Propagate draft state only downwards.

`Bugfix` | [OGC-3129](https://linear.app/onegovcloud/issue/OGC-3129) | [9a6fbc3e23](https://github.com/onegov/onegov-cloud/commit/9a6fbc3e234e6bbf60d8e7089a173c31bc3b3cd1)

### Org

##### Allow links creation directly on root level (as for pages)

The workaround was to create it on any level and move it to the root level.

`Feature` | [OGC-3118](https://linear.app/onegovcloud/issue/OGC-3118) | [33bba4d45a](https://github.com/onegov/onegov-cloud/commit/33bba4d45a2b5e8e239ff66b1e38408faac8e904)

##### Fetch command option to include imported events

`Feature` | [OGC-3140](https://linear.app/onegovcloud/issue/OGC-3140) | [1e92524250](https://github.com/onegov/onegov-cloud/commit/1e92524250e7f60cc9bea3c260541ae385411006)

##### Fixes crash in reservation acceptance PDF when submission has no renderable fields

`Bugfix` | [OGC-3138](https://linear.app/onegovcloud/issue/OGC-3138) | [5086ef771a](https://github.com/onegov/onegov-cloud/commit/5086ef771a36f6ed77117db431d8b0f5f85a50a1)

### Pas

##### Map with zg_username.

`Feature` | [OGC-3112](https://linear.app/onegovcloud/issue/OGC-3112) | [43c7d2eff9](https://github.com/onegov/onegov-cloud/commit/43c7d2eff9d65a9b70b47927d6c4c0927336d2db)

##### Adds sync user account cli.

`Feature` | [d4313d1a42](https://github.com/onegov/onegov-cloud/commit/d4313d1a428f812749d5d4fbef8e8d260273e62f)

##### Removed add/edit/delete views.

No reason to allow manual editing, as it introduces
unnecessary risk and potential abuse.

`Feature` | [OGC-3149](https://linear.app/onegovcloud/issue/OGC-3149) | [4d3325255f](https://github.com/onegov/onegov-cloud/commit/4d3325255ff7b0604dfd7d8d11c6a45445723935)

##### Fixes Vice president not being detected.

`Bugfix` | [OGC-3116](https://linear.app/onegovcloud/issue/OGC-3116) | [be2e918e51](https://github.com/onegov/onegov-cloud/commit/be2e918e518512942b358e676409d76788ecbaa4)

##### Corrects wrong LiteralType

`Bugfix` | [6321d54a86](https://github.com/onegov/onegov-cloud/commit/6321d54a862170bf35ab17b6de8cabf79506b5e3)

##### Persist org_type on ParliamentarianRole via meta column.

The KUB importer knows whether a role belongs to Kantonsrat,
(via organizationTypeTitle), but this information was
discarded after import. Detecting Kantonsrat membership required a
fragile heuristic checking three columns for NULL.
Kantonsrat membership meaning being active in parliament itself, so 
it's a special kind of `ParliamentarianRole`.

`Bugfix` | [OGC-3143](https://linear.app/onegovcloud/issue/OGC-3143) | [d34177d12c](https://github.com/onegov/onegov-cloud/commit/d34177d12cd18079b9558a911f212a6d90a22e62)

##### Fix commission membership import losing role transitions.

The import key (parliamentarian_id, commission_id) allowed only one
membership per person per commission. When a person transitioned roles
(e.g. Mitglied → Präsident), the second entry overwrote the first.

`Bugfix` | [OGC-3156](https://linear.app/onegovcloud/issue/OGC-3156) | [c98acf65d8](https://github.com/onegov/onegov-cloud/commit/c98acf65d8a59ce3763e194e765d40f4a217e37b)

##### Add back the commission president view that was removed.

`Bugfix` | [f19ecab47b](https://github.com/onegov/onegov-cloud/commit/f19ecab47b0dc9360501b10470eb122f69ebc018)

### Town6

##### Fixes time display in occurrences.

`Feature` | [OGC-3144](https://linear.app/onegovcloud/issue/OGC-3144) | [ad7ce9f65e](https://github.com/onegov/onegov-cloud/commit/ad7ce9f65e5a72296913e44752d3c37dbf639bf3)

### Winterthur

##### Fixes inline search.

Hotfix for:
sqlalchemy.exc.ProgrammingError:
(psycopg2.ProgrammingError) can't adapt type 'property'

`Bugfix` | [OGC-3119](https://linear.app/onegovcloud/issue/OGC-3119) | [8be97af686](https://github.com/onegov/onegov-cloud/commit/8be97af68678d38d84b588ecdde62f756f842517)

## 3

`2026-05-07` | [672d745358...c2a7ca8cb0](https://github.com/OneGov/onegov-cloud/compare/672d745358^...c2a7ca8cb0)

## 2

`2026-05-06` | [c822395c1c...390789af02](https://github.com/OneGov/onegov-cloud/compare/c822395c1c^...390789af02)

## results

`2026-05-04` | [0e89ad461d...17c021f8f0](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...17c021f8f0)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

## 2026.25

`2026-04-29` | [9e5c99c325...047fbbe0d7](https://github.com/OneGov/onegov-cloud/compare/9e5c99c325^...047fbbe0d7)

### Agency

##### Fix display bug of people cards in safari

`Bugfix` | [OGC-3109](https://linear.app/onegovcloud/issue/OGC-3109) | [107321312a](https://github.com/onegov/onegov-cloud/commit/107321312afed644358a181721ddb2dc7b80a941)

### Event

##### Makes an upgrade task more robust.

In certain edge cases `values` can be None.

`Bugfix` | [1c20dcece2](https://github.com/onegov/onegov-cloud/commit/1c20dcece2d1622f03df20a03b8efa1a851df0a0)

### Org

##### Fixes AI formcoder bug (incorrect POST url).

JS sent to `/resources/new-room/formcoder`, but the view is
registered on `FormCollection`. The endpoint is always at
`/forms/formcoder`.

`Bugfix` | [OGC-3081](https://linear.app/onegovcloud/issue/OGC-3081) | [9e5c99c325](https://github.com/onegov/onegov-cloud/commit/9e5c99c3251fcb9c060a033a23de55db85639309)

##### Add missing translation for "Edit Event Filter Configuration".

`Bugfix` | [OGC-3052](https://linear.app/onegovcloud/issue/OGC-3052) | [f18cd03430](https://github.com/onegov/onegov-cloud/commit/f18cd0343055a2f932ed0c31df6675632229258a)

### Pas

##### Adds filter for import logs by user.

`Feature` | [2b3a6dfabc](https://github.com/onegov/onegov-cloud/commit/2b3a6dfabc0c45935267e9fde7d5b3700d59f4f0)

##### Map with zg_username.

`Feature` | [OGC-3112](https://linear.app/onegovcloud/issue/OGC-3112) | [43c7d2eff9](https://github.com/onegov/onegov-cloud/commit/43c7d2eff9d65a9b70b47927d6c4c0927336d2db)

##### Fixes Vice president not being detected.

`Bugfix` | [OGC-3116](https://linear.app/onegovcloud/issue/OGC-3116) | [be2e918e51](https://github.com/onegov/onegov-cloud/commit/be2e918e518512942b358e676409d76788ecbaa4)

##### Corrects wrong LiteralType

`Bugfix` | [6321d54a86](https://github.com/onegov/onegov-cloud/commit/6321d54a862170bf35ab17b6de8cabf79506b5e3)

### Winterthur

##### Fixes inline search.

Hotfix for:
sqlalchemy.exc.ProgrammingError:
(psycopg2.ProgrammingError) can't adapt type 'property'

`Bugfix` | [OGC-3119](https://linear.app/onegovcloud/issue/OGC-3119) | [8be97af686](https://github.com/onegov/onegov-cloud/commit/8be97af68678d38d84b588ecdde62f756f842517)

## 2026.24

`2026-04-24` | [5482237bcd...63ac7fac26](https://github.com/OneGov/onegov-cloud/compare/5482237bcd^...63ac7fac26)

### Api

##### New filters.

Includes also OGC-3085 which is similar.

`Feature` | [OGC-3086](https://linear.app/onegovcloud/issue/OGC-3086) | [7be5be95d6](https://github.com/onegov/onegov-cloud/commit/7be5be95d66ad56cc667e8bbbc9811a7c95fabf6)

### Feriennet

##### Fix bug where hidden needs are displayed

`Bugfix` | [PRO-1530](https://linear.app/projuventute/issue/PRO-1530) | [5482237bcd](https://github.com/onegov/onegov-cloud/commit/5482237bcd942170bd6a495e4b24b6e93346d8b0)

##### Add translations for group code

`Bugfix` | [PRO-931](https://linear.app/projuventute/issue/PRO-931) | [eeee14f0ef](https://github.com/onegov/onegov-cloud/commit/eeee14f0efe716b8089d84677ad8fc1b120fd1d8)

### Pas

##### Add missing filter for plenary session.

`Bugfix` | [70af86f00d](https://github.com/onegov/onegov-cloud/commit/70af86f00dc43aacb3db061892be2ca156fae95b)

##### Show `zg_username` on parliamentarian.

`Bugfix` | [b32b7fd8c6](https://github.com/onegov/onegov-cloud/commit/b32b7fd8c6e806c7f6b4f8355068c8a87b292d51)

## swi

`2026-04-23` | [b2808d3bc1...aa61b72930](https://github.com/OneGov/onegov-cloud/compare/b2808d3bc1^...aa61b72930)

## 2026.23

`2026-04-23` | [415f877415...ef4ba26201](https://github.com/OneGov/onegov-cloud/compare/415f877415^...ef4ba26201)

### Api

##### Adds a full-text search filter to each Api endpoint in Org

`Feature` | [OGC-3088](https://linear.app/onegovcloud/issue/OGC-3088) | [89afa6e0ab](https://github.com/onegov/onegov-cloud/commit/89afa6e0ab26a21b610a993cf194dcf6821e455a)

### Form

##### Fixes some bugs in the formcode indentation checker logic

`Bugfix` | [OGC-3110](https://linear.app/onegovcloud/issue/OGC-3110) | [5e96c08c79](https://github.com/onegov/onegov-cloud/commit/5e96c08c7996525f7e14580abdf655a5b26052f9)

### Org

##### Includes additional ticket information in reservations summary PDF

This additional information is only included when the context is a
single ticket, rather than a time-bounded stream of reservations.

`Feature` | [OGC-3095](https://linear.app/onegovcloud/issue/OGC-3095) | [415f877415](https://github.com/onegov/onegov-cloud/commit/415f877415bdebdf8ac06ea01eca97c27714c317)

##### Improves performance of keyword filter counts in events/directories

`Performance` | [OGC-1823](https://linear.app/onegovcloud/issue/OGC-1823) | [4383caffa3](https://github.com/onegov/onegov-cloud/commit/4383caffa3cdbc1cb4bc67e2ff4c0f97e5437f75)

### Pas

##### Store zg username field.

`Feature` | [OGC-2951](https://linear.app/onegovcloud/issue/OGC-2951) | [cca2483842](https://github.com/onegov/onegov-cloud/commit/cca24838422179337e3084b3e2a4e8ddb19e0be4)

##### Updates Allowances and various improvements.

- Admin-only attendance editing enforced, permission tests updated
  - Attendance pagination, filters, edit link fixes, bulk-add UI improvements
  - Settlement run filter added
  - 2 allowances bugs fixed, presidential allowance form/model reworked
  - Single parliamentarian export now includes allowances
  - Removed "amtliche Mission" commission type
  - Removed manual JSON import view
  - Email: PAS-specific template (Outlook logo fix), left-aligned logo/footer, admin emails only to active admins
  - DB index added for frequently used queries
  - Translations updated, invalid tests removed, misc error fixes

`Bugfix` | [OGC-2951](https://linear.app/onegovcloud/issue/OGC-2951) | [4d2299faa2](https://github.com/onegov/onegov-cloud/commit/4d2299faa288345c273042eaaa016e7af1299f4a)

## swi

`2026-04-21` | [b2808d3bc1...726a35e0e4](https://github.com/OneGov/onegov-cloud/compare/b2808d3bc1^...726a35e0e4)

### Feriennet

##### Add content disposition attribute

Add content disposition attribute so json can be an attachment instead of being shown directly in the browser.

`Bugfix` | [PRO-1525](https://linear.app/projuventute/issue/PRO-1525) | [383ec48e61](https://github.com/onegov/onegov-cloud/commit/383ec48e61bacdb85ee5ac10bfa541cb8f62ae4f)

### Org

##### Rearrange settings and management bar

- Added a link for User manual
- Added a new category "modules" to the global tools
- Rearranged the global tools and settings
- Added categories to settings

`Feature` | [a245aa0a42](https://github.com/onegov/onegov-cloud/commit/a245aa0a42cbe9a16ff7482bc2d425c0aa8e0f3d)

##### Enables the OneGov Api in Org apps as well, not just Town6 apps

`Feature` | [OGC-3091](https://linear.app/onegovcloud/issue/OGC-3091) | [86c800c6d5](https://github.com/onegov/onegov-cloud/commit/86c800c6d5386c536e44a12b1b7c3a2a62dbcae2)

##### Allow handlers to control ticket reopen decisions.

`Bugfix` | [254c81f313](https://github.com/onegov/onegov-cloud/commit/254c81f31316afc34c959567e4ada7cd8310c57e)

##### Fix problem with selecting additional dates

`Bugfix` | [OGC-3070](https://linear.app/onegovcloud/issue/OGC-3070) | [41759f21bb](https://github.com/onegov/onegov-cloud/commit/41759f21bb212ea9b57257f370144705861ed469)

##### Fixes a logic bug in holidays.

Erroneous superset operator was never true for all practical purposes. The
condition `self._cantons > {'TI', 'VS'}` checked whether the configured cantons
formed a strict superset of the exclusion set, meaning it only evaluated to
True when both TI and VS plus at least one additional canton were present.
Since most instances are configured with a single canton, Good Friday and
Easter Monday were silently skipped for virtually all users.

`Bugfix` | [OGC-3106](https://linear.app/onegovcloud/issue/OGC-3106) | [1bf879d3f4](https://github.com/onegov/onegov-cloud/commit/1bf879d3f47333ecfe33764663979bd3c8d29d06)

##### Add translations for "Appendix"

`Bugfix` | [OGC-3092](https://linear.app/onegovcloud/issue/OGC-3092) | [90c3880a09](https://github.com/onegov/onegov-cloud/commit/90c3880a0944b398554c635e611f479ead04b8dd)

### Pas

##### Bulk operations should only be edited as such.

- Enforce bulk/single edit separation
- Fix PDF spacing in address

`Feature` | [OGC-2951](https://linear.app/onegovcloud/issue/OGC-2951) | [31f7bad4ff](https://github.com/onegov/onegov-cloud/commit/31f7bad4ff79d4a43f31d0ba27c6fd7e38112a19)

### Ris

##### Properly filters inactive members in commissions

This also adds filter options to the view and displays the date range
of each membership in the list.

`Bugfix` | [OGC-3108](https://linear.app/onegovcloud/issue/OGC-3108) | [1e5855c213](https://github.com/onegov/onegov-cloud/commit/1e5855c213224863a883c0af6d60b45f1be241df)

### Tests

##### Switches browser tests from Selenium to Playwright

`Feature` | [OGC-3100](https://linear.app/onegovcloud/issue/OGC-3100) | [f81f59c607](https://github.com/onegov/onegov-cloud/commit/f81f59c607536811d6aba6165f5f7f3115a3b803)

##### Increases robustness of playwright browser tests

This slightly increases the default timeout and re-runs tests that
failed due to a timeout. It also ignore all CMP related console messages
not just the ones at the `WARNING` level for the Feriennet test.

`Bugfix` | [5de85d02dd](https://github.com/onegov/onegov-cloud/commit/5de85d02ddcba368261af458f0017fa500f7f3d8)

### Town6

##### Makes possible values for API query filters machine readable

This also fixes built-in event tags being reported in English instead
of the configured language within the event API.

`Feature` | [OGC-3087](https://linear.app/onegovcloud/issue/OGC-3087) | [a9c22bc940](https://github.com/onegov/onegov-cloud/commit/a9c22bc9403f2a3b76edf20e443ff0e9924d47a1)

## 2026.22

`2026-04-10` | [44e9a3b7d0...9a453a7c5d](https://github.com/OneGov/onegov-cloud/compare/44e9a3b7d0^...9a453a7c5d)

## 2026.21

`2026-04-10` | [cc33ac41df...cc33ac41df](https://github.com/OneGov/onegov-cloud/compare/cc33ac41df^...cc33ac41df)

## 2026.20

No changes since last release

## 2026.19

`2026-04-10` | [1a8da1014a...32712ed32a](https://github.com/OneGov/onegov-cloud/compare/1a8da1014a^...32712ed32a)

### Core

##### Avoids a potential race condition for messages tied to a session

`Bugfix` | [ONEGOV-CLOUD-5DM](https://seantis-gmbh.sentry.io/issues/?query=ONEGOV-CLOUD-5DM) | [0f65411221](https://github.com/onegov/onegov-cloud/commit/0f654112219f10d9cdccc5ee13328112eeaeda3f)

### Feriennet

##### Update homepage structure for new instances

`Feature` | [1a8da1014a](https://github.com/onegov/onegov-cloud/commit/1a8da1014a39e64b5f59e31f730aed1504b990bf)

##### Make group code optional

Create option to activate and deactivate group codes in the period form

`Feature` | [PRO-931](https://linear.app/projuventute/issue/PRO-931) | [a24cbd1d52](https://github.com/onegov/onegov-cloud/commit/a24cbd1d529f0baa758f3f4b6e53a4fdbee4825b)

##### Volunteers as recipients

Add volunteers with different states as options for message recipients

`Feature` | [PRO-1421](https://linear.app/projuventute/issue/PRO-1421) | [9226adf192](https://github.com/onegov/onegov-cloud/commit/9226adf192e86e0d2f02d2cb1e01e64945266524)

##### Fixes potential crash in personal attendee views

This also makes the `Personal` access restriction on `Attendee` more
robust by baking it into the security rules.

`Bugfix` | [ONEGOV-CLOUD-5DN](https://seantis-gmbh.sentry.io/issues/?query=ONEGOV-CLOUD-5DN) | [0a198f0d52](https://github.com/onegov/onegov-cloud/commit/0a198f0d5281d400f1254877309ea7ef1f050e82)

### Org

##### Adds an optional parent resource to reservation resources

Parent resources will be blocked by children and vice versa, but the
children don't block each other.

`Feature` | [OGC-2580](https://linear.app/onegovcloud/issue/OGC-2580) | [ea165dbeae](https://github.com/onegov/onegov-cloud/commit/ea165dbeae1af7d3f702eddaecb6b234e612ec24)

##### Improves robustness of `reject` view for reservations

Previously it was possible to accidentally reject all reservations if
a link was clicked multiple times or the ticket was opened in multiple
tabs.

`Bugfix` | [OGC-3072](https://linear.app/onegovcloud/issue/OGC-3072) | [d1fdb2ca8f](https://github.com/onegov/onegov-cloud/commit/d1fdb2ca8ff9806ba15941a2e5c559049267d744)

##### Fixes copy paste on views that make use of `NewsCollection`

`Bugfix` | [ONEGOV-CLOUD-482](https://seantis-gmbh.sentry.io/issues/?query=ONEGOV-CLOUD-482) | [916f5bec09](https://github.com/onegov/onegov-cloud/commit/916f5bec09c90abf8f497a27256b3bc2d36656f4)

### Pas

##### Refactor `hourly_user_account_sync` to run directly after import.

`Feature` | [66696474ab](https://github.com/onegov/onegov-cloud/commit/66696474aba458a8a43963a5388ddd663bad9392)

##### Make import more resilient if 0 records fetched.

`Bugfix` | [7650a01981](https://github.com/onegov/onegov-cloud/commit/7650a0198179423809fd11ccc980440fa1f40f37)

### Town6

##### Fixes rendering of person organisations in search results

`Bugfix` | [OGC-3074](https://linear.app/onegovcloud/issue/OGC-3074) | [dee62b0f5f](https://github.com/onegov/onegov-cloud/commit/dee62b0f5f21f26b7a10660465d30f70d8c806e4)

### Translator Direcory

##### `operation_comments` is now member visible.

`Feature` | [OGC-3065](https://linear.app/onegovcloud/issue/OGC-3065) | [1da4c06a3c](https://github.com/onegov/onegov-cloud/commit/1da4c06a3cbdc0b8ca747ad9911e21611f82c36c)

##### Adds a view test for `operation_comments`.

`Feature` | [OGC-3065](https://linear.app/onegovcloud/issue/OGC-3065) | [0dac70f4c5](https://github.com/onegov/onegov-cloud/commit/0dac70f4c5a8b84f76c2e143390e348abfbf22e0)

## swi

`2026-03-30` | [b2808d3bc1...59f3a504ba](https://github.com/OneGov/onegov-cloud/compare/b2808d3bc1^...59f3a504ba)

## 2026.18

`2026-03-27` | [4a8cf6ef55...72b3b75960](https://github.com/OneGov/onegov-cloud/compare/4a8cf6ef55^...72b3b75960)

### Core

##### Extend json directive adding CORS header for GET and HEAD requests

`Feature` | [OGC-2988](https://linear.app/onegovcloud/issue/OGC-2988) | [fb30809189](https://github.com/onegov/onegov-cloud/commit/fb308091891cbe22ae4e73bf84ce2c75ada9eb1e)

### Org

##### Fix href rendering False when use_links is falsy in occurrence list macro (event ticket)

This ensures the template doesn’t output href="False"

`Bugfix` | [NONE](#NONE) | [4a8cf6ef55](https://github.com/onegov/onegov-cloud/commit/4a8cf6ef551d41705541ded7b9f06df47b089696)

## ech0252

`2026-03-26` | [0e89ad461d...423d93f6a6](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...423d93f6a6)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

### Org

##### Adds missing `connect-src` for the Plausible analytics provider

`Bugfix` | [OGC-3067](https://linear.app/onegovcloud/issue/OGC-3067) | [165b8b17d3](https://github.com/onegov/onegov-cloud/commit/165b8b17d3f3a09d27c00e92493a213a135f63e3)

### Pas

##### Use cert in requests.

`Feature` | [OGC-2087](https://linear.app/onegovcloud/issue/OGC-2087) | [03edb4cd38](https://github.com/onegov/onegov-cloud/commit/03edb4cd38e4b40bcfc4a397f52c2375572ed6af)

##### Use an unified dropdown for allowances.

`Bugifx` | [fafafdfa75](https://github.com/onegov/onegov-cloud/commit/fafafdfa75b1f7c50eb2fe2558a2a4df8b94cfaa)

## 2026.17

`2026-03-26` | [4cdba419d4...14012932b0](https://github.com/OneGov/onegov-cloud/compare/4cdba419d4^...14012932b0)

### Agency

##### Eagerly load parent property for API calls, fixing n+1 query issue

`Feature` | [NONE](#NONE) | [7120cda5e0](https://github.com/onegov/onegov-cloud/commit/7120cda5e0be5623a5e4d72d416067a13b4183bc)

### Core

##### Makes `do/translate` compatible with Python 3.14

This also involved updating to Lingua 4.16.2, which meant we
had to slightly change our code in some places, so `pot-create`
doesn't crash and correctly picks up all the translation strings.



Co-authored-by: David Salvisberg <david.salvisberg@seantis.ch>

`Bugfix` | [OGC-3063](https://linear.app/onegovcloud/issue/OGC-3063) | [d79d07a156](https://github.com/onegov/onegov-cloud/commit/d79d07a156cb0aa90060c44f352e0d1fd5ff0f76)

### Event

##### Adds created column to event export data

`Feature` | [OGC-2992](https://linear.app/onegovcloud/issue/OGC-2992) | [2ecd43949a](https://github.com/onegov/onegov-cloud/commit/2ecd43949a8a83a3a80a1598a631c3d78512d945)

### Feriennet

##### New recipient group

Add two new recipient groups:
-  Organisers without occasions
-  Users with attendees that have no wishes or bookings

`Feature` | [PRO-1448](https://linear.app/projuventute/issue/PRO-1448) | [2a84801580](https://github.com/onegov/onegov-cloud/commit/2a84801580476237cc4fdd4d6014f3b2aaf4a7bb)

### Form

##### Raise error for nested field set definitions (as they are currently not supported)

`Feature` | [OGC-3033](https://linear.app/onegovcloud/issue/OGC-3033) | [defee57c92](https://github.com/onegov/onegov-cloud/commit/defee57c9278dbd50e09010aef4f6007c70cedf3)

### Landsgemeinde

##### Adds breadcrumbs to search results

`Feature` | [OGC-2880](https://linear.app/onegovcloud/issue/OGC-2880) | [4cdba419d4](https://github.com/onegov/onegov-cloud/commit/4cdba419d4d4566892d0251eaf1dca7ae1f220c2)

### Org

##### Fixes potential `KeyError` scenarios related to Kaba configuration

`Bugfix` | [4514a09db0](https://github.com/onegov/onegov-cloud/commit/4514a09db0093b5e72d32f996cbe92cf0c3b172d)

##### Fixes a rare edge-case in auto-accepting reservation tickets

`Bugfix` | [892ce12d82](https://github.com/onegov/onegov-cloud/commit/892ce12d824da9161def7644f02cf5502a42b669)

##### Fixes crash in tickets views for invalid owner filter

`Bugfix` | [4a3efcc072](https://github.com/onegov/onegov-cloud/commit/4a3efcc0721cb8ce975635e192ee15335b7e291b)

### Pas

##### SAML2 login for parliamentarians.

`Feature` | [OGC-2725](https://linear.app/onegovcloud/issue/OGC-2725) | [a6288c0b68](https://github.com/onegov/onegov-cloud/commit/a6288c0b6825e97ff522db838fb7ae3a7731302e)

##### Add allowances.

`Feature` | [OGC-2950](https://linear.app/onegovcloud/issue/OGC-2950) | [c5e2589e74](https://github.com/onegov/onegov-cloud/commit/c5e2589e741d626e1de2e3708aec9646de06b585)

##### Export pdf improvements, add logo and change margin.

`Bugfix` | [OGC-2949](https://linear.app/onegovcloud/issue/OGC-2949) | [de747b62ff](https://github.com/onegov/onegov-cloud/commit/de747b62ffdc10d2c5e4a295650627a711a55d76)

##### Simplify KUB config lookup, silently skip if unconfigured.

`Bugfix` | [ba58bae5b7](https://github.com/onegov/onegov-cloud/commit/ba58bae5b7bbd4f884faaea894c190b874823641)

### Translator Direcory

##### Make `operation_comments` editor visible field.

`Feature` | [OGC-3065](https://linear.app/onegovcloud/issue/OGC-3065) | [8bde6add9a](https://github.com/onegov/onegov-cloud/commit/8bde6add9a2e2b4ab48a11e6d2d8c2e4bf0019bd)

## ech0252

`2026-03-20` | [0e89ad461d...5c58a21e9f](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...5c58a21e9f)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Core

##### Upgrades to Python 3.14

`Feature` | [OGC-3038](https://linear.app/onegovcloud/issue/OGC-3038) | [585abf6c8d](https://github.com/onegov/onegov-cloud/commit/585abf6c8d91f8e4cda709bac2970bf0d146b32d)

### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

##### No longer delete elections on the same date.

Deleting all elections on the same date that are not in the current
eCH 0252 delivery is to aggressive. Remove only elections in the
same ElectionCompound.

`Feature` | [5c58a21e9f](https://github.com/onegov/onegov-cloud/commit/5c58a21e9f60f1a3e5d129e7529397125a751922)

### Event

##### Switches new source filter to a prefix filter

When we import events we always store source as a combination of
a prefix followed by the original id, so only allowing the entire
source for filtering is not helpful. Instead we now filter by prefix.

`Bugfix` | [OGC-3021](https://linear.app/onegovcloud/issue/OGC-3021) | [38f35221d7](https://github.com/onegov/onegov-cloud/commit/38f35221d72cfea84bd6fb3d8f3c23ee07d913cf)

### Search

##### Add breadcrumbs to search results in order to provide more context

`Feature` | [OGC-2880](https://linear.app/onegovcloud/issue/OGC-2880) | [7cf450189b](https://github.com/onegov/onegov-cloud/commit/7cf450189b6cbb427be146fa413946df840eafe5)

### User

##### Adds an `ensure_user` callback to modify login-system behavior

`Feature` | [OGC-3049](https://linear.app/onegovcloud/issue/OGC-3049) | [c690d7d4c7](https://github.com/onegov/onegov-cloud/commit/c690d7d4c74fddda585a17ec6e975ed4ac7f2e5c)

## 2026.16

`2026-03-18` | [2d2f7e1f80...2ed1e9db67](https://github.com/OneGov/onegov-cloud/compare/2d2f7e1f80^...2ed1e9db67)

### Landsgemeinde

##### Fixes drafts being publicly visible and accessible

`Bugfix` | [OGC-3040](https://linear.app/onegovcloud/issue/OGC-3040) | [2d2f7e1f80](https://github.com/onegov/onegov-cloud/commit/2d2f7e1f80b6dffb4efdae87a32685691d580b2d)

## ech0252

`2026-03-18` | [0e89ad461d...4a0a8a0904](https://github.com/OneGov/onegov-cloud/compare/0e89ad461d^...4a0a8a0904)

**Upgrade hints**
- New version of xsdata-ech required, run `make update`
### Election-Day

##### Improves error messages in API

Return proper errors in JSON for 401 and 500 errors.

`Feature` | [0e89ad461d](https://github.com/onegov/onegov-cloud/commit/0e89ad461dc51dabebaa97b3e0c9bf9d7bb94c3b)

##### Adds support for eCH-0252 V2.0.0

Replaces existing pre release support.

`Feature` | [fbe95b9391](https://github.com/onegov/onegov-cloud/commit/fbe95b9391d20a027acc296d089f00e17aebdde5)

##### Improves error message for unsupported DOI

`Feature` | [a0d220d432](https://github.com/onegov/onegov-cloud/commit/a0d220d4329c5d53f2b302283fe6d6f4b207ac1e)

## 2026.15

`2026-03-17` | [97194afd57...36363b5db9](https://github.com/OneGov/onegov-cloud/compare/97194afd57^...36363b5db9)

### Org

##### Extends events API endpoint with filters

`Feature` | [OGC-3021](https://linear.app/onegovcloud/issue/OGC-3021) | [97194afd57](https://github.com/onegov/onegov-cloud/commit/97194afd578684e3eb5b3d04515714a22fdc8146)

## 2026.14

`2026-03-17` | [6ea1066d5b...1ada718257](https://github.com/OneGov/onegov-cloud/compare/6ea1066d5b^...1ada718257)

### Agency

##### New UI

New UI using foundation 6.

`Feature` | [OGC-2853](https://linear.app/onegovcloud/issue/OGC-2853) | [94219e1eb3](https://github.com/onegov/onegov-cloud/commit/94219e1eb32f30d5e4e276423b9bc2df91c3d4c1)

### Api

##### Adds html link to person, agency and memebership

`Feature` | [OGC-2989](https://linear.app/onegovcloud/issue/OGC-2989) | [312ae338e4](https://github.com/onegov/onegov-cloud/commit/312ae338e44a44a9e228ef508933700f5a0a15c7)

### Form

##### Improve `formcoder` prompt

`Feature` | [OGC-2974](https://linear.app/onegovcloud/issue/OGC-2974) | [cf2d9f6198](https://github.com/onegov/onegov-cloud/commit/cf2d9f619821ca91123f532f065e2ee023c5f3c5)

## 2026.13

`2026-03-13` | [926add3838...bcc04abfb1](https://github.com/OneGov/onegov-cloud/compare/926add3838^...bcc04abfb1)

### Core

##### Upgrades to Python 3.12

`Feature` | [OGC-1604](https://linear.app/onegovcloud/issue/OGC-1604) | [1fa7d9f2a5](https://github.com/onegov/onegov-cloud/commit/1fa7d9f2a5f0d4e64cb1f3a7368c97b5650be939)

### Org

##### Removes "Item(s)" text in mails for numeric fields

This text only really made sense for a small subset of numeric fields,
if this pops up again as a feature request, we should extend formcode
instead with an optional unit label for numeric fields.

`Bugfix` | [OGC-3023](https://linear.app/onegovcloud/issue/OGC-3023) | [926add3838](https://github.com/onegov/onegov-cloud/commit/926add3838b1a9ea0ef2fabbffb1e12fb8a0cb09)

##### Fixes arbitrary files showing up in the photoalbum image selection

`Bugfix` | [OGC-3024](https://linear.app/onegovcloud/issue/OGC-3024) | [9c86521d9d](https://github.com/onegov/onegov-cloud/commit/9c86521d9dae64cefda9079b6f84ada30ebbd32a)

##### Fixes arbitrary files showing up in the file picker

`Bugfix` | [eb7e22c5f0](https://github.com/onegov/onegov-cloud/commit/eb7e22c5f01fac1fd2e80dea543e218e9dab1f79)

##### Hardens a couple of other file queries against incorrect file types

`Bugfix` | [efb439261e](https://github.com/onegov/onegov-cloud/commit/efb439261e24fd20ba9811c41898958509137112)

##### Fixes re-publishing a withdrawn event from its ticket

`Bugfix` | [OGC-3002](https://linear.app/onegovcloud/issue/OGC-3002) | [cb9d4cf060](https://github.com/onegov/onegov-cloud/commit/cb9d4cf060099b177400dc3e311fb79ce22fa69f)

### Pas

##### Fixes file download permissions for parliamentarians.

`Bugfix` | [OGC-2942](https://linear.app/onegovcloud/issue/OGC-2942) | [d4837e64ac](https://github.com/onegov/onegov-cloud/commit/d4837e64ac88a4b397b11144c96b6ec2987cba63)

### Photoalbum

##### Remove error message for non images, simplify template

`Bugfix` | [OGC-2997](https://linear.app/onegovcloud/issue/OGC-2997) | [495848763e](https://github.com/onegov/onegov-cloud/commit/495848763e51813113a9485f8ff7c1ef8989b075)

## votes2

`2026-03-12` | [19e0174404...f5398c1bcd](https://github.com/OneGov/onegov-cloud/compare/19e0174404^...f5398c1bcd)

## votes

`2026-03-11` | [7bcfbc7ca6...cd0b7131c4](https://github.com/OneGov/onegov-cloud/compare/7bcfbc7ca6^...cd0b7131c4)

### Election-Day

##### Explicitly imports and stores number of received votes.

For complex votes the number of invalid and (completely) empty ballots
may not be mapped to the individual results so that the number of
received votes cannot be derived from the other numbers.

`Feature` | [OGC-3011](https://linear.app/onegovcloud/issue/OGC-3011) | [7bcfbc7ca6](https://github.com/onegov/onegov-cloud/commit/7bcfbc7ca699804c3e98d144b491937a5a54588e)

### Org

##### Increase ticket message limit.

`Feature` | [OGC-2542](https://linear.app/onegovcloud/issue/OGC-2542) | [85c3225a40](https://github.com/onegov/onegov-cloud/commit/85c3225a409ca9acbc3fbd45c59fe13cb783cc24)

##### Fixes reservation export being empty.

`Bugfix` | [OGC-3008](https://linear.app/onegovcloud/issue/OGC-3008) | [69b7867648](https://github.com/onegov/onegov-cloud/commit/69b78676487574b8d3021e335042ab351690c9cf)

### Settings

##### Remove migrate links from settings view

`Feature` | [OGC-3003](https://linear.app/onegovcloud/issue/OGC-3003) | [61936f3248](https://github.com/onegov/onegov-cloud/commit/61936f3248d8c78f146f927846c13bf5e65a6635)

## fedpol

`2026-03-10` | [17ecf7e9f6...40ee4fa04b](https://github.com/OneGov/onegov-cloud/compare/17ecf7e9f6^...40ee4fa04b)

### Fedpol

##### Adds demo application

`Feature` | [OGC-2979](https://linear.app/onegovcloud/issue/OGC-2979) | [17ecf7e9f6](https://github.com/onegov/onegov-cloud/commit/17ecf7e9f609caf8fbbb2f81e44db7db8c3779b4)

### Form

##### Adds AI support to generate form code

`Feature` | [OGC-2974](https://linear.app/onegovcloud/issue/OGC-2974) | [71ba68e5e0](https://github.com/onegov/onegov-cloud/commit/71ba68e5e040e654526c745a21da650c739b852a)

##### Change form code link to docs.admin.digital

`Feature` | [OGC-3006](https://linear.app/onegovcloud/issue/OGC-3006) | [f384b48e19](https://github.com/onegov/onegov-cloud/commit/f384b48e196af082791249c5e4aa4b44ae3a0236)

##### Fixes form code parser incorrectly escaping help messages

`Bugfix` | [OGC-3015](https://linear.app/onegovcloud/issue/OGC-3015) | [cb526a472a](https://github.com/onegov/onegov-cloud/commit/cb526a472af0e5b12292d00db155ae776d6a3f05)

## 2026.12

`2026-03-09` | [0b252fd439...6ed90f787e](https://github.com/OneGov/onegov-cloud/compare/0b252fd439^...6ed90f787e)

### Form

##### Change form code link to docs.admin.digital

`Feature` | [OGC-3006](https://linear.app/onegovcloud/issue/OGC-3006) | [f34cdb6767](https://github.com/onegov/onegov-cloud/commit/f34cdb67673d44ca00041b8b4a92a8a40400bf95)

##### Adds AI support to generate form code

`Feature` | [OGC-2974](https://linear.app/onegovcloud/issue/OGC-2974) | [85f5f3af5e](https://github.com/onegov/onegov-cloud/commit/85f5f3af5ed3a8aa9a929eec5d0dd37a71e852ad)

### Pas

##### Fixes two minor issues in export.

`Bugfix` | [OGC-3005](https://linear.app/onegovcloud/issue/OGC-3005) | [0b252fd439](https://github.com/onegov/onegov-cloud/commit/0b252fd439b1de873aedc853e24475d29123949a)

### Photoalbum

##### Fix missing size attribute for grid mode

`Bugfix` | [OGC-2997](https://linear.app/onegovcloud/issue/OGC-2997) | [0d16f99784](https://github.com/onegov/onegov-cloud/commit/0d16f9978420611168fe9d6b298da396bbdeb909)

## fedpol4

`2026-03-09` | [f384b48e19...f384b48e19](https://github.com/OneGov/onegov-cloud/compare/f384b48e19^...f384b48e19)

### Form

##### Change form code link to docs.admin.digital

`Feature` | [OGC-3006](https://linear.app/onegovcloud/issue/OGC-3006) | [f384b48e19](https://github.com/onegov/onegov-cloud/commit/f384b48e196af082791249c5e4aa4b44ae3a0236)

## fedpol3

`2026-03-09` | [71ba68e5e0...71ba68e5e0](https://github.com/OneGov/onegov-cloud/compare/71ba68e5e0^...71ba68e5e0)

### Form

##### Adds AI support to generate form code

`Feature` | [OGC-2974](https://linear.app/onegovcloud/issue/OGC-2974) | [71ba68e5e0](https://github.com/onegov/onegov-cloud/commit/71ba68e5e040e654526c745a21da650c739b852a)

