# Changes

## Unreleased

> commits: **19 / [cc3764630e...53849be4fe](https://github.com/OneGov/onegov-cloud/compare/cc3764630e...53849be4fe)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=Unreleased)](https://buildkite.com/seantis/onegov-cloud)

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

## Release `2019.1`

> Released: **2019-08-27 14:22**<br>

> commits: **19 / [cc3764630e...53849be4fe](https://github.com/OneGov/onegov-cloud/compare/cc3764630e...53849be4fe)**<br>
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

