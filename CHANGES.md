# Changes

## Release `2019.5`

> commits: **13 / [326bab40a2...88a02c2a16](https://github.com/OneGov/onegov-cloud/compare/326bab40a2...88a02c2a16)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.5)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🎉 **Improved PDF rendering, solving Link caching**

Features new page break settings where PDF Layout can be chosen. Fixes link caching especially on Firefox by generating unique links for agency pdf's on creation and links based on modified timestamp for root.pdf (and poeple Excel File as well).

**`Feature`** | **[ZW-200](https://kanton-zug.atlassian.net/browse/ZW-200) | **[2410ee7ab7](https://github.com/onegov/onegov-cloud/commit/2410ee7ab715fcc956c2c49ec72016fe5219eef8)**

### Fixes

✨ **Sed -i '.bak' => sed -i.bak**

**`Other`** | **[88a02c2a16](https://github.com/onegov/onegov-cloud/commit/88a02c2a16aa5822b910af00110205d4905ce8c6)**

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

**`Feature`** | **[STAKA-15](https://ogc-ar.atlassian.net/projects/STAKA/issues/STAKA-15) | **[4191ba6e06](https://github.com/onegov/onegov-cloud/commit/4191ba6e0611c38a743b488e5fe7294bbf9d2151)**

### Core

✨ **Improves Sentry integration**

All filtering now happens on sentry.io and we enabled the Redis and
SQLAlchemy integrations for Sentry.

**`Other`** | **[4313c2d546](https://github.com/onegov/onegov-cloud/commit/4313c2d546b2232f1aab6df4376c329c36385047)**

### Feriennet

🎉 **Adds custom error for insufficient funds**

Resolves #1

**`Feature`** | **[1](https://github.com/onegov/onegov-cloud/issues/1) | **[cc0ad2475c](https://github.com/onegov/onegov-cloud/commit/cc0ad2475c9ec57c29d9c491897e3f296f8a7ac7)**

🐞 **Fixes donations not working**

Regular users were unable to make donations due to an infinite redirect.

**`Bugfix`** | **[5e5a05eddb](https://github.com/onegov/onegov-cloud/commit/5e5a05eddb47bc13d95c40d41fddcaec562fcadf)**

### Winterthur

✨ **Removes pricacy notice.**

It is now renderd outside our iFrame.

**`Other`** | **[FW-69](https://stadt-winterthur.atlassian.net/browse/FW-69) | **[1d9a695a06](https://github.com/onegov/onegov-cloud/commit/1d9a695a068021ffca8a8e44481cf188c854c7fe)**

🐞 **Fixes wrong formatting of percentages**

The daycare subsidy calculator "rounded" percentage of '10.00' to '1'.

**`Bugfix`** | **[FW-63](https://stadt-winterthur.atlassian.net/browse/FW-63) | **[7b0f07f86a](https://github.com/onegov/onegov-cloud/commit/7b0f07f86a3221d0de26adb6e1922bff46d73048)**

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

