# Changes

## Release `2019.19`

> commits: **4 / [75f6dd1a4c...c2014f3002](https://github.com/OneGov/onegov-cloud/compare/75f6dd1a4c^...c2014f3002)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.19)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🎉 **Adds WYSIWYG Editor for agency portrait**

Supports html in agency portrait and export to pdf (except of images).

**`Feature`** | **[c2014f3002](https://github.com/onegov/onegov-cloud/commit/c2014f3002d623817cc1f570dc597cff302ef77d)**

### Election-Day

🐞 **Fixes handling of panachage results**

Introduces FileImportError if any `{id}` from `panachage_result_from_{id}` list not in one of the `list_id`/'id' for wabsti and internal api format.

**`Bugfix`** | **[75f6dd1a4c](https://github.com/onegov/onegov-cloud/commit/75f6dd1a4c458c5df678348210a2adbf68038bb0)**

### Feriennet

🐞 **Fixes custom error for insufficient funds**

The error message was not shown as expected.

**`Bugfix`** | **[ONEGOV-CLOUD-356](https://sentry.io/organizations/seantis-gmbh/issues/?query=ONEGOV-CLOUD-356)** | **[e11ac602fc](https://github.com/onegov/onegov-cloud/commit/e11ac602fcae5e92b6c804ca5e780eff036e9482)**

## Release `2019.18`

> released: **2019-09-23 11:44**<br>
> commits: **4 / [0b45b544e6...18a54e46fe](https://github.com/OneGov/onegov-cloud/compare/0b45b544e6^...18a54e46fe)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.18)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🐞 **Fixes stale-connection error in LDAP client**

The LDAP client would raise an error after a certain idle-period. Once
that happened, the client would not reconnect to the server until the
process was restartet.

**`Bugfix`** | **[c8a1cce2d5](https://github.com/onegov/onegov-cloud/commit/c8a1cce2d504fde438fd3e49559572a918d4eecd)**

### Core

🐞 **Disable SameSite=Lax for Safari 12.x**

Safari 12.x has some issues with SameSite=Lax, preventing the storage of
cookies on certain environment (mainly in development). As a work
around, this change disables SameSite for this specific browser.

**`Bugfix`** | **[0b45b544e6](https://github.com/onegov/onegov-cloud/commit/0b45b544e653ec1424ae4cdbd87e20c8846ab0eb)**

### Feriennet

🎉 **Adds a booking phase date, anytime cancellations**

Implements two seperate issues that largely touch the same lines of
code. Bringing the following improvements:

* Periods now hold an explicit booking phase date-range
* Admins may now book outside the booking phase
* Admins may now cancel bookings even if they have been billed

**`Feature`** | **[FER-783](https://issues.seantis.ch/browse/FER-783)** | **[aa122cc81c](https://github.com/onegov/onegov-cloud/commit/aa122cc81c4806e8cf37b9dc4f343bc2a3020fcc)**

## Release `2019.17`

> released: **2019-09-19 11:27**<br>
> commits: **11 / [d37cb83d40...c1168ff4c9](https://github.com/OneGov/onegov-cloud/compare/d37cb83d40^...c1168ff4c9)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.17)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🐞 **Fixes display of list mandates for intermediate results for election proporz**

**`Bugfix`** | **[9345406de5](https://github.com/onegov/onegov-cloud/commit/9345406de5bc811a1f0116d61793d18374cf1b35)**

🐞 **Fixes roundtrip, re-organizes tests and fixture data loading**

- list_id can be alphanumeric, change that for all apis to evade roundtrip problems
- Reorganizes sample data into folder strukture like `/domain/principal/{api_format}_{type}.tar.gz` instead of using a flat hierarchy.
- Adds an import_test_dataset fixture to instantiate model object and then load result data from the fixtures folder.

**`Bugfix`** | **[fdeeb69c67](https://github.com/onegov/onegov-cloud/commit/fdeeb69c67130fbb0b15dc0232a86572390e3f8e)**

### User

✨ **Adds removal to change-yubikey command**

To remove a yubikey from an account through the onegov-user
change-yubikey command, one can now simply enter an empty yubikey. This
results in the same behaviour already present in `onegov-user add`.

**`Other`** | **[8ab40dc73c](https://github.com/onegov/onegov-cloud/commit/8ab40dc73ca1b26348cfbd98c531cbf9566ddbb0)**

## Release `2019.16`

> released: **2019-09-13 10:56**<br>
> commits: **2 / [9ab37eddeb...a78362e65e](https://github.com/OneGov/onegov-cloud/compare/9ab37eddeb^...a78362e65e)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.16)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Adds file datamanager cross-fs support**

The file datamanager for transactions assumed that temp files were on
the same filesystem as the final target files. With containers this is
definitely no longer true (/tmp is usually mounted as tmpfs). This patch
fixes this problem by falling back to a copy/delete approach.

**`Bugfix`** | **[ONEGOV-CLOUD-37W](https://sentry.io/organizations/seantis-gmbh/issues/?query=ONEGOV-CLOUD-37W)** | **[9ab37eddeb](https://github.com/onegov/onegov-cloud/commit/9ab37eddeb1b05de459c987ff7b65510cca86510)**

## Release `2019.15`

> released: **2019-09-13 10:15**<br>
> commits: **3 / [7ee8f0b3ed...4b3c372d2e](https://github.com/OneGov/onegov-cloud/compare/7ee8f0b3ed^...4b3c372d2e)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.15)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Activates LDAP integration for onegov.wtfs**

The integration works the exact same way as the one in onegov.org.

**`Feature`** | **[098fb14721](https://github.com/onegov/onegov-cloud/commit/098fb14721ad2676623d0b8439a461f92d8d5f9e)**

### Formcode

🐞 **Fixes empty fieldsets causing an error**

It is perfectly valid to create empty fieldsets in formcode (though
non-sensical). Unfortunately this caused an error until this commit.

**`Bugfix`** | **[ONEGOV-CLOUD-37S](https://sentry.io/organizations/seantis-gmbh/issues/?query=ONEGOV-CLOUD-37S)** | **[7ee8f0b3ed](https://github.com/onegov/onegov-cloud/commit/7ee8f0b3eddd48ea9c69badfe65f7912c48d8efb)**

## Release `2019.14`

> released: **2019-09-12 15:42**<br>
> commits: **7 / [8bf89eafbb...12cd043598](https://github.com/OneGov/onegov-cloud/compare/8bf89eafbb^...12cd043598)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.14)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Enable insecure LDAP connections**

It would be great if we could limit ourselves to LDAPS, but not all IT
departments support this configuration.

**`Feature`** | **[b8c8650179](https://github.com/onegov/onegov-cloud/commit/b8c86501797b63c43ab1e205d9fa8af7fd9b263c)**

✨ **Increases resilience for LDAP**

LDAP connections should now automatically be re-established if the
server disconnects the client.

**`Other`** | **[cc61f23864](https://github.com/onegov/onegov-cloud/commit/cc61f23864be708d8d6818ad757865145b3c51b2)**

✨ **Use auto-login on all pages if activated**

It is preferrable to be always logged-in, rather than having an escape
hatch.

**`Other`** | **[e951b53be8](https://github.com/onegov/onegov-cloud/commit/e951b53be8e7cab5e8818beca14cb931a18501d4)**

### Feriennet

🐞 **Fixes my-bills raising an exception**

When periods existed, but none of them were active, the "My Bills" view
would throw an exception.

**`Bugfix`** | **[8bf89eafbb](https://github.com/onegov/onegov-cloud/commit/8bf89eafbb5b30cc1550842484ff1d46b6b4b90f)**

## Release `2019.13`

> released: **2019-09-11 11:33**<br>
> commits: **6 / [226c3dd0ff...3646bae845](https://github.com/OneGov/onegov-cloud/compare/226c3dd0ff^...3646bae845)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.13)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🐞 **Fixes Kerberos handshake not working**

The handshake would only work if it had been successful before.

**`Bugfix`** | **[81517c6abe](https://github.com/onegov/onegov-cloud/commit/81517c6abe145afe2dc53df7b15f126adf086068)**

### Election-Day

🎉 **Corrects calculation of total votes in one election**

Provides new widgets, mostly tables that can be used a `<iframe>`

**`Feature`** | **[1b4c135343](https://github.com/onegov/onegov-cloud/commit/1b4c135343d7c68e7307e2fbf42ee1078d6d22ac)**

🐞 **Fixes calculation of total list votes for aggr. lists api**

For the aggregated lists api, we deliver the % of `list_votes / total_votes` for one election in aggregated form. `total_votes` is now aggregated as the total of all `list_votes` across all lists rather than aggregated from `ElectionResults` as a function using counting valid - invalid - blank votes etc. It adds a couple of more fields to the api to directly evaluate if the results are correct.

**`Bugfix`** | **[088d466583](https://github.com/onegov/onegov-cloud/commit/088d466583d071807adab92be8ebeb00d5da247d)**

## Release `2019.12`

> released: **2019-09-10 13:29**<br>
> commits: **3 / [cc133b91bc...770c2a73dc](https://github.com/OneGov/onegov-cloud/compare/cc133b91bc^...770c2a73dc)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.12)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🏎 **Improves Stripe payment synchronisation**

Stripe payments syncs were terribly slow, producing way too many
queries, grinding the production server to a halt.

With this update Stripe payments syncs are still amongst our slower
views, but with a runtime of < 10s on large databases, we are now
looking at reasonable numbers.

**`Performance`** | **[FER-791](https://issues.seantis.ch/browse/FER-791)** | **[cc133b91bc](https://github.com/onegov/onegov-cloud/commit/cc133b91bc2fa8e133eccdfcb48fcfe1634c5b41)**

## Release `2019.11`

> released: **2019-09-09 12:48**<br>
> commits: **5 / [b4ca9c0722...ef7ec74cd8](https://github.com/OneGov/onegov-cloud/compare/b4ca9c0722^...ef7ec74cd8)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.11)](https://buildkite.com/seantis/onegov-cloud)

### Search

✨ **Improves search resilience**

Elasticsearch is not guaranteed to be in sync with our database. The
server might also not be available or all data may be temporarily gone.

We have of course been aware of this and have counter-measures in the
code. However there were some loopholes which should now be closed.

Apart from the search not being available, the user should not see
any error messages anymore at this point.

**`Other`** | **[6cbf703c64](https://github.com/onegov/onegov-cloud/commit/6cbf703c64f86e322b9df00292e6529d33753546)**

## Release `2019.10`

> released: **2019-09-06 16:11**<br>
> commits: **2 / [ac565ca225...ba85af9184](https://github.com/OneGov/onegov-cloud/compare/ac565ca225^...ba85af9184)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.10)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Adds api endpoint with aggregated information for national council elections**

The endpoint is available under the url `/election/eample/data-aggregated-lists`.

**`Feature`** | **[ac565ca225](https://github.com/onegov/onegov-cloud/commit/ac565ca22590faf46e01f8325bd5f52833ff7a97)**

## Release `2019.9`

> released: **2019-09-06 15:09**<br>
> commits: **4 / [3e406aeb3c...3c9b101357](https://github.com/OneGov/onegov-cloud/compare/3e406aeb3c^...3c9b101357)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.9)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Adds app-specific role maps for LDAP**

Without this change all applications whould share the same role map,
which is too limiting for the general OneGov Cloud use.

**`Feature`** | **[3e406aeb3c](https://github.com/onegov/onegov-cloud/commit/3e406aeb3c59e258e309f260cc525d77cb508dcd)**

## Release `2019.8`

> released: **2019-09-06 12:43**<br>
> commits: **2 / [a728bf78f8...75d00e69fc](https://github.com/OneGov/onegov-cloud/compare/a728bf78f8^...75d00e69fc)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.8)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Integrates Kerberos/LDAP**

A new authentication provider provides LDAP authentication together with Kerberos. The request is authenticated by Kerberos (providing a username), the user authorised by LDAP.

**`Feature`** | **[a728bf78f8](https://github.com/onegov/onegov-cloud/commit/a728bf78f8a2025e3b63ff4db3fe2b7342ceed91)**

## Release `2019.7`

> released: **2019-09-05 17:40**<br>
> commits: **8 / [64c5f5bdfb...f48727bc88](https://github.com/OneGov/onegov-cloud/compare/64c5f5bdfb^...f48727bc88)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.7)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Fixes relative dates throwing an error**

Arrow recently started supporting weeks, however it did not provide a
translation yet, which lead to an exception.

**`Bugfix`** | **[80af30dfe4](https://github.com/onegov/onegov-cloud/commit/80af30dfe4ac3672772618ff86134c10e9351e19)**

### Gis

✨ **Removes ZugMap Ortsplan**

This map type is being phased out and is therefore no longer supported.

**`Other`** | **[ZW-125](https://kanton-zug.atlassian.net/browse/ZW-125)** | **[148cb2c74d](https://github.com/onegov/onegov-cloud/commit/148cb2c74d92236feba6c562ef914c53f3b36a3b)**

### Org

🐞 **Fixes wrong phone number link**

The phone number was linkified twice, which resulted in invalid HTML
being generated and displayed in the directory contact.

**`Bugfix`** | **[ZW-233](https://kanton-zug.atlassian.net/browse/ZW-233)** | **[64c5f5bdfb](https://github.com/onegov/onegov-cloud/commit/64c5f5bdfbde1891b391d0f67496904bdbc928df)**

## Release `2019.6`

> released: **2019-09-04 10:24**<br>
> commits: **2 / [0d57b12204...3d53d3b4b9](https://github.com/OneGov/onegov-cloud/compare/0d57b12204^...3d53d3b4b9)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.6)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

✨ **Hide intermediate results for elections and votes**

Hides clear statuses such as elected or number of mandates per list for proporz election if election is not final.

**`Other`** | **[0d57b12204](https://github.com/onegov/onegov-cloud/commit/0d57b122040a9e883735a56d40d891430bae3c10)**

## Release `2019.5`

> released: **2019-09-04 06:04**<br>
> commits: **14 / [326bab40a2...a8937ba123](https://github.com/OneGov/onegov-cloud/compare/326bab40a2^...a8937ba123)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.5)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🎉 **Improved PDF rendering, solving Link caching**

Features new page break settings where PDF Layout can be chosen. Fixes link caching especially on Firefox by generating unique links for agency pdf's on creation and links based on modified timestamp for root.pdf (and poeple Excel File as well).

**`Feature`** | **[ZW-200](https://kanton-zug.atlassian.net/browse/ZW-200)** | **[2410ee7ab7](https://github.com/onegov/onegov-cloud/commit/2410ee7ab715fcc956c2c49ec72016fe5219eef8)**

### Town

✨ **Hide signature verification for anonymous**

Only logged-in users are now able to see the verification widget - it
seems that the public is more confused by this than anything.

**`Other`** | **[326bab40a2](https://github.com/onegov/onegov-cloud/commit/326bab40a2d6870af9f1b84f204f493dc34a32a0)**

## Release `2019.4`

> released: **2019-08-30 15:31**<br>
> commits: **11 / [5c3adde749...282ed75f8e](https://github.com/OneGov/onegov-cloud/compare/5c3adde749^...282ed75f8e)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.4)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🎉 **Adds excel export for people and their memberships**

Adds Excel export for people and their memberships and download link for logged in users.
Addition: Fixes static `page_break_on_levle` in `views/agencies.py` for root and org pdf.

**`Feature`** | **[STAKA-15](https://ogc-ar.atlassian.net/projects/STAKA/issues/STAKA-15)** | **[4191ba6e06](https://github.com/onegov/onegov-cloud/commit/4191ba6e0611c38a743b488e5fe7294bbf9d2151)**

### Core

✨ **Improves Sentry integration**

All filtering now happens on sentry.io and we enabled the Redis and
SQLAlchemy integrations for Sentry.

**`Other`** | **[4313c2d546](https://github.com/onegov/onegov-cloud/commit/4313c2d546b2232f1aab6df4376c329c36385047)**

### Feriennet

🎉 **Adds custom error for insufficient funds**

Resolves #1

**`Feature`** | **[1](https://github.com/onegov/onegov-cloud/issues/1)** | **[cc0ad2475c](https://github.com/onegov/onegov-cloud/commit/cc0ad2475c9ec57c29d9c491897e3f296f8a7ac7)**

🐞 **Fixes donations not working**

Regular users were unable to make donations due to an infinite redirect.

**`Bugfix`** | **[5e5a05eddb](https://github.com/onegov/onegov-cloud/commit/5e5a05eddb47bc13d95c40d41fddcaec562fcadf)**

### Winterthur

🐞 **Fixes wrong formatting of percentages**

The daycare subsidy calculator "rounded" percentage of '10.00' to '1'.

**`Bugfix`** | **[FW-63](https://stadt-winterthur.atlassian.net/browse/FW-63)** | **[7b0f07f86a](https://github.com/onegov/onegov-cloud/commit/7b0f07f86a3221d0de26adb6e1922bff46d73048)**

✨ **Removes pricacy notice.**

It is now renderd outside our iFrame.

**`Other`** | **[FW-69](https://stadt-winterthur.atlassian.net/browse/FW-69)** | **[1d9a695a06](https://github.com/onegov/onegov-cloud/commit/1d9a695a068021ffca8a8e44481cf188c854c7fe)**

## Release `2019.3`

> released: **2019-08-29 09:39**<br>
> commits: **5 / [36ebdbfa71...4633aeb348](https://github.com/OneGov/onegov-cloud/compare/36ebdbfa71^...4633aeb348)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.3)](https://buildkite.com/seantis/onegov-cloud)

### Core

🎉 **Adds `onegov.core.__version__`**

This version identifier always contains the current version of the
container. During development this information may be stale, as the
version is only updated during the release process.

**`Feature`** | **[b2f4f16f61](https://github.com/onegov/onegov-cloud/commit/b2f4f16f614ad690b8eb5c222b1881a677d1e323)**

## Release `2019.2`

> released: **2019-08-28 10:04**<br>
> commits: **6 / [69399e0e7a...50afe830eb](https://github.com/OneGov/onegov-cloud/compare/69399e0e7a^...50afe830eb)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.2)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🐞 **Fixes bug in validate_integer(line, 'stimmen') in wmkandidaten_gde**

**`Bugfix`** | **[75dcf68244](https://github.com/onegov/onegov-cloud/commit/75dcf68244b1cc836fee5a5f27303536819a5720)**

## Release `2019.1`

> released: **2019-08-27 14:22**<br>
> commits: **19 / [53849be4fe...cc3764630e](https://github.com/OneGov/onegov-cloud/compare/53849be4fe^...cc3764630e)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.1)](https://buildkite.com/seantis/onegov-cloud)

### Core

🎉 **Better defaults for onegov-core transfer**

The `onegov-core transfer` command may now be used without specifying
a remote config path, as long as Seantis servers are used. That is,
the default remote config is now `/var/lib/onegov-cloud/onegov.yml`.

**`Feature`** | **[c6bcea9f1e](https://github.com/onegov/onegov-cloud/commit/c6bcea9f1ef3e73ea986665e2f823b7607775177)**

🐞 **Fixes Sentry SDK integration**

The Sentry SDK integration was not loaded when requested, so exceptions
on the applications were not reported.

**`Bugfix`** | **[48fce86e19](https://github.com/onegov/onegov-cloud/commit/48fce86e197f993fdc53268d30b62fa2799a9b5b)**

