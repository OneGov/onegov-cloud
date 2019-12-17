# Changes

## Release `2019.53`

> commits: **2 / [14d3d9de02...a856b44726](https://github.com/OneGov/onegov-cloud/compare/14d3d9de02^...a856b44726)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.53)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Slightly decrease fuzziness of search results**

We now require the first three letters to match exactly, giving only the
other letters the option to be slightly mismatched with a Levenshtein
distance of 1.

This should improve the clarity of our search results.

**`Feature`** | **[14d3d9de02](https://github.com/onegov/onegov-cloud/commit/14d3d9de02064013fe4ab9b025900c991593c9ad)**

### Swissvotes

🎉 **Adds static urls for /page/dataset**

**`Feature`** | **[a856b44726](https://github.com/onegov/onegov-cloud/commit/a856b44726f6465bb88ff5594a41ddfaa0f46517)**

## Release `2019.52`

> released: **2019-12-16 15:02**<br>
> commits: **2 / [c5f8710c60...c66dbd3a70](https://github.com/OneGov/onegov-cloud/compare/c5f8710c60^...c66dbd3a70)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.52)](https://buildkite.com/seantis/onegov-cloud)

### Swisvotes

🎉 **Adds static urls for vote details page**

**`Feature`** | **[c5f8710c60](https://github.com/onegov/onegov-cloud/commit/c5f8710c60a004f0c8a5a9170eb3b674116badb5)**

## Release `2019.51`

> released: **2019-12-15 23:06**<br>
> commits: **4 / [497c3d9581...286b2d3137](https://github.com/OneGov/onegov-cloud/compare/497c3d9581^...286b2d3137)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.51)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds a paid/unpaid filter to billing**

By default, we only show unpaid bills and use the filter as a toggle.

**`Feature`** | **[FER-489](https://issues.seantis.ch/browse/FER-489)** | **[497c3d9581](https://github.com/onegov/onegov-cloud/commit/497c3d958187c3966697109cbd438877b7fa42c7)**

### Fsi

🐞 **Fixes smaller issue of beta testing phase**

**`Bugfix`** | **[93b02920ff](https://github.com/onegov/onegov-cloud/commit/93b02920ffd329beb9c702ce022684bd3a0c75df)**

### Swissvotes

🎉 **Adds legel form deciding question**

Updates dataset with curiavista, bkresults and bkchrono links. Adds 3 additional attachments.
Adapts views for deciding question.

**`Feature`** | **[b592e32e76](https://github.com/onegov/onegov-cloud/commit/b592e32e769e4cd666f4161b136508580387bd5e)**

## Release `2019.50`

> released: **2019-12-14 15:44**<br>
> commits: **9 / [c50857d184...2c694b27a9](https://github.com/OneGov/onegov-cloud/compare/c50857d184^...2c694b27a9)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.50)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **View group invites as another user**

Admins may now view group invites from the view of another user, which
helps them help out users that are stuck.

**`Feature`** | **[FER-754](https://issues.seantis.ch/browse/FER-754)** | **[c71bc833d4](https://github.com/onegov/onegov-cloud/commit/c71bc833d46fe73e9c6ce98d3a98b434f40124cb)**

🎉 **Optionally override booking cost per occasion**

This allows users to have a higher booking cost for occasions which need
more work to administer, say a 1-week sommercamp.

**`Feature`** | **[FER-824](https://issues.seantis.ch/browse/FER-824)** | **[0ff2671f01](https://github.com/onegov/onegov-cloud/commit/0ff2671f01ab39aa9f37f31eb2c24708d19b976d)**

### Org

🐞 **Fixes thumbnails not working in many cases**

**`Bugfix`** | **[fce1381665](https://github.com/onegov/onegov-cloud/commit/fce138166531db76435149da0b5ebe97cb018654)**

## Release `2019.49`

> released: **2019-12-12 15:18**<br>
> commits: **8 / [837d01d82e...f470ca3a09](https://github.com/OneGov/onegov-cloud/compare/837d01d82e^...f470ca3a09)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.49)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds the ability to book after finalization**

This allows normal users to create bookings after the bill has been
published. Before, this was reserved for administrators.

**`Feature`** | **[FER-194](https://issues.seantis.ch/browse/FER-194)** | **[9d4f242107](https://github.com/onegov/onegov-cloud/commit/9d4f24210762cba487c932b493026a0b5502de00)**

## Release `2019.48`

> released: **2019-12-11 14:10**<br>
> commits: **15 / [ead36cf8ec...11a07e9dcc](https://github.com/OneGov/onegov-cloud/compare/ead36cf8ec^...11a07e9dcc)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.48)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Clear dates when duplicating occasions**

Before, a default date was automatically filled. By clearing the dates
instead we force the user to make a decision, which is what they need to
do anyways, so this is communicated more clearly this way.

**`Feature`** | **[FER-832](https://issues.seantis.ch/browse/FER-832)** | **[ea41093077](https://github.com/onegov/onegov-cloud/commit/ea4109307782802b03cf12ef9f34a5a38873da80)**

🎉 **Adds a print button to my-bills**

It was always possible to have a print version, but not a lot of users
knew about it. With a button it is more obvious.

**`Feature`** | **[FER-653](https://issues.seantis.ch/browse/FER-653)** | **[897f773f32](https://github.com/onegov/onegov-cloud/commit/897f773f3207b4e0787da7372ccddda27892461c)**

### Fsi

🎉 **Limits editor capabilities**

- hide links in UI
- make email sending admin-only
- hides all attendees editors do not have permission to see
- hides all reservations editors do not have permissions to see

**`Feature`** | **[2efe80fe51](https://github.com/onegov/onegov-cloud/commit/2efe80fe5127735ec661e46362d0e366f7001070)**

🎉 **Mailing System incl. previews**

completes functionality for email templates subscription confirmation, cancellation, invitation via form and automatic reminders sent via cronjob. Adds "Cancel" Button to cancel a course event.

**`Feature`** | **[9f9fed2126](https://github.com/onegov/onegov-cloud/commit/9f9fed2126038fc7a04c69e827f795110bf35e9a)**

🎉 **UI Improvements**

- auto-resizing of iframe for email preview
- Hiding cols in reservation table
- prepare lazy-loading switch for accordions /fsi/courses
- use fa icons when printing "course attended" column

**`Feature`** | **[91061072b3](https://github.com/onegov/onegov-cloud/commit/91061072b3d2c3c1a7398c13f6a4e62ed128280f)**

🐞 **Fix translation issues**

**`Bugfix`** | **[a823aa4efa](https://github.com/onegov/onegov-cloud/commit/a823aa4efa1be80e28e9325a472fdfb2205e160f)**

## Release `2019.47`

> released: **2019-12-05 16:02**<br>
> commits: **2 / [fa96aac112...2ae5915c63](https://github.com/OneGov/onegov-cloud/compare/fa96aac112^...2ae5915c63)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.47)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Redesigns group code bookings**

The new UI solves a number of issues with the old approach,
streamlining common use-cases and offering more clarity.

**`Feature`** | **[FER-789](https://issues.seantis.ch/browse/FER-789)** | **[fa96aac112](https://github.com/onegov/onegov-cloud/commit/fa96aac11205c3ac29c00f333f0a7f0e54d6fedb)**

## Release `2019.46`

> released: **2019-12-04 11:52**<br>
> commits: **4 / [96e14a3688...4fa9647ea2](https://github.com/OneGov/onegov-cloud/compare/96e14a3688^...4fa9647ea2)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.46)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Fixes reservations not being shown after selecting them**

This is a regression introduced with the recent view settings change.
The accompanying javascript would generate invalid URLs.

**`Bugfix`** | **[96e14a3688](https://github.com/onegov/onegov-cloud/commit/96e14a36884617ca33ee1b90074cef9df9690d50)**

## Release `2019.45`

> released: **2019-12-03 18:13**<br>
> commits: **9 / [87138a72a5...4fd31b78b4](https://github.com/OneGov/onegov-cloud/compare/87138a72a5^...4fd31b78b4)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.45)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Shows user contact data on bookings/reservations.**

This makes it easier for admins to get in touch with users. Additionally
we also provide a link to the user management of the user.

**`Feature`** | **[FER-825](https://issues.seantis.ch/browse/FER-825)** | **[9f576f76d4](https://github.com/onegov/onegov-cloud/commit/9f576f76d491d1b0568cd8fb68f09f0a69487fad)**

🎉 **Removes edit links for archived occasions**

Occasions from archived periods can technically still be edited, but the

**`Feature`** | **[FER-831](https://issues.seantis.ch/browse/FER-831)** | **[c1e73c7940](https://github.com/onegov/onegov-cloud/commit/c1e73c7940eac2b1054fdb04e11d541228c9e219)**

🎉 **Improves payment details**

Label changes and an additional placeholder should make the usage of
bank payments a bit clearer.

**`Feature`** | **[FER-588](https://issues.seantis.ch/browse/FER-588)** | **[662832b4d0](https://github.com/onegov/onegov-cloud/commit/662832b4d022a47f3019d957aaff17b9fd003fd0)**

✨ **Removes unclear label**

The 'no additional costs' label was misunderstood by many to mean 'free
public transport'. Removing the label altogether rectifies the problem.

**`Other`** | **[FER-564](https://issues.seantis.ch/browse/FER-564)** | **[ffcbc06d5b](https://github.com/onegov/onegov-cloud/commit/ffcbc06d5b8fe0decccc8a1ac8795dea05b5c579)**

### Fsi

🎉 **Adds email previews, info notification sending**

- Email-Previews and Email-Rendering for all Templates
- Improved Attendee Collection with pagination
- Toggle course attended has is passed course event
- Implementation of permissions from LDAP in collections

**`Feature`** | **[5e02776a5f](https://github.com/onegov/onegov-cloud/commit/5e02776a5f92b49804579d7ffa9b42a909bbdf44)**

## Release `2019.44`

> released: **2019-12-02 12:53**<br>
> commits: **3 / [d1e2208edb...d6c938c5f6](https://github.com/OneGov/onegov-cloud/compare/d1e2208edb^...d6c938c5f6)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.44)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🎉 **Improves pdf rendering**

- hold titles together
- makes spacing after portrait consistent

**`Feature`** | **[3a37b55ec5](https://github.com/onegov/onegov-cloud/commit/3a37b55ec5edf88cfd7802c833f30ca68f36f6cc)**

## Release `2019.43`

> released: **2019-11-28 14:27**<br>
> commits: **3 / [9acc0a1abe...55b6c0d996](https://github.com/OneGov/onegov-cloud/compare/9acc0a1abe^...55b6c0d996)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.43)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds the ability to hide events**

Events may now be hidden with the same access methods as normal pages.
That is they can be removed from the list (accessible if you know the
URL), or made private entirely.

**`Feature`** | **[ZW-196](https://kanton-zug.atlassian.net/browse/ZW-196)** | **[5685e17e88](https://github.com/onegov/onegov-cloud/commit/5685e17e88ea943d7925e4af3018cd139f40212c)**

🐞 **Fixes resource subscription error**

When viewing a resource subscription, an error would occur in certain
secenarios.

Fixes ONEGOV-CLOUD-3AS

**`Bugfix`** | **[9acc0a1abe](https://github.com/onegov/onegov-cloud/commit/9acc0a1abe87f508b073cc049b198dbdc2b6c97e)**

## Release `2019.42`

> released: **2019-11-27 15:13**<br>
> commits: **4 / [f4fbdf6818...616849323b](https://github.com/OneGov/onegov-cloud/compare/f4fbdf6818^...616849323b)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.42)](https://buildkite.com/seantis/onegov-cloud)

### User

✨ **Integrates on_login support**

This extends the on_login callback to all user handling applications and
brings it under the onegov.user umbrella, fixing a few bugs.

**`Other`** | **[10f6c5f33d](https://github.com/onegov/onegov-cloud/commit/10f6c5f33df348c578eab1d9aea0ab6ec5951265)**

## Release `2019.41`

> released: **2019-11-26 10:41**<br>
> commits: **2 / [1c5bad57b7...7b78ee1ad1](https://github.com/OneGov/onegov-cloud/compare/1c5bad57b7^...7b78ee1ad1)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.41)](https://buildkite.com/seantis/onegov-cloud)

### File

🐞 **Removes PDF file sanitizing**

This caused a number of issues with Reportlab generated PDFs. Since the
risk of malicious PDFs is somewhat low in most modern environments, we
disable the PDF sanitizing feature, until we find one that works
reliably.

**`Bugfix`** | **[1c5bad57b7](https://github.com/onegov/onegov-cloud/commit/1c5bad57b7d77d8fe9aee9f5bf9e5f22d2b53585)**

## Release `2019.40`

> released: **2019-11-26 09:05**<br>
> commits: **9 / [df42fa39b6...ba91f9cc07](https://github.com/OneGov/onegov-cloud/compare/df42fa39b6^...ba91f9cc07)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.40)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🐞 **Improves pdf rendering**

- Fixes saving and rendering empty p-tags for agency.portrait
- Does not add spacer after empty title
- Keeps agency and members on one page if possible

**`Bugfix`** | **[f62d32a463](https://github.com/onegov/onegov-cloud/commit/f62d32a463a41f7f49de0dcea719c412c79689cf)**

### Org

🎉 **Adds default view option to resource editor**

This gives users the ability to have their room resource open with a
monthly or weekly view. So far, the weekly view was hardcoded in this
case.

They daypass resource only has one view, so the option is not shown for
this resource type.

**`Feature`** | **[ZW-226](https://kanton-zug.atlassian.net/browse/ZW-226)** | **[184c4ae1e5](https://github.com/onegov/onegov-cloud/commit/184c4ae1e58406083a99ff28a1f2756635bc855c)**

🐞 **Fixes logout not redirecting to root**

This issue only occurred in development, where the full path to the
tenant is used in the browser.

**`Bugfix`** | **[5a42041a41](https://github.com/onegov/onegov-cloud/commit/5a42041a416a77231d95175fa59fe0299cd477f6)**

## Release `2019.39`

> released: **2019-11-22 13:58**<br>
> commits: **256 / [4fa47c7b87...1986fcfd5b](https://github.com/OneGov/onegov-cloud/compare/4fa47c7b87^...1986fcfd5b)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.39)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🐞 **Fixes PDF generation not working**

Semicolons were not escaped which lead to invalid PDF files in some
scenarios.

**`Bugfix`** | **[687504c8a8](https://github.com/onegov/onegov-cloud/commit/687504c8a845cd3f8dbc2ff3a89e85cba8ccc061)**

🐞 **Fixes PDF rendering failing in certain cases**

This is the second fix to the PDF rendering issue. We found that the
logo of Appenzell Ausserrhoden could not be parsed reliably and needed
to be replaced with a high-resolution PNG.

**`Bugfix`** | **[7bc18af1e1](https://github.com/onegov/onegov-cloud/commit/7bc18af1e13809f945568c01aa4a8d9d24664d5f)**

### Fsi

🎉 **Supports database updates**

Database updates were not yet activated. Existing FSI databases have to
be recreated.

**`Feature`** | **[ed99729224](https://github.com/onegov/onegov-cloud/commit/ed9972922429f1cf3edf2ac3b65e0e27244aec34)**

### User

🎉 **Adds a source id to external users**

This allows us to track user changes by external providers, including
changes to the e-mail address.

**`Feature`** | **[23ce2b6793](https://github.com/onegov/onegov-cloud/commit/23ce2b6793bd50020294f213225549b5895b8705)**

## Release `2019.38`

> released: **2019-11-19 08:38**<br>
> commits: **6 / [0658a7862b...176281bfe3](https://github.com/OneGov/onegov-cloud/compare/0658a7862b^...176281bfe3)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.38)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds static title option for directory addresses**

By default, the first line of each address in a directory item view is
the title of the address block. This feature adds the ability to define
an alternate fixed title.

**`Feature`** | **[ZW-248](https://kanton-zug.atlassian.net/browse/ZW-248)** | **[c82856479c](https://github.com/onegov/onegov-cloud/commit/c82856479c85a580b5d4d8c854d76f188a278c4a)**

🐞 **Fixes event rendering error**

Events without a price set would not render in some cases.


Fixes ONEGOV-CLOUD-39E
Fixes ONEGOV-CLOUD-39F

**`Bugfix`** | **[0658a7862b](https://github.com/onegov/onegov-cloud/commit/0658a7862bea3512950ebd1e7f40de5a725b81cd)**

### Scanauftrag

🎉 **Orders the invoice positions by BFS number**

This solves sorting issues for municiaplities that have merged.

**`Feature`** | **[SA-51](https://stadt-winterthur.atlassian.net/browse/SA-51)** | **[6cebc1a371](https://github.com/onegov/onegov-cloud/commit/6cebc1a37112be32dc794381b4e6aca396a80950)**

### User

🎉 **Adds a generic LDAP provider**

It currently implements authentication and authorisation using a single
connection to query the LDAP server and the LDAP COMPARE operation to
check user credentials.

It can easily be extended to support authentication through rebind.

**`Feature`** | **[e6c587f30d](https://github.com/onegov/onegov-cloud/commit/e6c587f30d5decc5c3c78cbe5f7bceb1eece2789)**

## Release `2019.37`

> released: **2019-11-13 11:09**<br>
> commits: **3 / [847ec8204a...0e6469b6a6](https://github.com/OneGov/onegov-cloud/compare/847ec8204a^...0e6469b6a6)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.37)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🐞 **Fixes accidental assert statement in Membership.add_person**

When order index is repeating, this gets fixed if the user re-arranges
the order

**`Bugfix`** | **[847ec8204a](https://github.com/onegov/onegov-cloud/commit/847ec8204ad730ca42b53697602794a1954907fe)**

### Winterthur

✨ **Updates legend label**

**`Other`** | **[FW-66](https://stadt-winterthur.atlassian.net/browse/FW-66)** | **[9084c913fb](https://github.com/onegov/onegov-cloud/commit/9084c913fbb38cd1d745faf4e0f0f551910d9f37)**

## Release `2019.36`

> released: **2019-11-12 15:14**<br>
> commits: **3 / [fc630b8095...18553040e2](https://github.com/OneGov/onegov-cloud/compare/fc630b8095^...18553040e2)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.36)](https://buildkite.com/seantis/onegov-cloud)

### Winterthur

🎉 **Splits datetime on mission reports**

The single datetime field was confusing for many users, and the widget
we use has some corner cases with sloppy input. By splitting this field
into two, we have fewer problems.

**`Feature`** | **[FW-66](https://stadt-winterthur.atlassian.net/browse/FW-66)** | **[fc630b8095](https://github.com/onegov/onegov-cloud/commit/fc630b80953c97f17a67a269d572ddfa3a6ff9d5)**

🎉 **Adds customisation options for mission reports**

It is now possible to hide the civil defence's involvement and to
provide a custom legend (including removing it entirely).

**`Feature`** | **[FW-66](https://stadt-winterthur.atlassian.net/browse/FW-66)** | **[e108e096c3](https://github.com/onegov/onegov-cloud/commit/e108e096c376cfd012cd937da204f20b15f74917)**

## Release `2019.35`

> released: **2019-11-12 08:59**<br>
> commits: **4 / [889623375e...80349d6d9d](https://github.com/OneGov/onegov-cloud/compare/889623375e^...80349d6d9d)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.35)](https://buildkite.com/seantis/onegov-cloud)

### Core

✨ **Upgrade to Python 3.8**

OneGov Cloud now uses Python 3.8 instead of 3.7.

**`Other`** | **[195ccc2f23](https://github.com/onegov/onegov-cloud/commit/195ccc2f23ac0d9b8d2968dcf464bf75732ce496)**

## Release `2019.34`

> released: **2019-10-30 15:59**<br>
> commits: **2 / [123b198a00...32e0377e18](https://github.com/OneGov/onegov-cloud/compare/123b198a00^...32e0377e18)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.34)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Fixes news widget failing on certain sites.**

**`Bugfix`** | **[123b198a00](https://github.com/onegov/onegov-cloud/commit/123b198a00533299575e019f37429893a6b3f058)**

## Release `2019.33`

> released: **2019-10-30 09:56**<br>
> commits: **6 / [0dc5b8fc9f...ac06bc140a](https://github.com/OneGov/onegov-cloud/compare/0dc5b8fc9f^...ac06bc140a)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.33)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Enabls hiding of percentage in candidate-by-district**

**`Feature`** | **[0dc5b8fc9f](https://github.com/onegov/onegov-cloud/commit/0dc5b8fc9f8d2c8f18a91c7de81b9bb214bd2464)**

### Search

✨ **Switch to Elasticsearch 7.x**

This doesn't come with any new features, it just uses the latest
Elasticsearch release to stay up to date.

**`Other`** | **[6a26e712dd](https://github.com/onegov/onegov-cloud/commit/6a26e712dd5bcbc39f90d01902017faf286fed68)**

## Release `2019.32`

> released: **2019-10-25 11:52**<br>
> commits: **5 / [5687e1683f...2ded9d9fd7](https://github.com/OneGov/onegov-cloud/compare/5687e1683f^...2ded9d9fd7)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.32)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds categories to the directories geojson**

**`Feature`** | **[ZW-238](https://kanton-zug.atlassian.net/browse/ZW-238)** | **[ca890fb369](https://github.com/onegov/onegov-cloud/commit/ca890fb369ca9de8bad690c57eb03845b1a00230)**

🎉 **Adds a setting to hide the OneGov Cloud footer.**

This includes the marketing site and the privacy policy link.

**`Feature`** | **[ZW-245](https://kanton-zug.atlassian.net/browse/ZW-245)** | **[f0c9b5e937](https://github.com/onegov/onegov-cloud/commit/f0c9b5e9370df2780707ea99972da583ca63ffed)**

🎉 **Adds the ability to upload PDFs with events**

This is useful to add things like flyers or other information.

**`Feature`** | **[ZW-196](https://kanton-zug.atlassian.net/browse/ZW-196)** | **[d0df6ac7e2](https://github.com/onegov/onegov-cloud/commit/d0df6ac7e22c56815045f2067c679615ce8bd0af)**

## Release `2019.31`

> released: **2019-10-23 14:12**<br>
> commits: **4 / [c898172a68...5949739a67](https://github.com/OneGov/onegov-cloud/compare/c898172a68^...5949739a67)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.31)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Improves SMS sending performance**

The main change is that we switch from requests to pycurl, which offers
much better performance.

**`Feature`** | **[c898172a68](https://github.com/onegov/onegov-cloud/commit/c898172a68938b12dea41f86b024cbc5f2d04d26)**

## Release `2019.30`

> released: **2019-10-23 10:39**<br>
> commits: **2 / [816a404e04...117b19eb79](https://github.com/OneGov/onegov-cloud/compare/816a404e04^...117b19eb79)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.30)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Adds support of yml configuration to hide certain graphics or views**

Adapts code to use configuration value to hide certain graphs and percentages according to the tenant's needs. This was implemented for views where a `skip_rendering` was introduced beforehand. Also adds a small fix for a sql window function expression.

**`Feature`** | **[816a404e04](https://github.com/onegov/onegov-cloud/commit/816a404e0498bc810863c22a116b109969944b4d)**

## Release `2019.29`

> released: **2019-10-23 10:16**<br>
> commits: **15 / [d19e1fa2c6...714bb1a7da](https://github.com/OneGov/onegov-cloud/compare/d19e1fa2c6^...714bb1a7da)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.29)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Fixes linkify/paragraphify producing bad output**

This solves two cases, where the html output of these functions were
less then optimal:

* Paragraphify would output empty paragraphs for empty text
* Linkify would swallow newlines in front of some phone numbers

**`Bugfix`** | **[21b4fd7b57](https://github.com/onegov/onegov-cloud/commit/21b4fd7b5716fe085e204a32aafdace4b4631148)**

### Election Day

🐞 **Fixes being unable to embed iframes.**

This was possible before because we did not enforce the Content Security
Policy on all instances. Now we do.

**`Bugfix`** | **[a023fc229f](https://github.com/onegov/onegov-cloud/commit/a023fc229fce57f4f789f632ee21b5bf5b226d28)**

### Election-Day

🐞 **Fixes sql query window function to connection results**

**`Bugfix`** | **[b2950c657c](https://github.com/onegov/onegov-cloud/commit/b2950c657c1bd82d76939d3ed9a40a288ce30bd2)**

### File

🎉 **Automatically sanitize all incoming PDF files**

The sanitizer will obfuscate dangerous directives like /JavaScript to
ensure that the PDF does no harm. As a result, certain features might
not work after uploading the PDF.

**`Feature`** | **[ZW-196](https://kanton-zug.atlassian.net/browse/ZW-196)** | **[c241e03c62](https://github.com/onegov/onegov-cloud/commit/c241e03c6227e48aebf9eada6121bd169829d686)**

### Org

🎉 **Adds public e-mail address to events**

E-Mails could always be entered in the description, but this makes it
more explicit.

**`Feature`** | **[ZW-196](https://kanton-zug.atlassian.net/browse/ZW-196)** | **[7a9a12fb96](https://github.com/onegov/onegov-cloud/commit/7a9a12fb96a88bc843c59b982d45f65c95d72cfe)**

🎉 **Adds designated price field to events**

This is a free text, since prices for events are often described, rather
than quantified.

**`Feature`** | **[ZW-196](https://kanton-zug.atlassian.net/browse/ZW-196)** | **[3a951a1bb4](https://github.com/onegov/onegov-cloud/commit/3a951a1bb49d63531965ded28276a2662116eb81)**

🎉 **Hides the news if there are no news items.**

This enables some sites to go completely without top-bar.

**`Feature`** | **[c066ad168a](https://github.com/onegov/onegov-cloud/commit/c066ad168afde411497ba2445adad895aaa019c6)**

## Release `2019.28`

> released: **2019-10-15 09:42**<br>
> commits: **3 / [af4ff8e167...67cc464e10](https://github.com/OneGov/onegov-cloud/compare/af4ff8e167^...67cc464e10)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.28)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Fixes arrow week granularity translations for itialian and rumantsch**

**`Bugfix`** | **[f1da1d1f47](https://github.com/onegov/onegov-cloud/commit/f1da1d1f47ebb570529f423cdd255f54e8530538)**

## Release `2019.27`

> released: **2019-10-14 14:20**<br>
> commits: **3 / [cf141436da...2f96cfc593](https://github.com/OneGov/onegov-cloud/compare/cf141436da^...2f96cfc593)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.27)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Allows for booking and execution phases to overlap**

This also gets rid of the deadline date, which is now the booking
phase's end date.

**`Feature`** | **[FER-783](https://issues.seantis.ch/browse/FER-783)** | **[c7a310ef3a](https://github.com/onegov/onegov-cloud/commit/c7a310ef3a3404e2d358e6ec19c6f7c5e27dee08)**

## Release `2019.26`

> released: **2019-10-11 10:21**<br>
> commits: **5 / [54237533cc...7c8f1750e7](https://github.com/OneGov/onegov-cloud/compare/54237533cc^...7c8f1750e7)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.26)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds payment state to ticket list view**

This enables us to easily show which tickets have open payments.
Additionally it is now possible to change the payment state without
having to repoen a ticket.

**`Feature`** | **[2443034e78](https://github.com/onegov/onegov-cloud/commit/2443034e7828189d71c85c22537704a34595bccb)**

### User

🎉 **Redirect to / after auto-login, if on login page**

This ensures that after a successful auto-login, the user is not
confused when he sees the login form again.

**`Feature`** | **[f75a760671](https://github.com/onegov/onegov-cloud/commit/f75a7606717c4714e93bc37a4ea56f9114431bd6)**

## Release `2019.25`

> released: **2019-10-10 15:09**<br>
> commits: **5 / [bfa6f6b0ff...453ac1ade7](https://github.com/OneGov/onegov-cloud/compare/bfa6f6b0ff^...453ac1ade7)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.25)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Hides connection-chart for lists if election is not completed**

**`Feature`** | **[18958675f1](https://github.com/onegov/onegov-cloud/commit/18958675f11246d89104d2e54c2b6903d1c33686)**

🐞 **Fixes displaying party pana results for list pana results**

- Fixes adding owner for list panachage results
- Adds parent_connection_id prefix to connection_id

**`Bugfix`** | **[b69d1d8b72](https://github.com/onegov/onegov-cloud/commit/b69d1d8b720ebb1d1fc95504dd351492499c331d)**

## Release `2019.24`

> released: **2019-10-09 14:31**<br>
> commits: **2 / [33a3fe7881...cac0b1a82c](https://github.com/OneGov/onegov-cloud/compare/33a3fe7881^...cac0b1a82c)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.24)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Fixes database upgrade failing on Postgres < 10**

The upgrade used a feature not available on 9.6.'

**`Bugfix`** | **[33a3fe7881](https://github.com/onegov/onegov-cloud/commit/33a3fe7881774c11129eeb93c7e264668b0feac4)**

## Release `2019.23`

> released: **2019-10-09 13:11**<br>
> commits: **6 / [7cdac038a6...3059a207ee](https://github.com/OneGov/onegov-cloud/compare/7cdac038a6^...3059a207ee)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.23)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Introduces new access settings**

This replaces the 'hide from public' setting with a three-tiered setting
that supports the following attributes:

* Public (default)
* Secret (accessible through URL, not listed)
* Private (Existing hide from public equivalent)

**`Feature`** | **[351550d9e0](https://github.com/onegov/onegov-cloud/commit/351550d9e0a65806f33b060c49585b831f9441ba)**

🎉 **Adds a zipcode block for resources**

Resources may now have an optional zipcode block, which prefers people
from certain zipcodes when it comes to bookings.

**`Feature`** | **[bef57fa350](https://github.com/onegov/onegov-cloud/commit/bef57fa3502d80a5bd108800a7e35bcf4a2b543f)**

## Release `2019.22`

> released: **2019-10-03 16:54**<br>
> commits: **10 / [8636d6d3f5...3925017707](https://github.com/OneGov/onegov-cloud/compare/8636d6d3f5^...3925017707)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.22)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Show a note for denied bookings**

This explains why a booking has the 'denied' state in a few words, to
soften the blow, so to speak.

**`Feature`** | **[FER-777](https://issues.seantis.ch/browse/FER-777)** | **[7ce88e195a](https://github.com/onegov/onegov-cloud/commit/7ce88e195aa9816872cbac67e0e4733fee1feaf9)**

🎉 **Send notifications per period**

Notifications used to be sent to the active period in most cases. Now it
is possible to select the period to which the notificaiton applies to
(defaulting to the active period).

**`Feature`** | **[FER-792](https://issues.seantis.ch/browse/FER-792)** | **[8ed483a499](https://github.com/onegov/onegov-cloud/commit/8ed483a4995f6e36b972a8d4ca02c6bf2daebd05)**

🐞 **Improves locations for inline-loaded activites**

In certain situations, the location history would not work for
inline-loaded activites. Now it should work in all cases.

**`Bugfix`** | **[FER-756](https://issues.seantis.ch/browse/FER-756)** | **[8636d6d3f5](https://github.com/onegov/onegov-cloud/commit/8636d6d3f542c72f79619751d49af97891a89521)**

✨ **Improve finalization message**

It did not yet take into account the newly given powers to
administrators.

**`Other`** | **[FER-394](https://issues.seantis.ch/browse/FER-394)** | **[c0c9c7ef7c](https://github.com/onegov/onegov-cloud/commit/c0c9c7ef7ca6af04b108186a6f67b67e0cee5fd9)**

🐞 **Fixes occasion count**

Activities with occasions in multiple periods would show the wrong
occasion count when booking an occasion.

**`Bugfix`** | **[FER-802](https://issues.seantis.ch/browse/FER-802)** | **[32aaf6c597](https://github.com/onegov/onegov-cloud/commit/32aaf6c597b69c49cfdc735ce1c3059cf2e8c16c)**

### Org

🎉 **Automatically break e-mail links**

A hyphen was inserted before and it didn't work on Firefox.

**`Feature`** | **[FER-776](https://issues.seantis.ch/browse/FER-776)** | **[21aeb3268e](https://github.com/onegov/onegov-cloud/commit/21aeb3268e1b648d1b6413762356e3778748cad3)**

## Release `2019.21`

> released: **2019-10-01 16:29**<br>
> commits: **14 / [729c079a33...d7e90e52ba](https://github.com/OneGov/onegov-cloud/compare/729c079a33^...d7e90e52ba)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.21)](https://buildkite.com/seantis/onegov-cloud)

### Core

✨ **No longer delete cookies**

This fixes an issue with logout messages never being shown to the user.
Security wise this does not make a difference, because when we forget a
user we do so by removing the necessary authentication bits in our
server-side session cache. That is, if a certain session id stored in
the cookie is deleted, it is irrelevant if that session id is requested
again, we have already downgraded it.

**`Other`** | **[3fd5db0a87](https://github.com/onegov/onegov-cloud/commit/3fd5db0a877d18f57bef0fb6fe1cd7ced50ed5a7)**

### Election-Day

🏎 **Sql query api rewrite for election/connections-table**

Adds sql query and api endpoint `/election/data-list-connections` for `election-connections-table`. Handles display of sublist names better for the case sublist names are prefixed with parent connections.

**`Performance`** | **[729c079a33](https://github.com/onegov/onegov-cloud/commit/729c079a33ad8f3c00de56a4f4d84d3b7f50a344)**

### Feriennet

🎉 **Introduces a command to delete periods**

This is a semi-regular support request we have to fulfill, which is
going to be much easier to fulfill with this command.

**`Feature`** | **[e532bb4c67](https://github.com/onegov/onegov-cloud/commit/e532bb4c67926c3ec3617b5e7e3508f2f8b39af2)**

🎉 **Adds periods without pre-booking/billing**

Users may now chose to disable pre-booking and/or billing when creating
a period. Pre-booking can only be disabled upon creation of the period,
billing can be changed at any time.

**`Feature`** | **[FER-677](https://issues.seantis.ch/browse/FER-677)** | **[11e8490be4](https://github.com/onegov/onegov-cloud/commit/11e8490be4b28258d4a0de6e5d9872a28fe781bb)**

🎉 **Adds locations for inline-loaded activites**

In the activity list, clicking on "more activites" did not use any
browser history yet. This caused issues with Chrome which does not come
with a bfcache and therefore tries to re-load the site, losing all
navigational state.

This change solves this issue by updating the URL for each loaded page.

**`Feature`** | **[FER-756](https://issues.seantis.ch/browse/FER-756)** | **[b7f503a21c](https://github.com/onegov/onegov-cloud/commit/b7f503a21c779ac950bf01cb11185f6033ddaac9)**

✨ **Adds BoSW and OneGov Awards to Footer**

**`Other`** | **[FER-752](https://issues.seantis.ch/browse/FER-752)** | **[172b88f6bd](https://github.com/onegov/onegov-cloud/commit/172b88f6bd5690b9bc3ce577e4f2f5ef45ff1b4d)**

✨ **Improves wording of occasion notifactions**

It was unclear that these notifications would also be sent to users with
wishes.

**`Other`** | **[FER-515](https://issues.seantis.ch/browse/FER-515)** | **[b6b5c778e3](https://github.com/onegov/onegov-cloud/commit/b6b5c778e33d610f975db1eb994994eef7b59043)**

### Org

🎉 **Logout now always redirects to the homepage**

This avoids the confusing 'Access Denied' message after logging out
while being on a protected view.

**`Feature`** | **[FER-681](https://issues.seantis.ch/browse/FER-681)** | **[e1784982ce](https://github.com/onegov/onegov-cloud/commit/e1784982cefba4442787b25196dc106066fb787e)**

🎉 **Adds social media links for YouTube and Instagram**

**`Feature`** | **[FER-116](https://issues.seantis.ch/browse/FER-116)** | **[f6ec72a0bc](https://github.com/onegov/onegov-cloud/commit/f6ec72a0bcfec18c7d843780d7b50dd7ce12ad41)**

## Release `2019.20`

> released: **2019-09-26 11:21**<br>
> commits: **3 / [350f56de4b...8862d19fee](https://github.com/OneGov/onegov-cloud/compare/350f56de4b^...8862d19fee)**<br>
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.20)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Admins may now book after billing**

When an admin adds a booking after the bills have been created, a new
billing item is added for each booking made, unless the billing is
all-inclusive, in which case the booking is only added if necessary.

**`Feature`** | **[FER-786](https://issues.seantis.ch/browse/FER-786)** | **[350f56de4b](https://github.com/onegov/onegov-cloud/commit/350f56de4bea0a8e7fe4306eae46fd7f5d169423)**

### Winterthur

🐞 **Fixes municipality imports not working**

It would work on certain Postgres releases, but not all.

**`Bugfix`** | **[b317593649](https://github.com/onegov/onegov-cloud/commit/b3175936499cc317d4a89a53805a7778a192cb59)**

## Release `2019.19`

> released: **2019-09-24 16:58**<br>
> commits: **5 / [75f6dd1a4c...bbe6bb9f78](https://github.com/OneGov/onegov-cloud/compare/75f6dd1a4c^...bbe6bb9f78)**<br>
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

