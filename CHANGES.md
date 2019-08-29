# Changes

## Release `2019.3`

> commits: **4 / [36ebdbfa71...ba66e0052e](https://github.com/OneGov/onegov-cloud/compare/36ebdbfa71...ba66e0052e)**<br>
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

