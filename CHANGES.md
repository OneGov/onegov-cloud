# Changes

## Release `2019.10`

> commits: **1 / [ac565ca225...ac565ca225](https://github.com/OneGov/onegov-cloud/compare/ac565ca225...ac565ca225)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.10)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Adds api endpoint with aggregated information for national council elections**

The endpoint is available under the url `/election/eample/data-aggregated-lists`.

**`Feature`** | **[ac565ca225](https://github.com/onegov/onegov-cloud/commit/ac565ca22590faf46e01f8325bd5f52833ff7a97)**

## Release `2019.9`

> released: **2019-09-06 15:09**<br>
> commits: **4 / [3e406aeb3c...3c9b101357](https://github.com/OneGov/onegov-cloud/compare/3e406aeb3c...3c9b101357)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.9)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Adds app-specific role maps for LDAP**

Without this change all applications whould share the same role map,
which is too limiting for the general OneGov Cloud use.

**`Feature`** | **[3e406aeb3c](https://github.com/onegov/onegov-cloud/commit/3e406aeb3c59e258e309f260cc525d77cb508dcd)**

## Release `2019.8`

> released: **2019-09-06 12:43**<br>
> commits: **2 / [a728bf78f8...75d00e69fc](https://github.com/OneGov/onegov-cloud/compare/a728bf78f8...75d00e69fc)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.8)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Integrates Kerberos/LDAP**

A new authentication provider provides LDAP authentication together with Kerberos. The request is authenticated by Kerberos (providing a username), the user authorised by LDAP.

**`Feature`** | **[a728bf78f8](https://github.com/onegov/onegov-cloud/commit/a728bf78f8a2025e3b63ff4db3fe2b7342ceed91)**

## Release `2019.7`

> released: **2019-09-05 17:40**<br>
> commits: **8 / [64c5f5bdfb...f48727bc88](https://github.com/OneGov/onegov-cloud/compare/64c5f5bdfb...f48727bc88)**<br>
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
> commits: **2 / [0d57b12204...3d53d3b4b9](https://github.com/OneGov/onegov-cloud/compare/0d57b12204...3d53d3b4b9)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.6)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

✨ **Hide intermediate results for elections and votes**

Hides clear statuses such as elected or number of mandates per list for proporz election if election is not final.

**`Other`** | **[0d57b12204](https://github.com/onegov/onegov-cloud/commit/0d57b122040a9e883735a56d40d891430bae3c10)**

## Release `2019.5`

> released: **2019-09-04 06:04**<br>
> commits: **14 / [326bab40a2...a8937ba123](https://github.com/OneGov/onegov-cloud/compare/326bab40a2...a8937ba123)**<br>
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
> commits: **11 / [5c3adde749...282ed75f8e](https://github.com/OneGov/onegov-cloud/compare/5c3adde749...282ed75f8e)**<br>
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

✨ **Removes pricacy notice.**

It is now renderd outside our iFrame.

**`Other`** | **[FW-69](https://stadt-winterthur.atlassian.net/browse/FW-69)** | **[1d9a695a06](https://github.com/onegov/onegov-cloud/commit/1d9a695a068021ffca8a8e44481cf188c854c7fe)**

🐞 **Fixes wrong formatting of percentages**

The daycare subsidy calculator "rounded" percentage of '10.00' to '1'.

**`Bugfix`** | **[FW-63](https://stadt-winterthur.atlassian.net/browse/FW-63)** | **[7b0f07f86a](https://github.com/onegov/onegov-cloud/commit/7b0f07f86a3221d0de26adb6e1922bff46d73048)**

## Release `2019.3`

> released: **2019-08-29 09:39**<br>
> commits: **5 / [36ebdbfa71...4633aeb348](https://github.com/OneGov/onegov-cloud/compare/36ebdbfa71...4633aeb348)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.3)](https://buildkite.com/seantis/onegov-cloud)

### Core

🎉 **Adds `onegov.core.__version__`**

This version identifier always contains the current version of the
container. During development this information may be stale, as the
version is only updated during the release process.

**`Feature`** | **[b2f4f16f61](https://github.com/onegov/onegov-cloud/commit/b2f4f16f614ad690b8eb5c222b1881a677d1e323)**

## Release `2019.2`

> released: **2019-08-28 10:04**<br>
> commits: **6 / [69399e0e7a...50afe830eb](https://github.com/OneGov/onegov-cloud/compare/69399e0e7a...50afe830eb)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.2)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🐞 **Fixes bug in validate_integer(line, 'stimmen') in wmkandidaten_gde**

**`Bugfix`** | **[75dcf68244](https://github.com/onegov/onegov-cloud/commit/75dcf68244b1cc836fee5a5f27303536819a5720)**

## Release `2019.1`

> released: **2019-08-27 14:22**<br>
> commits: **19 / [53849be4fe...cc3764630e](https://github.com/OneGov/onegov-cloud/compare/53849be4fe...cc3764630e)**<br>
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

