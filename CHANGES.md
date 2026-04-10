# Changes

## 2026.21

No changes since last release

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

## fedpol2

`2026-03-05` | [cace0810c8...2d54353105](https://github.com/OneGov/onegov-cloud/compare/cace0810c8^...2d54353105)

## fedpol

`2026-03-04` | [17ecf7e9f6...6b6a653c12](https://github.com/OneGov/onegov-cloud/compare/17ecf7e9f6^...6b6a653c12)

### Fedpol

##### Adds demo application

`Feature` | [OGC-2979](https://linear.app/onegovcloud/issue/OGC-2979) | [17ecf7e9f6](https://github.com/onegov/onegov-cloud/commit/17ecf7e9f609caf8fbbb2f81e44db7db8c3779b4)

### Feriennet

##### Text change and infopanel

Changed "attendees" to "carpool contacts" and added an infopanel for clarification .

`Feature` | [PRO-1494](https://linear.app/projuventute/issue/PRO-1494) | [3355fe7af8](https://github.com/onegov/onegov-cloud/commit/3355fe7af82fd96d6bd3db6abad27300941ba14a)

### Org

##### Fixes potential float underflow error in search query

`Bugfix` | [1cf45d9254](https://github.com/onegov/onegov-cloud/commit/1cf45d9254177f8d90898943c977e83c9bad906c)

### Pas

##### Makes the label more clear that it's decimal hours input.

`Feature` | [2b7c50efd3](https://github.com/onegov/onegov-cloud/commit/2b7c50efd36752842aace6e267c162577678a7a8)

##### Send email if a commission finalized.

`Feature` | [OGC-2941](https://linear.app/onegovcloud/issue/OGC-2941) | [8bd5c50179](https://github.com/onegov/onegov-cloud/commit/8bd5c50179a3a36d954fb93e449cc839fc29443d)

##### Reduce log level to prevent sentry spam.

`Bugfix` | [b0a97bfa13](https://github.com/onegov/onegov-cloud/commit/b0a97bfa13d4b7ae94400731ce96eeec6f9e84d4)

### Payment

##### Fix sqlalchemy 2.0 loader path strictness for payment batch-set

Fixes sentry: https://seantis-gmbh.sentry.io/issues/7294132496

`Bugfix` | [NONE](#NONE) | [3cb3d433fa](https://github.com/onegov/onegov-cloud/commit/3cb3d433faf5f5651bbbe8e7421c0dba56eed00d)

### Ris

##### Fix wrong translation for political party

`Bugfix` | [OGC-2994](https://linear.app/onegovcloud/issue/OGC-2994) | [dce46c6fb0](https://github.com/onegov/onegov-cloud/commit/dce46c6fb064c0774b6ba02a0ab363b46a5837aa)

### Tests

##### Fix leap year issue in test

Replace freeze_time with date.today as both Python and SQL expression agree on ages

`Bugfix` | [NONE](#NONE) | [5e9f8c21d2](https://github.com/onegov/onegov-cloud/commit/5e9f8c21d2804c0ca99e68f2e2ea691982646ed4)

## 2026.11

`2026-02-27` | [f5feeeea66...c8c42347ea](https://github.com/OneGov/onegov-cloud/compare/f5feeeea66^...c8c42347ea)

### Feriennet

##### Show error if file cannot be displayed in photo album

`Feature` | [OGC-2976](https://linear.app/onegovcloud/issue/OGC-2976) | [6730b8d860](https://github.com/onegov/onegov-cloud/commit/6730b8d860436c2d1ebfeea74f43ea2c0b95ae8e)

##### Fix period info

Show wishlist info not only when wishlist phase is active

`Bugfix` | [PRO-1487](https://linear.app/projuventute/issue/PRO-1487) | [33fe463c48](https://github.com/onegov/onegov-cloud/commit/33fe463c48b1ccfef78a3d9520414e6365ad02ac)

##### Prevent photoalbum and photoalbum overview from crashing due to missing size attribute (e.g. video)

This is just an intermediate step. We may need to handle different file types in albums differently

`Bugfix` | [OGC-2976](https://linear.app/onegovcloud/issue/OGC-2976) | [31a6fed7c2](https://github.com/onegov/onegov-cloud/commit/31a6fed7c27933281242b1bc0490da68a6bf695d)

### Org

##### Adds a change username function for admins

Changing usernames is only allowed for users that are not sourced from
an external login provider and if the current admin user has either a
Yubikey or TOTP second factor configured (mTAN is not yet supported).

This also adds a CLI command to change usernames, which can be utilized
in all applications, not just Org.

`Feature` | [OGC-2532](https://linear.app/onegovcloud/issue/OGC-2532) | [4b4467c068](https://github.com/onegov/onegov-cloud/commit/4b4467c068fe9add20957ecde58e2443a941ba87)

##### Makes `OrgRequest.current_user` more robust

With SQLAlchemy 2.0 it is possible for the `User` object to become
detached, which can result in errors if we try to access a deferred
attribute later on.

`Bugfix` | [47bf5c3bd0](https://github.com/onegov/onegov-cloud/commit/47bf5c3bd0cf87baa1bcf1f9b57c8e7f86616421)

##### Fixes inverted condition in allocation display

`Bugfix` | [OGC-2984](https://linear.app/onegovcloud/issue/OGC-2984) | [17e9addabd](https://github.com/onegov/onegov-cloud/commit/17e9addabde93d74f60661976585c15f3e067cd7)

### Pas

##### Fixes an issue with comma in filename on windows.

`Bugfix` | [NONE](#NONE) | [64908b60ac](https://github.com/onegov/onegov-cloud/commit/64908b60ac0b0ef184d62d8181a096c378aef130)

##### Make sure address fits in letter.

`Bugfix` | [NONE](#NONE) | [0d478902be](https://github.com/onegov/onegov-cloud/commit/0d478902beda550c5cd7f8c9e4d11acfbcd31b57)

##### Display the true value for plenary session.

`Bugfix` | [NONE](#NONE) | [7fac7accd6](https://github.com/onegov/onegov-cloud/commit/7fac7accd61a164d84ad6ae71f6129d9b327eec2)

##### Round to two decimal places.

`Bugfix` | [74859ffcc8](https://github.com/onegov/onegov-cloud/commit/74859ffcc85a968c0d6df2fcca99222bbf82863d)

### Town6

##### Remove searchbar in empty slider

Don't display the searchbar if there are no images in the slider

`Other` | [f5feeeea66](https://github.com/onegov/onegov-cloud/commit/f5feeeea66ccc9ff407fc3008f434afbde8eabb5)

### Wab

##### Handle invalid polling day date

`Feature` | [OGC-2785](https://linear.app/onegovcloud/issue/OGC-2785) | [3d0b3fe3d4](https://github.com/onegov/onegov-cloud/commit/3d0b3fe3d4c4a1e5db126e8122a64214260c8393)

##### Prevent cli update archived results for development and staging

As `official_host` is not set for development and staging, cli `upload-archived-results` may cause duplicates when uploading new results due to different urls.

`Feature` | [OGC-2978](https://linear.app/onegovcloud/issue/OGC-2978) | [34820b252c](https://github.com/onegov/onegov-cloud/commit/34820b252c306342d9defa6f2f38bbf4d3fcdb48)

## ui

`2026-02-23` | [dd502dc069...997bc59a4a](https://github.com/OneGov/onegov-cloud/compare/dd502dc069^...997bc59a4a)

## 2026.10

`2026-02-20` | [673622456d...007adfdc2d](https://github.com/OneGov/onegov-cloud/compare/673622456d^...007adfdc2d)

### Wab

##### Improve error handling for xml file upload

`Bugfix` | [OGC-2785](https://linear.app/onegovcloud/issue/OGC-2785) | [673622456d](https://github.com/onegov/onegov-cloud/commit/673622456dfe01f640bab2527068fa659acae899)

## ui

`2026-02-20` | [dd502dc069...a7ce12aa8e](https://github.com/OneGov/onegov-cloud/compare/dd502dc069^...a7ce12aa8e)

### Feriennet

##### Add contact form, photoalbums and volunteer to main menu

Add link to the first form in form colleciton, link to photoalbums and link to volunteer activity list to the navigation.

`Feature` | [PRO-1468](https://linear.app/projuventute/issue/PRO-1468) | [0388161dc8](https://github.com/onegov/onegov-cloud/commit/0388161dc8e346c12a8c350c7ca9d16b5601d5ac)

### Org

##### Ensure mime type validation on file upload fields in form code

`Feature` | [OGC-2738](https://linear.app/onegovcloud/issue/OGC-2738) | [ff77bff6b9](https://github.com/onegov/onegov-cloud/commit/ff77bff6b96074d7c5ce5a85d7a50c818287176f)

## 2026.9

`2026-02-19` | [01dce7374a...3042c5af71](https://github.com/OneGov/onegov-cloud/compare/01dce7374a^...3042c5af71)

### Core

##### Upgrades to SQLAlchemy 2.0

`Feature` | [OGC-2945](https://linear.app/onegovcloud/issue/OGC-2945) | [dea56b3a58](https://github.com/onegov/onegov-cloud/commit/dea56b3a588dcccaada62728638773f5bdfb967b)

### Feriennet

##### Update homepage template

`Feature` | [65a5d96515](https://github.com/onegov/onegov-cloud/commit/65a5d965159661bea145f415ffdbc3cd6639206d)

##### Fix problem with selecting user for manual booking

- The dropdown for the users now pre-selects the correct user again.
- The users are now displayed correctly again and can be selected

`Bugfix` | [PRO-1481](https://linear.app/projuventute/issue/PRO-1481) | [574e4844b6](https://github.com/onegov/onegov-cloud/commit/574e4844b6e79a980688a40b82bbafedebaf89ff)

##### Fix problem with volunteer list

Newly loaded activity needs could not be added to the volunteers list

`Bugfix` | [PRO-1480](https://linear.app/projuventute/issue/PRO-1480) | [8a1f72e2ac](https://github.com/onegov/onegov-cloud/commit/8a1f72e2ac3ab1476626427ce186b2479be65af9)

### Pas

##### Add bulk operations for shortest meeting.

`Feature` | [OGC-2941](https://linear.app/onegovcloud/issue/OGC-2941) | [3b7d41a6c8](https://github.com/onegov/onegov-cloud/commit/3b7d41a6c85dc095915d6f7659e6099ad2a6a7c7)

##### Granular improvements based on feedback.

`Feature` | [OGC-2941](https://linear.app/onegovcloud/issue/OGC-2941) | [51ed0825eb](https://github.com/onegov/onegov-cloud/commit/51ed0825eb506b72922902e286a2e08a95b7f7a8)

### Town 6

##### Fix form size when files are attached

`Bugfix` | [OGC-2908](https://linear.app/onegovcloud/issue/OGC-2908) | [01dce7374a](https://github.com/onegov/onegov-cloud/commit/01dce7374a84d28bce8f9950164d14c6c7f295da)

## 2026.8

`2026-02-17` | [56a0169055...e39ad8b3da](https://github.com/OneGov/onegov-cloud/compare/56a0169055^...e39ad8b3da)

## 2026.7

`2026-02-17` | [f20e7fc393...2189bbd8f8](https://github.com/OneGov/onegov-cloud/compare/f20e7fc393^...2189bbd8f8)

### Feriennet

##### Resolves n+1 queries for homepage

Sentry examples:

    https://seantis-gmbh.sentry.io/issues/trace/0c49d7a3f0314d11acec7a2859f47232/
    https://seantis-gmbh.sentry.io/issues/trace/72578e382105402aac1ef2a6c37e056b/

`Performance` | [NONE](#NONE) | [f20e7fc393](https://github.com/onegov/onegov-cloud/commit/f20e7fc393a11557e862c93cb95e64486c43d04d)

## 2026.6

`2026-02-16` | [8101345cbe...f7481046ca](https://github.com/OneGov/onegov-cloud/compare/8101345cbe^...f7481046ca)

### Directories

##### Improves description for map configuration

Replaces word `coordinate` with `map` to explain what really happens.

`Feature` | [OGC-2883](https://linear.app/onegovcloud/issue/OGC-2883) | [cde5e5f3f8](https://github.com/onegov/onegov-cloud/commit/cde5e5f3f87be6fd77b1a1a85afd909d0d42f51a)

### Electionday

##### Improve layout for proposal, counterproposal and tie-breaker

`Feature` | [OGC-2850](https://linear.app/onegovcloud/issue/OGC-2850) | [872c94297d](https://github.com/onegov/onegov-cloud/commit/872c94297df645929aa115ff019ff7216a04da44)

##### Fix missing indent if no results for complex vote

`Bugfix` | [OGC-2850](https://linear.app/onegovcloud/issue/OGC-2850) | [d10d4b7cd6](https://github.com/onegov/onegov-cloud/commit/d10d4b7cd6604edb9110e8c4fa3bcf27e4287462)

### Org

##### Adds icon to vat settings menu

`Bugfix` | [OGC-2917](https://linear.app/onegovcloud/issue/OGC-2917) | [11aaf9700b](https://github.com/onegov/onegov-cloud/commit/11aaf9700b6f45ad7c791ca37d536827172ce5d5)

### Town6

##### Fix Dashboard in case of unavailable web statistics

`Bugfix` | [NONE](#NONE) | [d48491fc95](https://github.com/onegov/onegov-cloud/commit/d48491fc9579ef5336d7553261e0ddc1dce23ff2)

## test

`2026-02-11` | [dd502dc069...b8306cab4c](https://github.com/OneGov/onegov-cloud/compare/dd502dc069^...b8306cab4c)

### Town6

##### Fix bug in datetime selection

`Bugfix` | [PRO-1478](https://linear.app/projuventute/issue/PRO-1478) | [0a4012edd8](https://github.com/onegov/onegov-cloud/commit/0a4012edd806ba1f1cb46d471f460484984e8368)

## 2026.5

`2026-02-10` | [7178b5005b...c93df57ee5](https://github.com/OneGov/onegov-cloud/compare/7178b5005b^...c93df57ee5)

**Upgrade hints**
- onegov-election-day --select /onegov_election_day/gr update-archived-results
### Core

##### Prepares for SQLAlchemy 2.0 upgrade

`Feature` | [OGC-2944](https://linear.app/onegovcloud/issue/OGC-2944) | [ea2ef0eb7f](https://github.com/onegov/onegov-cloud/commit/ea2ef0eb7ff6e9162e3b935ae7fcaf98c736e2eb)

### Feriennet

##### Period display bugfix

`Bugfix` | [OGC-1467](https://linear.app/onegovcloud/issue/OGC-1467) | [111eac326b](https://github.com/onegov/onegov-cloud/commit/111eac326b77d44da6c0d757c66c78fab9c0e3b0)

### Landsgemeinde

##### Allows refining search results with a date range

All relevant content types now use the assembly date as their reference
date in the search index.

`Feature` | [OGC-2909](https://linear.app/onegovcloud/issue/OGC-2909) | [65746148d2](https://github.com/onegov/onegov-cloud/commit/65746148d202c25738e79cc3c53d3b5505fad893)

### Org

##### Avoids confusion by sometimes hiding the availability text

Allocations that are in the past or no longer/not yet available
because they're outside the registration window would previously
sometimes say that they're available, or partly available, even
though they can't be reserved. Since the reason for why they're
currently unavailable can be a bit contrived, it's better to not
display anything at all. Customers will still get a clear explanation
when they try to reserve these slots.

`Feature` | [OGC-2334](https://linear.app/onegovcloud/issue/OGC-2334) | [0e575db9cc](https://github.com/onegov/onegov-cloud/commit/0e575db9cc7662715f58093221e2e277638d1119)

##### Fixes CSP for Stripe/Datatrans payments

`Bugfix` | [OGC-2948](https://linear.app/onegovcloud/issue/OGC-2948) | [ccf901324f](https://github.com/onegov/onegov-cloud/commit/ccf901324faef9bf73bb66b4fc3021108fa34513)

##### Fixes blocker created with no reason being set to `null`

`Bugfix` | [OGC-2954](https://linear.app/onegovcloud/issue/OGC-2954) | [28fb8697dc](https://github.com/onegov/onegov-cloud/commit/28fb8697dccb64c642a3529803f04c2578d90f6e)

##### Fixes regression in `send_ticket_mail`

`Bugfix` | [OGC-2960](https://linear.app/onegovcloud/issue/OGC-2960) | [d983f55617](https://github.com/onegov/onegov-cloud/commit/d983f556171c49d87100825928628af424d2cd8a)

### Town 6

##### Searchbar on homepage slider and video

`Feature` | [OGC-2790](https://linear.app/onegovcloud/issue/OGC-2790) | [5fa5d7056e](https://github.com/onegov/onegov-cloud/commit/5fa5d7056e2a0d9c74cf9dfd57e3f274f3494dc8)

### Town6

##### Fix display bug of images

`Bugfix` | [OGC-2901](https://linear.app/onegovcloud/issue/OGC-2901) | [93b61635fa](https://github.com/onegov/onegov-cloud/commit/93b61635fad07090fb0195ff74312b0c52be0c2d)

### Wab

##### Show proposal, counterproposal and tie-breaker results separately for complex votes

`Feature` | [OGC-2850](https://linear.app/onegovcloud/issue/OGC-2850) | [435dbf9ae8](https://github.com/onegov/onegov-cloud/commit/435dbf9ae8c85197e60d213591ce0a11b90fa5d4)

## 2026.4

`2026-01-30` | [574f21d1c1...195a697ab3](https://github.com/OneGov/onegov-cloud/compare/574f21d1c1^...195a697ab3)

### Directory

##### Fix directory migration crash when renaming option labels

`Bugfix` | [OGC-2353](https://linear.app/onegovcloud/issue/OGC-2353) | [6bbe21e2a0](https://github.com/onegov/onegov-cloud/commit/6bbe21e2a0647bcbb428908d5aee663a9dc8a7b2)

### Org

##### Replaces data-attributes that triggered a call of `eval`

This means we no longer have any views where we have to add a narrow
`unsafe-eval` exception to the CSP, in order to make things work.

`Feature` | [OGC-2916](https://linear.app/onegovcloud/issue/OGC-2916) | [24b52c862e](https://github.com/onegov/onegov-cloud/commit/24b52c862e06d2097c85848194445f5ec8304ad2)

### Page

##### Improve iframe domain validation to for configured domains.

Right split trailing slashes from configured domains prior comparison

`Feature` | [OGC-2940](https://linear.app/onegovcloud/issue/OGC-2940) | [005ce6fc34](https://github.com/onegov/onegov-cloud/commit/005ce6fc34f25b27cfaaa05d14cc8e4c736dc48a)

### Pas

##### Validate attendance to be within a settlement run.

`Bugfix` | [OGC-2848](https://linear.app/onegovcloud/issue/OGC-2848) | [9762773489](https://github.com/onegov/onegov-cloud/commit/97627734897050e2435e9a2d0622a3e66af017d0)

##### Ensure finalized attendance for commission.

`Bugfix` | [OGC-2845](https://linear.app/onegovcloud/issue/OGC-2845) | [58d94c5689](https://github.com/onegov/onegov-cloud/commit/58d94c568988d3748aa184372b1ee755ac0c858a)

## 2026.3

`2026-01-29` | [e17f907a3b...742db7bad0](https://github.com/OneGov/onegov-cloud/compare/e17f907a3b^...742db7bad0)

### Feriennet

##### Banner

`Feature` | [PRO-1474](https://linear.app/projuventute/issue/PRO-1474) | [09587de5de](https://github.com/onegov/onegov-cloud/commit/09587de5dec6f8da0f64717cc926937b4a535983)

### Org

##### Adds a resource switcher to the occupancy view

`Feature` | [OGC-2873](https://linear.app/onegovcloud/issue/OGC-2873) | [3943814f00](https://github.com/onegov/onegov-cloud/commit/3943814f00d40378b65be76af3100f4f9ec34114)

##### Adds an utilization stats button to the occupancy view

`Feature` | [OGC-2062](https://linear.app/onegovcloud/issue/OGC-2062) | [0baff1be97](https://github.com/onegov/onegov-cloud/commit/0baff1be97f0105c4f9fb3fdb37c292a93e91350)

##### Adds missing access hints in boardlets

`Bugfix` | [cd3d24431a](https://github.com/onegov/onegov-cloud/commit/cd3d24431a59ab8edde4049e50eb5b8ba5decb51)

##### Resolve fixme for TagField

`Bugfix` | [92b85f250f](https://github.com/onegov/onegov-cloud/commit/92b85f250f0f9cd3d0101ed082ff9d057c3a43bf)

##### Fixes reservation blockers for non-partly available allocations

`Bugfix` | [OGC-2937](https://linear.app/onegovcloud/issue/OGC-2937) | [92064770d5](https://github.com/onegov/onegov-cloud/commit/92064770d54e48997a5d471a859def6ab336f022)

### Search

##### Adds it_ch to used locales for Org and Town6

`Feature` | [OGC-2931](https://linear.app/onegovcloud/issue/OGC-2931) | [138cf9df78](https://github.com/onegov/onegov-cloud/commit/138cf9df78942706cddb5c1f7a55cb373d3cb59e)

### Town6

##### Allow to copy newsletter.

`Feature` | [OGC-1663](https://linear.app/onegovcloud/issue/OGC-1663) | [9af1fd1d74](https://github.com/onegov/onegov-cloud/commit/9af1fd1d74a7297f6314e7c093b0363220e399fc)

## 2026.2

`2026-01-23` | [7fe7cf163c...2f191d9543](https://github.com/OneGov/onegov-cloud/compare/7fe7cf163c^...2f191d9543)

### Core

##### Upgrades SQLAlchemy to version 1.4

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [7fe7cf163c](https://github.com/onegov/onegov-cloud/commit/7fe7cf163c340b75a7d5d99b18a07cd6ecd74dd1)

### Town6

##### Change background-size from cover to contain for image display.

`Bugfix` | [OGC-2867](https://linear.app/onegovcloud/issue/OGC-2867) | [8687186243](https://github.com/onegov/onegov-cloud/commit/86871862437fff784be55c4d0b4e607d45f8ff3a)

##### Increases robustness if underlying pdf of form doesn't exist.

`Bugfix` | [OGC-2922](https://linear.app/onegovcloud/issue/OGC-2922) | [1314f1bdf8](https://github.com/onegov/onegov-cloud/commit/1314f1bdf83b0fa65528bc9a2b5ed1e8436047e0)

## 2026.1

`2026-01-16` | [93d40ac5bd...b829bbf934](https://github.com/OneGov/onegov-cloud/compare/93d40ac5bd^...b829bbf934)

### Api

##### Extends standard Collection+JSON with a couple of meta properties

This provides additional context to users of the API, what each endpoint
contains.

`Feature` | [OGC-2912](https://linear.app/onegovcloud/issue/OGC-2912) | [68dd72486c](https://github.com/onegov/onegov-cloud/commit/68dd72486ccec8fa57adf9dd42036be7fb0bda62)

### Core

##### Replaces free-text analytics code with configurable providers

`Feature` | [OGC-2865](https://linear.app/onegovcloud/issue/OGC-2865) | [232119d51a](https://github.com/onegov/onegov-cloud/commit/232119d51a51b820c0603b4d35583e30b47825c5)

##### Makes default Content-Security-Policy more strict

Core: Makes default Content-Security-Policy more strict

This also updates foundation6 to the latest version as well as various
JS components, so they comply with the more strict CSP

`Feature` | [OGC-2740](https://linear.app/onegovcloud/issue/OGC-2740) | [231ad17b91](https://github.com/onegov/onegov-cloud/commit/231ad17b916e951909a0889f570f7b3eb1407aba)

##### Fix duplicate Message-ID header causing email queue failures.

`Bugfix` | [60ff3e03a5](https://github.com/onegov/onegov-cloud/commit/60ff3e03a5e2ae09e2a1823dc6d21f9a1dd01504)

##### Fix transfer command to use DSN connection parameters.

The transfer command was using `sudo -u postgres psql` which connects
to the system postgres user's default instance instead of respecting
the `onegov.yml` DSN configuration. This commit allows to use ports other 
than 5432 locally.

`Bugfix` | [6fc268cab6](https://github.com/onegov/onegov-cloud/commit/6fc268cab6d70a7c6269888acdc82f03bf69d4c8)

### Directory

##### Rename sidebar contact field

`Feature` | [OGC-2829](https://linear.app/onegovcloud/issue/OGC-2829) | [65fbf10196](https://github.com/onegov/onegov-cloud/commit/65fbf101961336bc24ee04e1546fc92e47851f75)

### Electionday

##### Adds map data and municipalities for 2026

`Feature` | [OGC-2906](https://linear.app/onegovcloud/issue/OGC-2906) | [6e8051b97d](https://github.com/onegov/onegov-cloud/commit/6e8051b97dc7a07636b0c126968bdc125de94208)

##### Fixes municipality and quarter data for 2026

`Bugfix` | [OGC-2906](https://linear.app/onegovcloud/issue/OGC-2906) | [57b7f49a21](https://github.com/onegov/onegov-cloud/commit/57b7f49a21c54e6aa46e505b46164d5b9c3eb2ff)

### Feriennet

##### Removes inline event handlers from templates

`Feature` | [OGC-2863](https://linear.app/onegovcloud/issue/OGC-2863) | [e357dd701e](https://github.com/onegov/onegov-cloud/commit/e357dd701e6d8c17285bdc0cabbfd61fb0fbb3a4)

##### Add narrow banners for email

`Bugfix` | [OGC-1460](https://linear.app/onegovcloud/issue/OGC-1460) | [170eea5533](https://github.com/onegov/onegov-cloud/commit/170eea5533674c7a238a58a872519df26c0ac12e)

##### Order of activities in activity widget

`Bugfix` | [PRO-1456](https://linear.app/projuventute/issue/PRO-1456) | [a854f104f1](https://github.com/onegov/onegov-cloud/commit/a854f104f1681c20fd148a74462b2d50ddadce84)

##### Filter "show more" bugfix

`Bugfix` | [PRO-1452](https://linear.app/projuventute/issue/PRO-1452) | [dc02194d72](https://github.com/onegov/onegov-cloud/commit/dc02194d72ba7962a451c6639f35de9d6803dc1b)

### Org

##### Improves e-mail threading for customer-facing ticket e-mails

We achieve this by setting (and remembering) the `Message-ID` and
setting the corresponding `In-Reply-To` and `References` headers.

`Feature` | [OGC-2869](https://linear.app/onegovcloud/issue/OGC-2869) | [6d761226e2](https://github.com/onegov/onegov-cloud/commit/6d761226e224ec32a71a493c7088f50fb28105a8)

##### Allows accepted reservations to be adjusted by managers

`Feature` | [OGC-2887](https://linear.app/onegovcloud/issue/OGC-2887) | [8ec0519afb](https://github.com/onegov/onegov-cloud/commit/8ec0519afbdcfd2fe9f6a7f457ba6398b1bf9454)

##### Adds administrative reservation blockers in the occupancy calendar

`Feature` | [OGC-2780](https://linear.app/onegovcloud/issue/OGC-2780) | [fbf6bf5cda](https://github.com/onegov/onegov-cloud/commit/fbf6bf5cdaeae102ce2817e39e37d6064d863ddb)

##### Fixes crash in invoice export for a large number of ticket groups

`Bugfix` | [OGC-2902](https://linear.app/onegovcloud/issue/OGC-2902) | [f928399ca0](https://github.com/onegov/onegov-cloud/commit/f928399ca0c9a0e717c02b751329cf6ba2ded498)

### Pas

##### Extend kub api call timeouts

As we found various sentry issues related to kub api timeouts

`Feature` | [NONE](#NONE) | [b8de6b01e5](https://github.com/onegov/onegov-cloud/commit/b8de6b01e5abf0aa0f5991f17a03a533e835058e)

##### Fixes N+1 query.

`Bugfix` | [c84cbe7755](https://github.com/onegov/onegov-cloud/commit/c84cbe775507cb4999547e5e69961c3f10be5df1)

### Resource

##### On resource deletion, handle archived tickets' date fields that may contain "[redacted]" instead of a datetime object.

`Feature` | [OGC-2793](https://linear.app/onegovcloud/issue/OGC-2793) | [409a5a323d](https://github.com/onegov/onegov-cloud/commit/409a5a323df27de407c5b986460a987530c50a40)

### Town6

##### Sidebar navigation closing

`Bugfix` | [OGC-2871](https://linear.app/onegovcloud/issue/OGC-2871) | [93d40ac5bd](https://github.com/onegov/onegov-cloud/commit/93d40ac5bd7d98654fe1c915d91bd465c8f29688)

##### Fixes some link elements crashing during rendering

`Bugfix` | [03fc0ce134](https://github.com/onegov/onegov-cloud/commit/03fc0ce13437d7756b61bc72c99045ffc20b6baf)

##### Fix image selection bug

`Bugfix` | [OGC-2901](https://linear.app/onegovcloud/issue/OGC-2901) | [86f2a7b2b6](https://github.com/onegov/onegov-cloud/commit/86f2a7b2b69a570dc7f5451fc9b6bde70daf4757)

### User

##### Adds explicit `last_login` column.

`Feature` | [OGC-2454](https://linear.app/onegovcloud/issue/OGC-2454) | [790bad6a9a](https://github.com/onegov/onegov-cloud/commit/790bad6a9ac0ceb3e8515021e92eb8b571f174a7)

## 2025.71

`2025-12-29` | [23c7322afb...cadf75d90c](https://github.com/OneGov/onegov-cloud/compare/23c7322afb^...cadf75d90c)

### Feriennet

##### Hide RSS Feed

`Feature` | [PRO-1458](https://linear.app/projuventute/issue/PRO-1458) | [8cbd225102](https://github.com/onegov/onegov-cloud/commit/8cbd225102b2207d1959b782cb99021f9399801a)

##### "Delete user" button

Deletion of a user in feriennet is now possible under the following conditions:
-    Has no attendees with bookings in the currently active period
-    Has no unpaid invoices in any period
-    Is not an organizer of any activities
-    Is not an admin

`Feature` | [PRO-987](https://linear.app/projuventute/issue/PRO-987) | [c4a775e09e](https://github.com/onegov/onegov-cloud/commit/c4a775e09e935f39e452ffc7bad4b70be72151ba)

##### Delete attendees

`Feature` | [PRO-1436](https://linear.app/projuventute/issue/PRO-1436) | [1fb8ee16a1](https://github.com/onegov/onegov-cloud/commit/1fb8ee16a18b3b3f2ec81cdf2a4135243226fe4c)

### Pas

##### Gets rid of inline event handler.

`Bugfix` | [OGC-2860](https://linear.app/onegovcloud/issue/OGC-2860) | [dde589d60e](https://github.com/onegov/onegov-cloud/commit/dde589d60eb6c1d7105886234b4f1789545127b9)

## 2025.70

`2025-12-19` | [7e83cff80c...2bf159789f](https://github.com/OneGov/onegov-cloud/compare/7e83cff80c^...2bf159789f)

### Form

##### Adds select all/deselect all buttons for multi checkbox fields

The buttons only get displayed if there are at least five options to
choose from. This also fixes a small bug with form resets when
there is a treeselect field present.

`Feature` | [OGC-2369](https://linear.app/onegovcloud/issue/OGC-2369) | [388a69d422](https://github.com/onegov/onegov-cloud/commit/388a69d422f66e76d9d3995bf5c0ba53d7c62560)

##### Identify wrongly indented identifier

But prevent wrongly indentation when loading a form

`Feature` | [OGC-2370](https://linear.app/onegovcloud/issue/OGC-2370) | [2cb04a6c3a](https://github.com/onegov/onegov-cloud/commit/2cb04a6c3a1e04ded187c1b576a506bd9824fbed)

### Org

##### Specify hint for notifications about ticket messages

`Feature` | [OGC-2672](https://linear.app/onegovcloud/issue/OGC-2672) | [7e83cff80c](https://github.com/onegov/onegov-cloud/commit/7e83cff80ce90a15888bd6eb2a0f05028be7be62)

##### Adds additional ways discounts in reservations can be calculated

Previously discounts always applied to the price per item/hour and
ignored any prices defined through extra fields. Now you can choose
to apply the discounts to just the extras, or everything at the end
as well.

`Feature` | [OGC-2263](https://linear.app/onegovcloud/issue/OGC-2263) | [4225ae51ba](https://github.com/onegov/onegov-cloud/commit/4225ae51baa8acd18930c3fb078c7fa11dd3f372)

##### Add o'clock in events time display.

`Feature` | [OGC-2763](https://linear.app/onegovcloud/issue/OGC-2763) | [4fd9547d95](https://github.com/onegov/onegov-cloud/commit/4fd9547d95085f281ce8abf0c4225d1c3902353a)

##### Improves search ranking for records that match with their title

`Feature` | [OGC-2789](https://linear.app/onegovcloud/issue/OGC-2789) | [98151c54a2](https://github.com/onegov/onegov-cloud/commit/98151c54a25327cbd9cdd6973d08051954b44477)

##### Produces smaller query strings for large ticket group filters

This improves compatibility with nginx proxies without having to resort
to very large buffer sizes.

`Bugfix` | [OGC-2824](https://linear.app/onegovcloud/issue/OGC-2824) | [93858c4997](https://github.com/onegov/onegov-cloud/commit/93858c499716ad86e5eaf8ce7bd5c33dd64b4f52)

### Pas

##### Disable YubiKey.

The two-factor authentication will be handled via a different
method; therefore, we do not want to use a YubiKey for this
namespace.

`Bugfix` | [0e6bb6554b](https://github.com/onegov/onegov-cloud/commit/0e6bb6554b7ced8701765630ab50c1c3223e2f6f)

### Ris

##### Fix N+1 Query for Parliamentarian view

`Performance` | [OGC-2876](https://linear.app/onegovcloud/issue/OGC-2876) | [af8e5530c0](https://github.com/onegov/onegov-cloud/commit/af8e5530c051365a1a1eefa152b92dbd601c635a)

### Search

##### Adds basic search result highlighting

This also moves string normalization from the client to the Postgres
server. This involves a little bit of additional setup on the server
but provides a better result highlighting experience.

`Feature` | [OGC-2881](https://linear.app/onegovcloud/issue/OGC-2881) | [e3b9d7d410](https://github.com/onegov/onegov-cloud/commit/e3b9d7d410f3dbd277e4c31b430adbb06df2a85c)

### Town6

##### Fix wrong event tag translation for Parties

`Bugfix` | [OGC-2890](https://linear.app/onegovcloud/issue/OGC-2890) | [d5b58c8026](https://github.com/onegov/onegov-cloud/commit/d5b58c8026fc8ec4e3dbbb659c27e8efabeaf8e9)

### Wil

##### Adds cli command to rename meeting files before July 2025

`Feature` | [OGC-2815](https://linear.app/onegovcloud/issue/OGC-2815) | [63e3cca045](https://github.com/onegov/onegov-cloud/commit/63e3cca0457180d30000ae758831faf6c691bcc4)

##### Event import failed due to missing location data

Some events recently do not provide location data which made the nightly import fail.

`Bugfix` | [OGC-2875](https://linear.app/onegovcloud/issue/OGC-2875) | [5506bfbb42](https://github.com/onegov/onegov-cloud/commit/5506bfbb42f53212db20977d198cd231758ca637)

### Winterthur

##### Gets rid of inline JavaScript in templates

`Feature` | [OGC-2859](https://linear.app/onegovcloud/issue/OGC-2859) | [e5df575d22](https://github.com/onegov/onegov-cloud/commit/e5df575d226662fe81a522c3f03e47284788de88)

## 2025.69

`2025-12-09` | [b39432183e...68810065f9](https://github.com/OneGov/onegov-cloud/compare/b39432183e^...68810065f9)

### Directory

##### Accordion mode now reflects the content fields hide labels from configuration

`Feature` | [OGC-2832](https://linear.app/onegovcloud/issue/OGC-2832) | [546a3bd918](https://github.com/onegov/onegov-cloud/commit/546a3bd9188472ab90d1a8088eb5ba11ac52ab3b)

### Feriennet

##### Remove privacy option in general settings and add in export

`Feature` | [OGC-1454](https://linear.app/onegovcloud/issue/OGC-1454) | [4246ff777d](https://github.com/onegov/onegov-cloud/commit/4246ff777d51667de2dac8f11243b136d1943390)

## 2025.68

`2025-12-05` | [5440ea7e83...979b8b8912](https://github.com/OneGov/onegov-cloud/compare/5440ea7e83^...979b8b8912)

### Core

##### Applies a more strict `Cache-Control` setting for logged in users

`Feature` | [OGC-2753](https://linear.app/onegovcloud/issue/OGC-2753) | [7e72534569](https://github.com/onegov/onegov-cloud/commit/7e72534569b7dfbbc2f3245cf3ffe1c9dab3d67b)

### Form

##### Improve error message for comment field indentation errors

`Feature` | [OGC-2311](https://linear.app/onegovcloud/issue/OGC-2311) | [36912ab924](https://github.com/onegov/onegov-cloud/commit/36912ab924f9bad4f3bc88bc39c8a602741e51fb)

### Landsgemeinde

##### Move print button

`Feature` | [OGC-2830](https://linear.app/onegovcloud/issue/OGC-2830) | [7a527a7780](https://github.com/onegov/onegov-cloud/commit/7a527a7780289f3887f582348ce3b37c4569aa18)

##### Removes inline javascript from templates

`Feature` | [OGC-2861](https://linear.app/onegovcloud/issue/OGC-2861) | [34b4446c7b](https://github.com/onegov/onegov-cloud/commit/34b4446c7b856e3c8874176263f64b8288c31ba7)

### Org

##### Allows extra fields to be displayed in occupancy view

Also slightly changes the order of values in the occupancy view so the
most important information is least likely to be visually cut off.

`Feature` | [OGC-2843](https://linear.app/onegovcloud/issue/OGC-2843) | [e8f1bfd8bf](https://github.com/onegov/onegov-cloud/commit/e8f1bfd8bf58a2eb10c71935a0b38d7605233789)

##### Makes reservation date filtering on payments/invoices more flexible

`Feature` | [OGC-2600](https://linear.app/onegovcloud/issue/OGC-2600) | [3e6cba29b6](https://github.com/onegov/onegov-cloud/commit/3e6cba29b64673c3c0b6d87d0ebf3776c9f0fc04)

##### Allows related tickets to be muted/unmuted from any related ticket

`Feature` | [OGC-2844](https://linear.app/onegovcloud/issue/OGC-2844) | [e2ea34a04b](https://github.com/onegov/onegov-cloud/commit/e2ea34a04b26f1c4f07dbbf862cc0ab1acb965ee)

##### Adds a tree select filter widget for payment/invoices

`Feature` | [OGC-2824](https://linear.app/onegovcloud/issue/OGC-2824) | [0ac1805858](https://github.com/onegov/onegov-cloud/commit/0ac1805858df97dcda18dcbf54c117cb36d3c357)

##### Allows allocations to define their own pricing

This serves use-cases like charging more for reservations on a weekend

`Feature` | [OGC-2768](https://linear.app/onegovcloud/issue/OGC-2768) | [1e50067e5d](https://github.com/onegov/onegov-cloud/commit/1e50067e5d3de845c84b4bd54ef4696d73930d27)

##### Removes inline javascript from the templates

This is preparation work for tightening up our Content-Security-Policy

`Feature` | [OGC-2864](https://linear.app/onegovcloud/issue/OGC-2864) | [ec68f8a057](https://github.com/onegov/onegov-cloud/commit/ec68f8a0570b0e143480bfb502b5f3e1be160574)

##### Video iFrame error

`Bugfix` | [OGC-2837](https://linear.app/onegovcloud/issue/OGC-2837) | [ae0da86876](https://github.com/onegov/onegov-cloud/commit/ae0da86876e95009f8369c9f9da2d3cad8ab71f5)

##### Fix bad redirect when rejecting reservation with comment

`Bugfix` | [OGC-2786](https://linear.app/onegovcloud/issue/OGC-2786) | [b54f36cf36](https://github.com/onegov/onegov-cloud/commit/b54f36cf360dffdcb2ba7ab23d89e3140460c285)

### Pas

##### Fixes by-effect of RIS refactoring on PAS.

Fixes commission edit form not having a save button.

`Bugfix` | [OGC-2847](https://linear.app/onegovcloud/issue/OGC-2847) | [9e98b030b6](https://github.com/onegov/onegov-cloud/commit/9e98b030b60ef9b73e39566b72a71302c80a186a)

##### Fixes dropdown syncing for commission presidents.

`Bugfix` | [OGC-2846](https://linear.app/onegovcloud/issue/OGC-2846) | [a42fd32358](https://github.com/onegov/onegov-cloud/commit/a42fd3235844b39968b570b84394b0faa9004274)

##### Fixes dropdown syncing for parliamentarians.

`Bugfix` | [OGC-2846](https://linear.app/onegovcloud/issue/OGC-2846) | [fc831a5829](https://github.com/onegov/onegov-cloud/commit/fc831a582977276ab99894fb9cbc59a13bae25c4)

### Ris

##### Multiple parliamentary groups can now be linked to a political business

`Feature` | [OGC-2816](https://linear.app/onegovcloud/issue/OGC-2816) | [fffb5c21b2](https://github.com/onegov/onegov-cloud/commit/fffb5c21b2c5a6324ca9e56b46c6a92603b46e4a)

##### Improve filename extraction, extension and file icon determination

`Bugfix` | [OGC-2813](https://linear.app/onegovcloud/issue/OGC-2813) | [eb0b0a9942](https://github.com/onegov/onegov-cloud/commit/eb0b0a9942992ccb8f7501360db3101ca90ed078)

### Town6

##### Adds a search field to the list of political businesses

`Feature` | [OGC-2836](https://linear.app/onegovcloud/issue/OGC-2836) | [5440ea7e83](https://github.com/onegov/onegov-cloud/commit/5440ea7e83618533c8380c394e55b98c0f85c980)

## 2025.67

`2025-11-27` | [98c33a124a...c4d2fbf0ed](https://github.com/OneGov/onegov-cloud/compare/98c33a124a^...c4d2fbf0ed)

### Feriennet

##### Make occasion location multi line

`Feature` | [OGC-1451](https://linear.app/onegovcloud/issue/OGC-1451) | [c1ca601070](https://github.com/onegov/onegov-cloud/commit/c1ca601070445ae1818150219988d8f331a72933)

##### Organizer text if username is not set

Resolves sentry issue https://seantis-gmbh.sentry.io/issues/7025105745/

`Bugfix` | [NONE](#NONE) | [98c33a124a](https://github.com/onegov/onegov-cloud/commit/98c33a124a0fede9464dc53de04a6324fd5a76e2)

### Org

##### Add option to add imagesets to resources

`Feature` | [OGC-2276](https://linear.app/onegovcloud/issue/OGC-2276) | [f858a0cd87](https://github.com/onegov/onegov-cloud/commit/f858a0cd87aa6694458b1433126f677febf17c0a)

##### Adds a content type filter to the search

`Feature` | [OGC-2834](https://linear.app/onegovcloud/issue/OGC-2834) | [9a52069202](https://github.com/onegov/onegov-cloud/commit/9a52069202b758b474e7c005b78d7c0a7578bc65)

##### Avoids crash in search for malicious queries

`Bugfix` | [ce796dcc24](https://github.com/onegov/onegov-cloud/commit/ce796dcc246fa317e17b9f352a8faf93d7e3dbcb)

##### Changes ticket link in occupancy view for all logged in members

`Bugfix` | [OGC-2781](https://linear.app/onegovcloud/issue/OGC-2781) | [3c83cc09e0](https://github.com/onegov/onegov-cloud/commit/3c83cc09e0e0f92e2d5bee3207f39e5fb4fb984f)

### Pas

##### Fixes a bug in plenary session attendance.

`Feature` | [OGC-2787](https://linear.app/onegovcloud/issue/OGC-2787) | [5ea0bf004c](https://github.com/onegov/onegov-cloud/commit/5ea0bf004cdf3af1f846f49f37709923b233eacd)

### Ris

##### Remove political business number from overview

`Feature` | [OGC-2818](https://linear.app/onegovcloud/issue/OGC-2818) | [fa559658b3](https://github.com/onegov/onegov-cloud/commit/fa559658b36a5dc0e9a2ea40bda83ecc33178f38)

### Search

##### Makes parliamentarians available in search results

Makes parliamentarians, commissions and parliamentary groups documents independent of its age

`Feature` | [OGC-2788](https://linear.app/onegovcloud/issue/OGC-2788) | [bef509a57d](https://github.com/onegov/onegov-cloud/commit/bef509a57d2d484fac4a21783cd01d4611c90584)

### Town6

##### Adds a search field to the tickets and tickets archive

`Feature` | [OGC-2460](https://linear.app/onegovcloud/issue/OGC-2460) | [5e0b58d6b8](https://github.com/onegov/onegov-cloud/commit/5e0b58d6b8dff7d1f0f84eb2b82259a38c5e2cef)

##### Display allocation rule title below actions

`Bugfix` | [OGC-2819](https://linear.app/onegovcloud/issue/OGC-2819) | [e64567c7cc](https://github.com/onegov/onegov-cloud/commit/e64567c7ccb31c561bd2c7e3c4e09b779ea12b9f)

### User

##### Avoids crash for some second factor authentication failures

`Bugfix` | [3f9a6e6d03](https://github.com/onegov/onegov-cloud/commit/3f9a6e6d035a14cf371f9e7e1bced913cc381018)

## 2025.66

`2025-11-21` | [c001eb871d...df97031e21](https://github.com/OneGov/onegov-cloud/compare/c001eb871d^...df97031e21)

### Feriennet

##### Banners

`Feature` | [PRO-1443](https://linear.app/projuventute/issue/PRO-1443) | [7a37fb75df](https://github.com/onegov/onegov-cloud/commit/7a37fb75dffcd7d2dade97583b942b7ffd6dec0d)

##### New Privacy Settings

Users can now decide themselves if their contact data is shown to other attendees of the same course.

`Feature` | [OGC-1415](https://linear.app/onegovcloud/issue/OGC-1415) | [eef7415188](https://github.com/onegov/onegov-cloud/commit/eef7415188972d4a4cd2db48b4e011fca4e18116)

##### Line break for occasion description

`Bugfix` | [PRO-1449](https://linear.app/projuventute/issue/PRO-1449) | [6b98614db6](https://github.com/onegov/onegov-cloud/commit/6b98614db64d05f52a27be967d2e86aea4084d6e)

### Org

##### Adds cli command to list resources

`Feature` | [OGC-2335](https://linear.app/onegovcloud/issue/OGC-2335) | [0a935fd78c](https://github.com/onegov/onegov-cloud/commit/0a935fd78c5a5dd9ce733daf82ef96d680f6e85b)

##### Reservation button

`Feature` | [OGC-2441](https://linear.app/onegovcloud/issue/OGC-2441) | [3ed6fa2867](https://github.com/onegov/onegov-cloud/commit/3ed6fa286762b50f4be78115192a0680425c59ad)

##### Change editbar_links for allocation settings

`Bugfix` | [OGC-2368](https://linear.app/onegovcloud/issue/OGC-2368) | [d3040df735](https://github.com/onegov/onegov-cloud/commit/d3040df7353081b8e97489f8c0283afe0c6721e2)

### Search

##### Index parliamentarians, commissions and parliamentary groups

`Feature` | [OGC-2788](https://linear.app/onegovcloud/issue/OGC-2788) | [352d6a93c2](https://github.com/onegov/onegov-cloud/commit/352d6a93c232c15ed6d6e80590b7466737fcda8f)

### Swissvotes

##### News labels

Some text changes

`Feature` | [SWI-64](https://linear.app/swissvotes/issue/SWI-64) | [411fedc985](https://github.com/onegov/onegov-cloud/commit/411fedc98549ff46cc9727127010f1ef27b14ba4)

### Town6

##### Unlink Resource from payment and invoice before deleting it

`Bugfix` | [OGC-2719](https://linear.app/onegovcloud/issue/OGC-2719) | [eeb3e22489](https://github.com/onegov/onegov-cloud/commit/eeb3e224891e292ac5805cea8e8b12a330b355d9)

##### Anchor distance

`Bugfix` | [OGC-2777](https://linear.app/onegovcloud/issue/OGC-2777) | [042ef0f258](https://github.com/onegov/onegov-cloud/commit/042ef0f2587811300bdb7389ea574c917ac5bb27)

## 2025.65

`2025-11-16` | [cb11e65b71...a53b5d5f13](https://github.com/OneGov/onegov-cloud/compare/cb11e65b71^...a53b5d5f13)

### Town

##### Fix file details not shown

`Bugfix` | [OGC-2784](https://linear.app/onegovcloud/issue/OGC-2784) | [1bf4dda93d](https://github.com/onegov/onegov-cloud/commit/1bf4dda93d8bb51a69b8b5dd3501a3332c6e2ad9)

### Town6

##### Fixes footer contact and opening hours label for feriennet

`Bugfix` | [OGC-2424](https://linear.app/onegovcloud/issue/OGC-2424) | [0acc673b40](https://github.com/onegov/onegov-cloud/commit/0acc673b40084bd897acd5b2d5d15657c5260d9a)

## 2025.64

`2025-11-13` | [12f9839782...af0f368d08](https://github.com/OneGov/onegov-cloud/compare/12f9839782^...af0f368d08)

### Assembly

##### Add print icons

`Feature` | [OGC-2711](https://linear.app/onegovcloud/issue/OGC-2711) | [e39e916367](https://github.com/onegov/onegov-cloud/commit/e39e91636775b844eee510ea495412e5dcb07b7b)

### Feriennet

##### Volunteer activities

Only show activities needing more volunteers

`Feature` | [OGC-1417](https://linear.app/onegovcloud/issue/OGC-1417) | [d65cc9be8b](https://github.com/onegov/onegov-cloud/commit/d65cc9be8bfc29ae557f7c1e0fccc59c8069746a)

### Landsgemeinde

##### Links in Sidebar for assembly items

`Feature` | [OGC-2714](https://linear.app/onegovcloud/issue/OGC-2714) | [ab1f6d31f6](https://github.com/onegov/onegov-cloud/commit/ab1f6d31f6cfa14139d553f0f6f2015e227f2ca9)

### Org

##### More specific error message

`Feature` | [OGC-2722](https://linear.app/onegovcloud/issue/OGC-2722) | [12f9839782](https://github.com/onegov/onegov-cloud/commit/12f98397820d5f5d81eb55b2865d2fd264178fbd)

##### Link ticket instead of reservation

`Bugfix` | [OGC-2779](https://linear.app/onegovcloud/issue/OGC-2779) | [90f21c0159](https://github.com/onegov/onegov-cloud/commit/90f21c015946526a5b833449c736cf1c7fa716c2)

### Pas

##### Prevents a bug in user synchronization with admins.

Admins can add themselves to commissions for testing purposes.
This would result in them having their account permissions
downgraded to parliamentarian or president, if we didn't add this.

`Bugfix` | [OGC-2783](https://linear.app/onegovcloud/issue/OGC-2783) | [8a97c24954](https://github.com/onegov/onegov-cloud/commit/8a97c24954e7acc4e66602e73c8d2ccb6d53c12f)

### Town6

##### Makes link label for contact information and opening hours configurable

The footer settings allow to configure the link labels

`Feature` | [OGC-2424](https://linear.app/onegovcloud/issue/OGC-2424) | [4f303b0cdc](https://github.com/onegov/onegov-cloud/commit/4f303b0cdcdd5111b7c16385936fae308d0c2d11)

## 2025.63

`2025-11-10` | [6a3efb41f9...bf9c16100d](https://github.com/OneGov/onegov-cloud/compare/6a3efb41f9^...bf9c16100d)

## 2025.62

`2025-11-07` | [d90bbc51b7...c296944343](https://github.com/OneGov/onegov-cloud/compare/d90bbc51b7^...c296944343)

### Core

##### Clears browser cache on user logout

This provides a small extra layer of protection, in case any sensitive
content accidentally ended up in the browser's cache.

`Feature` | [OGC-2745](https://linear.app/onegovcloud/issue/OGC-2745) | [93be9cbff0](https://github.com/onegov/onegov-cloud/commit/93be9cbff0a4f72cf0399a358fbb7b47982575a4)

### Feriennet

##### Display wishphase if it's not in the past

`Bugfix` | [OGC-1444](https://linear.app/onegovcloud/issue/OGC-1444) | [ff53601345](https://github.com/onegov/onegov-cloud/commit/ff536013458acfad310e10d511d935c3f98c97dc)

### Landsgemeinde

##### Additional Documents for assembly

`Feature` | [OGC-2699](https://linear.app/onegovcloud/issue/OGC-2699) | [0f94d3a43a](https://github.com/onegov/onegov-cloud/commit/0f94d3a43afb228ef5b41ed8cda5264e7fb6a734)

##### Assembly item creation Bugfix

`Bugfix` | [OGC-2696](https://linear.app/onegovcloud/issue/OGC-2696) | [8b5bfd1595](https://github.com/onegov/onegov-cloud/commit/8b5bfd15954a3d55511747be9cbcc678ea5d240d)

### Org

##### Lowers refresh interval for resource iCal to 30 minutes

`Feature` | [OGC-2548](https://linear.app/onegovcloud/issue/OGC-2548) | [d90bbc51b7](https://github.com/onegov/onegov-cloud/commit/d90bbc51b7be17b447275cfd9147a2fa379aa971)

##### Adds another ticket PDF option which includes related tickets

`Feature` | [OGC-2708](https://linear.app/onegovcloud/issue/OGC-2708) | [1609c54ef6](https://github.com/onegov/onegov-cloud/commit/1609c54ef6c684c3d3cbf277f372850d6453efdc)

##### Add subsubsubtitle and h5

`Feature` | [bdc5e9b5de](https://github.com/onegov/onegov-cloud/commit/bdc5e9b5de017f305b36bb80cab70e79a264e99a)

##### Newsletter just show lead

Add option to just show the lead text of the news items in the newsletters.

`Feature` | [OGC-2343](https://linear.app/onegovcloud/issue/OGC-2343) | [ffba57f239](https://github.com/onegov/onegov-cloud/commit/ffba57f2399fdd6ffe8cc9d54ae9d94597ea0679)

##### Content Sidepanel

Option to define how many levels are displayed in the TOC-Sidepanel.

`Feature` | [OGC-2715](https://linear.app/onegovcloud/issue/OGC-2715) | [698fb15f40](https://github.com/onegov/onegov-cloud/commit/698fb15f405b5e04003c93ab9d51e1a6e05b208b)

##### Rename dashboard to overview

`Feature` | [OGC-2728](https://linear.app/onegovcloud/issue/OGC-2728) | [348e70a641](https://github.com/onegov/onegov-cloud/commit/348e70a641b744a3f9090497c1a873d93baff6e3)

##### Attaches reservations summary PDF to reservation acceptance mail

`Feature` | [OGC-2765](https://linear.app/onegovcloud/issue/OGC-2765) | [5d75b5d66b](https://github.com/onegov/onegov-cloud/commit/5d75b5d66be40defac0e5632516600d30dea8b4a)

##### Fixes reservation dates not being linked for migrated invoices

`Bugfix` | [OGC-2767](https://linear.app/onegovcloud/issue/OGC-2767) | [0d9d4c8ee2](https://github.com/onegov/onegov-cloud/commit/0d9d4c8ee2b68fd074acafd2d6c3750b99c057fa)

### Pas

##### Adds cronjob to sync parliamentarians and `User` accounts.

`Feature` | [OGC-2725](https://linear.app/onegovcloud/issue/OGC-2725) | [38ef00156a](https://github.com/onegov/onegov-cloud/commit/38ef00156a2734a2f3b9559f08f4b40bc38469a5)

### Ris

##### Properly handle interest ties for new parliamentarians

`Feature` | [OGC-2766](https://linear.app/onegovcloud/issue/OGC-2766) | [f5b2b91246](https://github.com/onegov/onegov-cloud/commit/f5b2b912462299ac037fbe7a5926d717a8ec5b25)

##### Cleanup unused relationships

They got replaced with relationships to meeting items

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [d2f1272a27](https://github.com/onegov/onegov-cloud/commit/d2f1272a27a23963b2724c12cda7b17ded5706c2)

### Town6

##### Adds unit tests for political businesses views

`Feature` | [OGC-2481](https://linear.app/onegovcloud/issue/OGC-2481) | [5471bbd824](https://github.com/onegov/onegov-cloud/commit/5471bbd8248f71f568ef0e769353e0543655ea4c)

##### Adds unit tests for parliamentarian views including parliamentary group and commission

`Feature` | [OGC-2381](https://linear.app/onegovcloud/issue/OGC-2381) | [fce241c9be](https://github.com/onegov/onegov-cloud/commit/fce241c9bef6d43496d20c6f176851f657366e73)

##### Prefer `reply_to` in template over general email.

`Feature` | [OGC-2671](https://linear.app/onegovcloud/issue/OGC-2671) | [4637af1a54](https://github.com/onegov/onegov-cloud/commit/4637af1a540e574e93597f1b0de4cb52def750bf)

### User

##### Adds validation against a list of commonly used passwords

`Feature` | [OGC-2737](https://linear.app/onegovcloud/issue/OGC-2737) | [a048ece0af](https://github.com/onegov/onegov-cloud/commit/a048ece0afad0cffeb90d246c6a33c9733361e75)

## 2025.61

`2025-11-03` | [93a5f5203e...c79c709d87](https://github.com/OneGov/onegov-cloud/compare/93a5f5203e^...c79c709d87)

### Feriennet

##### Update banners.

`Feature` | [PRO-1437](https://linear.app/projuventute/issue/PRO-1437) | [ec5e2ff043](https://github.com/onegov/onegov-cloud/commit/ec5e2ff043644e0577e03e764e3c3c5dec59c03e)

### File

##### Adds `X-Content-Type-Options: nosniff` header to uploaded files

`Feature` | [OGC-2750](https://linear.app/onegovcloud/issue/OGC-2750) | [44b9456cba](https://github.com/onegov/onegov-cloud/commit/44b9456cbac23dc726941fcaf1c13485f238acf7)

##### Switches to `Content-Disposition: attachment` for most uploads

There's only really a small list of content types we want to serve
inline, such as images, videos and PDF files, we continue to serve
them inline and serve everything else as attachments.

`Bugfix` | [OGC-2733](https://linear.app/onegovcloud/issue/OGC-2733) | [8eb56af3c1](https://github.com/onegov/onegov-cloud/commit/8eb56af3c1b2642a30a499dd04ecf27bae752960)

### Org

##### Adds a my reservations PDF to the ticket list for RSV tickets

`Feature` | [OGC-2756](https://linear.app/onegovcloud/issue/OGC-2756) | [5ac8e0bd32](https://github.com/onegov/onegov-cloud/commit/5ac8e0bd323f51be7e3a970472562d9ce2fb8a7e)

##### Invalidates related TANs after authentication

This also decreases the validity period of mTANs used as a second factor

`Bugfix` | [OGC-2749](https://linear.app/onegovcloud/issue/OGC-2749) | [bb3782adb9](https://github.com/onegov/onegov-cloud/commit/bb3782adb99a2af293213e2cc1ebc7e5a32e710c)

##### Fixes crash in `file-links` template macro

`Bugfix` | [54e794bac3](https://github.com/onegov/onegov-cloud/commit/54e794bac36555d9adc1ba36e971a814984f2b06)

##### Uses a more sensible column as the `fts_id` for `ExternalLink`

`Bugfix` | [e7210a3096](https://github.com/onegov/onegov-cloud/commit/e7210a309647df9fade4e4ea8269b27b7befb2af)

##### Fixes invisible partitions in reservation calendar

`Bugfix` | [OGC-2764](https://linear.app/onegovcloud/issue/OGC-2764) | [c07ac95a1d](https://github.com/onegov/onegov-cloud/commit/c07ac95a1ddfb6a2eaa1be97a79bcbdde362635f)

### Search

##### Integrates indexer into transaction workflow with a data manager

This also refactors some code that relied on the old indexer behavior

`Feature` | [OGC-2759](https://linear.app/onegovcloud/issue/OGC-2759) | [24b68fba31](https://github.com/onegov/onegov-cloud/commit/24b68fba316962aa50edfb6870599eaa48efa6e4)

### Town6

##### Fixes empty links still rendered due to `populate_obj`.

`Bugfix` | [OGC-2761](https://linear.app/onegovcloud/issue/OGC-2761) | [835976629e](https://github.com/onegov/onegov-cloud/commit/835976629e8bebedf5fb67493e164e1b6b306a1c)

### User

##### Raises minimum password length from 8 to 10

`Feature` | [OGC-2736](https://linear.app/onegovcloud/issue/OGC-2736) | [2948b7da2e](https://github.com/onegov/onegov-cloud/commit/2948b7da2eb63a367f541cd38dd075f83e6d535d)

## 2025.60

`2025-10-24` | [7136036d60...4b63568190](https://github.com/OneGov/onegov-cloud/compare/7136036d60^...4b63568190)

### Search

##### Only processes indexer queue on the main thread

`Bugfix` | [7136036d60](https://github.com/onegov/onegov-cloud/commit/7136036d60d622f20ab80d98d309bc81481d45e3)

## 2025.59

`2025-10-24` | [bcafc9a898...ca05b98a32](https://github.com/OneGov/onegov-cloud/compare/bcafc9a898^...ca05b98a32)

### Search

##### Avoids potentially leaking connections within the indexer

`Bugfix` | [bcafc9a898](https://github.com/onegov/onegov-cloud/commit/bcafc9a89878970d7a6f4c173081ee0702a763b2)

##### Also disposes the indexer engine at the end just to be sure.

`Bugfix` | [98bce20025](https://github.com/onegov/onegov-cloud/commit/98bce200258276f06ad7068d33c1c16fedb7648c)

## 2025.58

`2025-10-24` | [3a7d6284d7...bca98ed899](https://github.com/OneGov/onegov-cloud/compare/3a7d6284d7^...bca98ed899)

## 2025.57

`2025-10-24` | [a92f06950b...d1e1b4df2c](https://github.com/OneGov/onegov-cloud/compare/a92f06950b^...d1e1b4df2c)

### Core

##### Changes default for `email_validator.CHECK_DELIVERABILITY`

We both use this validator directly and indirectly through WTForms.
However WTForms uses its own defaults for `check_deliverability` which
is different from `email_validator.CHECK_DELIVERABILITY`. This change
harmonizes the two defaults and avoids unnecessary I/O overhead.

`Bugfix` | [OGC-2494](https://linear.app/onegovcloud/issue/OGC-2494) | [91f31d08fb](https://github.com/onegov/onegov-cloud/commit/91f31d08fb4e5aeadeb428b64883dc38cb49f238)

### Landsgemeinde

##### Fix InDesign Import

`Bugfix` | [OGC-2683](https://linear.app/onegovcloud/issue/OGC-2683) | [ff0f061aaf](https://github.com/onegov/onegov-cloud/commit/ff0f061aafd591e035c559881efe966e7b4a8bdf)

##### Improves search results and suggestions

`Bugfix` | [OGC-2695](https://linear.app/onegovcloud/issue/OGC-2695) | [6bb53b3ee3](https://github.com/onegov/onegov-cloud/commit/6bb53b3ee310aff30dea160f6bcfac09031925e6)

##### Add content-sidebar for assembly items

`Bugfix` | [OGC-2698](https://linear.app/onegovcloud/issue/OGC-2698) | [87a1e60828](https://github.com/onegov/onegov-cloud/commit/87a1e608282e5177daced0611764765b100e00fb)

### Org

##### Increases batch size for invoice and ticket paginations

`Feature` | [OGC-2687](https://linear.app/onegovcloud/issue/OGC-2687) | [89218d1ad8](https://github.com/onegov/onegov-cloud/commit/89218d1ad8f8a9cef626d87f20820aadad942fc7)

##### Allows multiple ticket categories for filtering invoices/payments

`Feature` | [OGC-2703](https://linear.app/onegovcloud/issue/OGC-2703) | [bcc780577b](https://github.com/onegov/onegov-cloud/commit/bcc780577be5e40062a8b87df41ae32ff28ff03b)

##### Only considers last reservation in date filter in payments/invoices

This allows a cleaner separation of invoicing periods, since every
invoice / payment will have one reference date, instead of a range which
could partially overlap and cause it to show up in multiple periods.

`Feature` | [OGC-2704](https://linear.app/onegovcloud/issue/OGC-2704) | [b68c68c85c](https://github.com/onegov/onegov-cloud/commit/b68c68c85c0afdd1ab37e8a756821f9bb78fc95a)

##### Change internal link to use a searchable dropdown in editor.

`Feature` | [OGC-2351](https://linear.app/onegovcloud/issue/OGC-2351) | [58ef8b671b](https://github.com/onegov/onegov-cloud/commit/58ef8b671ba1a9c9e8c531317aa4c79ee915b611)

##### Displays selected filters in ticket invoice pdf export

`Feature` | [OGC-2702](https://linear.app/onegovcloud/issue/OGC-2702) | [648f6d15ba](https://github.com/onegov/onegov-cloud/commit/648f6d15ba3496138a55fa03d7f74b3665bda885)

##### Adds a filter for invoices with positive net amounts

`Feature` | [OGC-2701](https://linear.app/onegovcloud/issue/OGC-2701) | [3ed6d5c5fb](https://github.com/onegov/onegov-cloud/commit/3ed6d5c5fb0eeea2a5331633729f81ed274cf9a2)

##### Removes some of the now redundant payment list functionality

This functionality should be better served by the invoice list

`Feature` | [OGC-2705](https://linear.app/onegovcloud/issue/OGC-2705) | [bc9461cc57](https://github.com/onegov/onegov-cloud/commit/bc9461cc57c7253beef5d2e5c2ea98708a6673da)

##### Shows related tickets that were created as part of the same order

`Feature` | [OGC-2691](https://linear.app/onegovcloud/issue/OGC-2691) | [29e9a1c295](https://github.com/onegov/onegov-cloud/commit/29e9a1c2958cf5fa1f9b93604771a77d989a118c)

##### Increases visible date range for resource iCal

`Feature` | [OGC-2710](https://linear.app/onegovcloud/issue/OGC-2710) | [bd4a7865ee](https://github.com/onegov/onegov-cloud/commit/bd4a7865ee589065f679500e7eb06ca0f264cba3)

##### Adds a PDF export to my reservations with customizable date range

`Feature` | [OGC-2157](https://linear.app/onegovcloud/issue/OGC-2157) | [1b8001843d](https://github.com/onegov/onegov-cloud/commit/1b8001843dc92cadcf6a928ac57f2cc5f4337cd4)

##### Option to hide submitter email

`Feature` | [OGC-2654](https://linear.app/onegovcloud/issue/OGC-2654) | [a490f6c9c5](https://github.com/onegov/onegov-cloud/commit/a490f6c9c515604ca73f533792909f51a1f259f7)

##### Avoids sending empty daily newsletters

`Bugfix` | [OGC-2706](https://linear.app/onegovcloud/issue/OGC-2706) | [72aa08883f](https://github.com/onegov/onegov-cloud/commit/72aa08883f4a695e252943486f4fedfb66f0564c)

### Pas

##### Adds option in cli to sync just one user account.

`Feature` | [d498e1f823](https://github.com/onegov/onegov-cloud/commit/d498e1f823228037957130b35ca846be7123dda9)

##### Fixes translation.

`Bugfix` | [aa378ebfc0](https://github.com/onegov/onegov-cloud/commit/aa378ebfc0278b721b2bcd9564a0258fdb84a9f7)

##### Fixes issue where parliamentarian choices were not limited.

`Bugfix` | [eeb492a63f](https://github.com/onegov/onegov-cloud/commit/eeb492a63fc68d773c77919d181638833292f2e9)

##### Log 404 errors as warnings instead of errors in Kub api.

In sync, test users legitimately hit 404 response, triggering
Sentry alerts — these shouldn't be treated as errors requiring
investigation.

`Bugfix` | [96db52c8f5](https://github.com/onegov/onegov-cloud/commit/96db52c8f5bd7546b247d47bca0553c7b0060b94)

##### Log API check failures as warnings instead of errors

When the KUB API is temporarily unavailable during cronjob imports,
the API accessibility check raises RuntimeError, triggering Sentry
alerts

Builds on 96db52c8 which handled 404 errors for individual records.

`Bugfix` | [9ee85b6542](https://github.com/onegov/onegov-cloud/commit/9ee85b6542379cda7239a56784586cae9001d327)

### Search

##### Removes ElasticSearch integration

`Feature` | [OGC-1017](https://linear.app/onegovcloud/issue/OGC-1017) | [1f53cc147d](https://github.com/onegov/onegov-cloud/commit/1f53cc147d8ac35408d1580c8c825241724559eb)

##### Makes upgrade task more robust

`Bugfix` | [20bf43aeb7](https://github.com/onegov/onegov-cloud/commit/20bf43aeb7b7bf96adb3636ceecdfce25d3d6313)

### Ticket

##### Be a bit more robust in upgrade task.

This is a classic upgrade task ordering problem where
the ORM model has been updated but the database schema
hasn't been migrated yet. Only happened locally:

`sqlalchemy.exc.ProgrammingError:
(psycopg2.errors.UndefinedColumn) column tickets.closed_on
does not exist`

`Other` | [f8955ffa68](https://github.com/onegov/onegov-cloud/commit/f8955ffa68901cb150624cf24bcac858292211f0)

### Town6

##### Automatically subscribe new parliamentarians to newsletters

`Feature` | [OGC-2621](https://linear.app/onegovcloud/issue/OGC-2621) | [f82516e3f9](https://github.com/onegov/onegov-cloud/commit/f82516e3f9adb484388ec2c33ccb240a949cd306)

##### Lead text for iFrames

`Feature` | [OGC-2367](https://linear.app/onegovcloud/issue/OGC-2367) | [2c32002bfc](https://github.com/onegov/onegov-cloud/commit/2c32002bfc009fc56b9407bbeef5cad00376bcc2)

##### Custom text above footer for Form mails

`Feature` | [OGC-2467](https://linear.app/onegovcloud/issue/OGC-2467) | [e6a9cc4f24](https://github.com/onegov/onegov-cloud/commit/e6a9cc4f245ab73db00703bc713b19d01929dc3c)

##### Reservation Quota

`Bugfix` | [OGC-2681](https://linear.app/onegovcloud/issue/OGC-2681) | [a92f06950b](https://github.com/onegov/onegov-cloud/commit/a92f06950bcb8d9e12ba93d993a3c8378508ec48)

##### Only show dropdown if there is any public resource

`Bugfix` | [OGC-2680](https://linear.app/onegovcloud/issue/OGC-2680) | [15d32ef710](https://github.com/onegov/onegov-cloud/commit/15d32ef71049fa67be063a43a6ad672611309574)

##### Avoids including non-public directory entries in API

`Bugfix` | [OGC-2723](https://linear.app/onegovcloud/issue/OGC-2723) | [a4e9e415c1](https://github.com/onegov/onegov-cloud/commit/a4e9e415c13f5ff9ec21732596d3889286f0ca6d)

