# Changes

## 2024.42

`2024-08-01` | [ef924060e7...ba900d48cc](https://github.com/OneGov/onegov-cloud/compare/ef924060e7^...ba900d48cc)

### Org

##### Avoids emitting a misleading warning for logged in users

`Bugfix` | [715091e1c0](https://github.com/onegov/onegov-cloud/commit/715091e1c08e3efb7258a914fac3b0e315780ad5)

### Translator

##### Make agency references field optional

`Feature` | [OGC-1753](https://linear.app/onegovcloud/issue/OGC-1753) | [ef924060e7](https://github.com/onegov/onegov-cloud/commit/ef924060e772d7d26f25518fc15ae5089941b123)

##### Adjust admission course text

`Feature` | [OGC-1760](https://linear.app/onegovcloud/issue/OGC-1760) | [25e2827d45](https://github.com/onegov/onegov-cloud/commit/25e2827d45ce9bde965516cae99847cbe571c355)

## 2024.41

`2024-07-26` | [6e7f24b857...f03c817189](https://github.com/OneGov/onegov-cloud/compare/6e7f24b857^...f03c817189)

### Directories

##### Adjust string field rendering to prevent many newlines

`Bugfix` | [OGC-1746](https://linear.app/onegovcloud/issue/OGC-1746) | [2463c194fa](https://github.com/onegov/onegov-cloud/commit/2463c194fabbd4e80fbff1dcee88313d824747df)

### Feriennet

##### Import bank statements now supports 27 character reference number in booking text (POFI)

Also we do not break the import if one entry fails

`Bugfix` | [OGC-1295](https://linear.app/onegovcloud/issue/OGC-1295) | [bd4e30ab0f](https://github.com/onegov/onegov-cloud/commit/bd4e30ab0f3f7ca705b2b1ef53e9b3ce46f5e216)

### News

##### Swap interchanged links for RSS feed and newsletter subscription

`Bugfix` | [OGC-1763](https://linear.app/onegovcloud/issue/OGC-1763) | [e49eeb29b2](https://github.com/onegov/onegov-cloud/commit/e49eeb29b2800ba9113182668f290b5a2dd3b459)

### Org

##### Adds mTAN as a second factor option

This second factor can be configured to be automatically set up after
the first login of a user without a configured second factor.

`Feature` | [OGC-1030](https://linear.app/onegovcloud/issue/OGC-1030) | [b3d87a0208](https://github.com/onegov/onegov-cloud/commit/b3d87a0208c8600f1fe041091a47997344289885)

##### Adds TOTP as a second factor option

`Feature` | [SEA-1413](https://linear.app/seantis/issue/SEA-1413) | [049160d61a](https://github.com/onegov/onegov-cloud/commit/049160d61a6ebd06902672e970a717d2ada07a9f)

## 2024.40

`2024-07-19` | [4fdef5e05c...f81d5c42cd](https://github.com/OneGov/onegov-cloud/compare/4fdef5e05c^...f81d5c42cd)

### Core

##### Updates Sentry integration for v2.10+

`Bugfix` | [OGC-1745](https://linear.app/onegovcloud/issue/OGC-1745) | [c9ba7fa549](https://github.com/onegov/onegov-cloud/commit/c9ba7fa54993b82f15d028b32d4b5e43c7024a2d)

### Docs

##### Fix Election Day API docs.

`Bugfix` | [b4dda4d15b](https://github.com/onegov/onegov-cloud/commit/b4dda4d15bf631344d0e2b1a0201e9d6a03db1bc)

### Event

##### Adds settings for general event files and shows files in sidebar of occurrences view

`Feature` | [OGC-1544](https://linear.app/onegovcloud/issue/OGC-1544) | [a4f76d7ce9](https://github.com/onegov/onegov-cloud/commit/a4f76d7ce94b4a91cb067157c07b29dfd285b4f0)

### Form

##### Adds email as default mandatory field for new forms

`Feature` | [OGC-1594](https://linear.app/onegovcloud/issue/OGC-1594) | [e22b65da60](https://github.com/onegov/onegov-cloud/commit/e22b65da603fec5047d73a0db1aaff512b656e93)

##### Raise error for empty field sets

`Feature` | [OGC-1160](https://linear.app/onegovcloud/issue/OGC-1160) | [11be9de24c](https://github.com/onegov/onegov-cloud/commit/11be9de24c12034b0e375968839e23929198c5d7)

### Org

##### Show event settings

`Bugfix` | [NONE](#NONE) | [b115c262c2](https://github.com/onegov/onegov-cloud/commit/b115c262c227b2b0fcb34ae094bd99c691a62224)

### Pas

##### Add rate sets, settlement runs and changes.

`Feature` | [OGC-1503](https://linear.app/onegovcloud/issue/OGC-1503) | [4aa7f4917d](https://github.com/onegov/onegov-cloud/commit/4aa7f4917dc415e7373dd5c23c55b4670b752866)

##### Fix translation.

`Bugfix` | [61ea339eca](https://github.com/onegov/onegov-cloud/commit/61ea339ecab7c09f4c53997a039dc969c667550d)

### People

##### CLI import command extended for organisation fields  Improved error output for incorrect header fields

`Feature` | [OGC-1736](https://linear.app/onegovcloud/issue/OGC-1736) | [4fdef5e05c](https://github.com/onegov/onegov-cloud/commit/4fdef5e05c22c9586c4b627270a6fdde6878c244)

### Settings

##### Move settings for events to event settings section

`Feature` | [NONE](#NONE) | [37e4cc067a](https://github.com/onegov/onegov-cloud/commit/37e4cc067a9bebe78e3c72f88de801fe496e413e)

## 2024.39

`2024-07-11` | [26aad8fd14...47267eebea](https://github.com/OneGov/onegov-cloud/compare/26aad8fd14^...47267eebea)

### Docker

##### Fix nginx cache buster.

`Bugfix` | [OGC-1734](https://linear.app/onegovcloud/issue/OGC-1734) | [d11dd89666](https://github.com/onegov/onegov-cloud/commit/d11dd89666180a2b5e13c3662138ca7b9aca3aab)

### Docs

##### Resolve various warnings.

`Bugfix` | [e45c8c878d](https://github.com/onegov/onegov-cloud/commit/e45c8c878de29612394bf1e0095f9184ad8f631e)

### Election Day

##### Fix search hint rendering.

`Bugfix` | [53c96917ca](https://github.com/onegov/onegov-cloud/commit/53c96917cab9f61d36a2709fb6d5c91a3877e942)

### Feriennet

##### Replace Banners

`Feature` | [PRO-1300](https://linear.app/projuventute/issue/PRO-1300) | [a0458ba8ac](https://github.com/onegov/onegov-cloud/commit/a0458ba8ac1e39da1d7b2e4eedc8fda797520b0a)

##### Fix bug when there is no prebooking phase

`Bugfix` | [PRO-1296](https://linear.app/projuventute/issue/PRO-1296) | [c4fe859a94](https://github.com/onegov/onegov-cloud/commit/c4fe859a94eb7b854c0804703d22a91d2b481a4c)

##### Read QR-Payments

Some entries have no "TxDtls" instead they have their information in "AddtlNtryInf".

`Bugfix` | [OGC-1198](https://linear.app/onegovcloud/issue/OGC-1198) | [dbf8a6afc2](https://github.com/onegov/onegov-cloud/commit/dbf8a6afc225ed98807207148b8b4b59ddca528f)

### Form

##### Fix broken rendering

`Bugfix` | [OGC-1738](https://linear.app/onegovcloud/issue/OGC-1738) | [55bbad189a](https://github.com/onegov/onegov-cloud/commit/55bbad189a2dc9faac1dd6c7bac240fcd81ba565)

### Landsgemeinde

##### Remove YouTube recommendations

`Feature` | [OGC-1651](https://linear.app/onegovcloud/issue/OGC-1651) | [2f561e8c85](https://github.com/onegov/onegov-cloud/commit/2f561e8c85fffa2d9b15b77673b4fb3e670c898e)

### Org

##### Surveys

Add option to create and view results of surveys

`Feature` | [OGC-1612](https://linear.app/onegovcloud/issue/OGC-1612) | [15b0142f61](https://github.com/onegov/onegov-cloud/commit/15b0142f6197ad607b5174f1e1e9184748464611)

### People

##### Fix vcard export.

`Bugfix` | [31d27201e3](https://github.com/onegov/onegov-cloud/commit/31d27201e373b67906cb91973bfb9d29855f3a3a)

### Resource

##### Allow deleting resources with future reservations. Deletes related payments

`Feature` | [OGC-1701](https://linear.app/onegovcloud/issue/OGC-1701) | [b4a9b75838](https://github.com/onegov/onegov-cloud/commit/b4a9b75838352da1713bc4ab6ce23ce70cff7a91)

### Town6

##### Move tracking code into header

`Feature` | [OGC-1700](https://linear.app/onegovcloud/issue/OGC-1700) | [c8b94b2202](https://github.com/onegov/onegov-cloud/commit/c8b94b2202ee5a0e1eac748e91b58e9ad02fec62)

##### Allow scrolling in side-navigation

`Feature` | [OGC-1703](https://linear.app/onegovcloud/issue/OGC-1703) | [ec2ee37558](https://github.com/onegov/onegov-cloud/commit/ec2ee375586d49297d1d98f4728810db53cfac08)

##### Editmode People

Add "save" and "cancel" to Edit-bar when editing people.

`Feature` | [7412046ffb](https://github.com/onegov/onegov-cloud/commit/7412046ffb37facb8560660e5bddfc6a3632db9b)

##### Rename Buttons

`Feature` | [OGC-1697](https://linear.app/onegovcloud/issue/OGC-1697) | [cf1e9033cb](https://github.com/onegov/onegov-cloud/commit/cf1e9033cb1d097944ff69d9ede69def04f35d58)

## 2024.38

`2024-07-05` | [72c07c37c0...485c773b87](https://github.com/OneGov/onegov-cloud/compare/72c07c37c0^...485c773b87)

### Agency

##### Align mutation note for agency to person

`Feature` | [OGC-1599](https://linear.app/onegovcloud/issue/OGC-1599) | [0a460dc832](https://github.com/onegov/onegov-cloud/commit/0a460dc832dcf39adc5d92cde4194841bfa34015)

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1721](https://linear.app/onegovcloud/issue/OGC-1721) | [fc8c86d540](https://github.com/onegov/onegov-cloud/commit/fc8c86d540821bdeb0b9ff26302c780dd5f4f146)

### Election Day

##### Add strategy for majority types in eCH.

`Feature` | [OGC-1673](https://linear.app/onegovcloud/issue/OGC-1673) | [d045e671e1](https://github.com/onegov/onegov-cloud/commit/d045e671e1784d7d1c28a6a1f9e05a1d2ad5564b)

##### Add strategy for expats in eCH.

`Feature` | [OGC-1673](https://linear.app/onegovcloud/issue/OGC-1673) | [693d436932](https://github.com/onegov/onegov-cloud/commit/693d4369326f8d801e6ad467c86791ff371fa01b)

##### Fixes class check in eCH import.

`Bugfix` | [99f5f862e7](https://github.com/onegov/onegov-cloud/commit/99f5f862e7c6f05510b0b861f21ac1878bda532d)

### Feriennet

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1723](https://linear.app/onegovcloud/issue/OGC-1723) | [ab79e862b5](https://github.com/onegov/onegov-cloud/commit/ab79e862b530d283f3bbeed7c316299a725581bc)

### Fsi

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1718](https://linear.app/onegovcloud/issue/OGC-1718) | [348927dc53](https://github.com/onegov/onegov-cloud/commit/348927dc532f1a66c10a6ac426c292d638bb81c2)

### Landsgemeinde

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1717](https://linear.app/onegovcloud/issue/OGC-1717) | [03f39f3500](https://github.com/onegov/onegov-cloud/commit/03f39f3500ec655c44f6df089fb236a4652ae28f)

##### Disable audio preload.

`Bugfix` | [d71094f62f](https://github.com/onegov/onegov-cloud/commit/d71094f62ffb29202c1ef9def45f5ce56a6a5ca0)

### Newsletter

##### Adds note for secret and private content not being sent. Scheduled newsletter contains same content as if sent by manager.

`Feature` | [OGC-1691](https://linear.app/onegovcloud/issue/OGC-1691) | [7ee983441d](https://github.com/onegov/onegov-cloud/commit/7ee983441de5e948d22440f26695a6958db3efb9)

### Org

##### Translate mail content

`Bugfix` | [OGC-1595](https://linear.app/onegovcloud/issue/OGC-1595) | [3d6bedee90](https://github.com/onegov/onegov-cloud/commit/3d6bedee90759bc15dc16d8109438fdda18a85b0)

##### Removes uses of structure keyword in templates

This also consistently produces/uses Markup in the core modules

`Bugfix` | [OGC-1722](https://linear.app/onegovcloud/issue/OGC-1722) | [357d6e8a0f](https://github.com/onegov/onegov-cloud/commit/357d6e8a0fd39ca1e21485811ec0b49d18e6b410)

##### Fixes some broken Markup rendering

`Bugfix` | [ae7fc68fe7](https://github.com/onegov/onegov-cloud/commit/ae7fc68fe7a584dfd82ec6393ba7bbcd8f018a6d)

### Pas

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1716](https://linear.app/onegovcloud/issue/OGC-1716) | [72c07c37c0](https://github.com/onegov/onegov-cloud/commit/72c07c37c0547f6958122ed1ba5596d2a6d47ec5)

### People

##### Adds filtering for organizations or sub organizations

`Feature` | [OGC-1695](https://linear.app/onegovcloud/issue/OGC-1695) | [238d714f7a](https://github.com/onegov/onegov-cloud/commit/238d714f7a9a4be490a44e943099274e56c26c8f)

### Submission

##### Change button label to 'Complete'

`Feature` | [OGC-1698](https://linear.app/onegovcloud/issue/OGC-1698) | [ef80e95220](https://github.com/onegov/onegov-cloud/commit/ef80e9522069a44db50bb13dcc707afb667a0831)

### Town6

##### Save and cancel buttons only in edit-bar

`Bugfix` | [efb181f976](https://github.com/onegov/onegov-cloud/commit/efb181f976a048753aaf8ae94ae1ceb2f474fcd7)

### Translatordirectory

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1720](https://linear.app/onegovcloud/issue/OGC-1720) | [7c5077bee6](https://github.com/onegov/onegov-cloud/commit/7c5077bee6f0b036cc8e6015aac59cd5a8ddecfd)

### Translators

##### Layout: Stop wrapping email addresses and increase max width

`Feature` | [OGC-1601](https://linear.app/onegovcloud/issue/OGC-1601) | [49c7a75180](https://github.com/onegov/onegov-cloud/commit/49c7a751806a17010a935ecf95632ffe2c2750c5)

### User Admin

##### Show 'active' users by default

`Feature` | [OGC-1710](https://linear.app/onegovcloud/issue/OGC-1710) | [d5fc407b74](https://github.com/onegov/onegov-cloud/commit/d5fc407b74484d9e05c5714b43de518be08a98a6)

##### Show 'active' users by default. Move implementation from path to navigation

`Feature` | [OGC-1710](https://linear.app/onegovcloud/issue/OGC-1710) | [480f20be13](https://github.com/onegov/onegov-cloud/commit/480f20be1392f63f330427dcd1b976e9b18f2254)

### Winterthur

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1724](https://linear.app/onegovcloud/issue/OGC-1724) | [b39a7e7ac8](https://github.com/onegov/onegov-cloud/commit/b39a7e7ac80bc7929b78645ce26c7ccb9fa223cd)

## 2024.37

`2024-06-26` | [011617db18...6715019161](https://github.com/OneGov/onegov-cloud/compare/011617db18^...6715019161)

### Election Day

##### Update conversion of eCH domains.

`Feature` | [OGC-1673](https://linear.app/onegovcloud/issue/OGC-1673) | [dc8b4738fc](https://github.com/onegov/onegov-cloud/commit/dc8b4738fc90542e5b0bc2286b93a1e74fb21132)

### Electionday

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1713](https://linear.app/onegovcloud/issue/OGC-1713) | [b3a879e1f5](https://github.com/onegov/onegov-cloud/commit/b3a879e1f541a47ca1eca2c39c5b7cc9a1396374)

### Gazette

##### Removes uses of structure keyword in templates (#1402)

This also adds `MarkupText` as a new column type

`Bugfix` | [OGC-1715](https://linear.app/onegovcloud/issue/OGC-1715) | [58c83b32d6](https://github.com/onegov/onegov-cloud/commit/58c83b32d6867d0fa1e4708c733500ad88835330)

### Newsletter

##### Improve separation line between news

`Feature` | [dcdfffd75d](https://github.com/onegov/onegov-cloud/commit/dcdfffd75d13e86179f2ee19effd0e86f5511399)

### Wtfs

##### Removes uses of structure keyword in templates

`Bugfix` | [OGC-1708](https://linear.app/onegovcloud/issue/OGC-1708) | [7643722820](https://github.com/onegov/onegov-cloud/commit/7643722820567199be2b5d2e3556ad8d228bac3d)

## 2024.36

`2024-06-21` | [8e594d6508...b261703dcc](https://github.com/OneGov/onegov-cloud/compare/8e594d6508^...b261703dcc)

### Files

##### Adds 'published until' column to file view

`Feature` | [OGC-1696](https://linear.app/onegovcloud/issue/OGC-1696) | [712232fdff](https://github.com/onegov/onegov-cloud/commit/712232fdffeee2de1785d86abf79ec72de0df84b)

### Newsletter

##### Subscribers are now auto-confirmed if a manager adds it

`Feature` | [OGC-1666](https://linear.app/onegovcloud/issue/OGC-1666) | [c3845373bc](https://github.com/onegov/onegov-cloud/commit/c3845373bccfe9d85015f836ed7d6066b91a263e)

### Org

##### New event tag "nature"

`Feature` | [OGC-1699](https://linear.app/onegovcloud/issue/OGC-1699) | [17c487854f](https://github.com/onegov/onegov-cloud/commit/17c487854fc5dd31447922217c5c23cd7b8d565a)

### Town6

##### Fix save-button bug

`Bugfix` | [OGC-1682](https://linear.app/onegovcloud/issue/OGC-1682) | [28d404230d](https://github.com/onegov/onegov-cloud/commit/28d404230da1ebc8856e195a9e358a846e27bb51)

## 2024.35

`2024-06-21` | [78ad20bd65...fe1b0dc0f1](https://github.com/OneGov/onegov-cloud/compare/78ad20bd65^...fe1b0dc0f1)

### Feriennet

##### Remove obsolete storage link expansion (as it is html now)

`Bugfix` | [PRO-1289](https://linear.app/projuventute/issue/PRO-1289) | [8ec64d4b4c](https://github.com/onegov/onegov-cloud/commit/8ec64d4b4c80f800b32e5124424d2dc0fb3099a9)

### Search

##### Avoids Postgres indexer causing invalid transactions

This problem only manifested itself in large import jobs where a lot of
ORM events are being generated and the indexer has to be called in the
middle of a transaction, rather than at the end. Since we don't yet use
the Postgres index we haven't fully fixed this yet and instead drop the
ORM events we can't fit into our queue.

This also fixes `ensure_user` failing if the new `username` is already
taken by another user.

`Bugfix` | [OGC-1400](https://linear.app/onegovcloud/issue/OGC-1400) | [1caed2b34e](https://github.com/onegov/onegov-cloud/commit/1caed2b34e7c5a12998ac631e48fec8344e137e6)

##### Allows executing the `PostgresIndexer` mid-transaction

Previously the indexer would've invalidated our transaction and vice
versa causing the entire request to semi-silently fail with a 409.

`Bugfix` | [OGC-1707](https://linear.app/onegovcloud/issue/OGC-1707) | [b6ea9a1148](https://github.com/onegov/onegov-cloud/commit/b6ea9a114819f7c6bd34966c34909d3e29faaaeb)

### Swissvotes

##### Removes uses of structure keyword in templates

This also bans further uses of said keyword within Swissvotes

`Bugfix` | [OGC-1709](https://linear.app/onegovcloud/issue/OGC-1709) | [2e5a5adc7b](https://github.com/onegov/onegov-cloud/commit/2e5a5adc7b10ecba25ab281b25a4685939e5900a)

## 2024.34

`2024-06-14` | [0160578239...b29d754fcf](https://github.com/OneGov/onegov-cloud/compare/0160578239^...b29d754fcf)

**Upgrade hints**
- Tokens generated prior to the upgrade will become invalid
### Core

##### Removes potential timing side channel when validating yubikeys

`Bugfix` | [SEA-1051](https://linear.app/seantis/issue/SEA-1051) | [eec19e4e31](https://github.com/onegov/onegov-cloud/commit/eec19e4e31d2eb9dee91b53e485cc64e026363b8)

### Directory

##### Enable option for getting notifications on new directory entries

If option is enabled in directory settings, people can now subscribe to a directory. Whenever said directory gets a new entry, subscribers get a notification email.

`Feature` | [OGC-1595](https://linear.app/onegovcloud/issue/OGC-1595) | [56de8c24aa](https://github.com/onegov/onegov-cloud/commit/56de8c24aad39479d09f7d499949a64573db04f1)

### Election Day

##### Add sitemap to open data documentation.

Also adds a JSON version of the sitemap.

`Feature` | [OGC-485](https://linear.app/onegovcloud/issue/OGC-485) | [6aae91e8d6](https://github.com/onegov/onegov-cloud/commit/6aae91e8d66e9c61dee381346235ccdbdbf9337f)

##### Allow application to be private.

`Feature` | [OGC-1678](https://linear.app/onegovcloud/issue/OGC-1678) | [f070906318](https://github.com/onegov/onegov-cloud/commit/f070906318a8273ca3365541804e48cda1539675)

##### Hide filters for tacit elections.

`Bugfix` | [82e2527da6](https://github.com/onegov/onegov-cloud/commit/82e2527da6ba4a1d0cc2e0a2b9645f2c1c5b1011)

### Feriennet

##### Switch to html for notification templates

`Bugfix` | [PRO-1289](https://linear.app/projuventute/issue/PRO-1289) | [0f1c65d2c6](https://github.com/onegov/onegov-cloud/commit/0f1c65d2c6e37ae7e392c9ef19fdc0282d8550ee)

### Server

##### Spawn wsgi processes instead of forking them in tests.

`Bugfix` | [OGC-1679](https://linear.app/onegovcloud/issue/OGC-1679) | [91f11b8c74](https://github.com/onegov/onegov-cloud/commit/91f11b8c741e33775a50085ec52affd1f29e46e1)

### Swissvote

##### Run swissvotes tests which manipulate the sessions locale serially

`Bugfix` | [OGC-1681](https://linear.app/onegovcloud/issue/OGC-1681) | [d0e791819f](https://github.com/onegov/onegov-cloud/commit/d0e791819fd4f3a309422970323c19f549549a82)

### User

##### Uses random salt for signup token generation

`Bugfix` | [SEA-1051](https://linear.app/seantis/issue/SEA-1051) | [ca4e50bb90](https://github.com/onegov/onegov-cloud/commit/ca4e50bb90d90faa38ce77b42ba7a9c55d0d68df)

### Various

##### Use timezone aware utcnow.

`Feature` | [OGC-1665](https://linear.app/onegovcloud/issue/OGC-1665) | [35f30d1d39](https://github.com/onegov/onegov-cloud/commit/35f30d1d39f0a83bd13f51bab5ab22d54073a6fa)

## 2024.33

`2024-06-08` | [0a0e7e6ec9...78de021837](https://github.com/OneGov/onegov-cloud/compare/0a0e7e6ec9^...78de021837)

## 2024.32

`2024-06-08` | [03612f6d30...486444c23b](https://github.com/OneGov/onegov-cloud/compare/03612f6d30^...486444c23b)

**Upgrade hints**
- Consider rotating the application and csrf secrets during upgrade
### Core

##### Fixes parsing of JSON attachments in `SMTPMailQueueProcessor`

`Bugfix` | [OGC-1667](https://linear.app/onegovcloud/issue/OGC-1667) | [51cf789ffc](https://github.com/onegov/onegov-cloud/commit/51cf789ffc05daf26e6e6642f94ffc17ac44cca8)

##### Increases security of some core constructs

This also includes a fix for `session_id`'s not being properly rotated
when they become invalid. Generally the security was high enough for
what we were using these constructs for, but this may change in the
future, so it's better to have them be as robust as possible now.

`Bugfix` | [SEA-1051](https://linear.app/seantis/issue/SEA-1051) | [d693617209](https://github.com/onegov/onegov-cloud/commit/d693617209cd22742a06b51ac31e882a9bef815b)

### Directories

##### Adds accordion layout for directories

The accordion layout maybe used for common question and answer catalogs

`Feature` | [OGC-1634](https://linear.app/onegovcloud/issue/OGC-1634) | [ed93c7d484](https://github.com/onegov/onegov-cloud/commit/ed93c7d4844cb522603fa8fd7a704904372f3ee0)

### Election Day

##### Move ballot to election day

`Feature` | [OGC-150](https://linear.app/onegovcloud/issue/OGC-150) | [0d0059a3ae](https://github.com/onegov/onegov-cloud/commit/0d0059a3ae0c9f5838af7225f01063906d9a3041)

##### Add compatibility with DCAT-AP CH Version 2.

`Feature` | [OGC-1670](https://linear.app/onegovcloud/issue/OGC-1670) | [29611a8e14](https://github.com/onegov/onegov-cloud/commit/29611a8e14cd5e78cb8c07ee0b74ccd1a41910a1)

##### Add short titles.

`Feature` | [OGC-1154](https://linear.app/onegovcloud/issue/OGC-1154) | [4ac430e072](https://github.com/onegov/onegov-cloud/commit/4ac430e07222509ee9c4817a48b4c26412e40c75)

##### Update Open Data documentation.

`Feature` | [OGC-485](https://linear.app/onegovcloud/issue/OGC-485) | [5c5351d8e5](https://github.com/onegov/onegov-cloud/commit/5c5351d8e5d6ba857d73ef0d71783abf81e6439d)

##### Distinguish between direct and indirect counter proposals.

`Feature` | [OGC-1675](https://linear.app/onegovcloud/issue/OGC-1675) | [f2ee087c1d](https://github.com/onegov/onegov-cloud/commit/f2ee087c1d50674146f559a4a10849642666e919)

##### Update open data documentation and add missing field.

`Bugfix` | [OGC-485](https://linear.app/onegovcloud/issue/OGC-485) | [6514bf2890](https://github.com/onegov/onegov-cloud/commit/6514bf2890ecb2d1a62f0b8bbf376274bdb38c1b)

##### Fix eCH enum imports.

`Bugfix` | [OGC-1671](https://linear.app/onegovcloud/issue/OGC-1671) | [87af7fb743](https://github.com/onegov/onegov-cloud/commit/87af7fb74363bcb899f81a79e6e458679740a4a4)

### Landsgemeinde

##### Add open data.

`Feature` | [OGC-1042](https://linear.app/onegovcloud/issue/OGC-1042) | [edacda3cdc](https://github.com/onegov/onegov-cloud/commit/edacda3cdccfe16544ff0fa370a39da3de84b203)

### Newsletter

##### Fix wrong breadcrumb link in newsletter import / export view

`Bugfix` | [OGC-1649](https://linear.app/onegovcloud/issue/OGC-1649) | [13555aad4f](https://github.com/onegov/onegov-cloud/commit/13555aad4f392e39d3f8d2c22a29284d44780cff)

### Search

##### Activate search cli test for command 'index-status'

`Bugfix` | [OGC-508](https://linear.app/onegovcloud/issue/OGC-508) | [ba09959b33](https://github.com/onegov/onegov-cloud/commit/ba09959b3333b60187dac15defe197cb568179ab)

### Swissvotes

##### Fix fög link.

`Bugfix` | [SWI-49](https://linear.app/swissvotes/issue/SWI-49) | [58369089ec](https://github.com/onegov/onegov-cloud/commit/58369089ec6abd30b814223b2a308f27d79e75cd)

##### Fix saving tablesaw settings to local storage.

`Bugfix` | [98945ae657](https://github.com/onegov/onegov-cloud/commit/98945ae657c27afef4d08baa46ee9ce60a235ef9)

### Tests

##### Add additional test group/split

`Feature` | [NONE](#NONE) | [42c2738fd3](https://github.com/onegov/onegov-cloud/commit/42c2738fd3128e0d0375366c72929045768f9255)

### Ticket

##### Prevent accessing 'extra_meta' if not existing in model.

This also affected the '/timeline' view when reassign activities.

`Bugfix` | [PRO-1285](https://linear.app/projuventute/issue/PRO-1285) | [4bbcf3dfa8](https://github.com/onegov/onegov-cloud/commit/4bbcf3dfa8d9ee766599e9fff8aef26e7e64a02c)

##### Display group information in case of deleted directory

`Bugfix` | [OGC-1674](https://linear.app/onegovcloud/issue/OGC-1674) | [9bcfb95351](https://github.com/onegov/onegov-cloud/commit/9bcfb953518fe410ea113d280449a0320047bd49)

### Topic

##### Adds missing trait to move links

`Bugfix` | [OGC-161](https://linear.app/onegovcloud/issue/OGC-161) | [38eb4ceb10](https://github.com/onegov/onegov-cloud/commit/38eb4ceb100a9b717b6854762c4659ebb82904f6)

### Town6

##### Fix sidebar problem in navigation

`Bugfix` | [OGC-1664](https://linear.app/onegovcloud/issue/OGC-1664) | [b13e478b14](https://github.com/onegov/onegov-cloud/commit/b13e478b14097e1cb5b7b4aa9f6a5c6734680a5c)

## 2024.31

`2024-05-24` | [669d8bb32f...b7fbb71ab0](https://github.com/OneGov/onegov-cloud/compare/669d8bb32f^...b7fbb71ab0)

### Election Day

##### Ignore incoming ballot type for simple votes.

The format should only contain results for one ballot anyway.

`Feature` | [OGC-1572](https://linear.app/onegovcloud/issue/OGC-1572) | [b0aa3bf151](https://github.com/onegov/onegov-cloud/commit/b0aa3bf15167e410ac003b11392e660f43f75b37)

##### Add the option to also clear existing ballots of a vote.

`Feature` | [OGC-1572](https://linear.app/onegovcloud/issue/OGC-1572) | [1ca68210eb](https://github.com/onegov/onegov-cloud/commit/1ca68210ebaf6683b8579ab7774fd451a16fbb9a)

### Event

##### Occurrences are now deletable when end date passed

`Feature` | [OGC-1560](https://linear.app/onegovcloud/issue/OGC-1560) | [669d8bb32f](https://github.com/onegov/onegov-cloud/commit/669d8bb32f152bce8a9737b2287cf5c8506009dd)

##### Replaces db time by sedate

`Feature` | [NONE](#NONE) | [9b4c4d895c](https://github.com/onegov/onegov-cloud/commit/9b4c4d895cc55c375167c2eaf99cc73ca480746b)

### Fsi

##### Adds link for confirmation email.

`Feature` | [OGC-1653](https://linear.app/onegovcloud/issue/OGC-1653) | [ac6c2a1be1](https://github.com/onegov/onegov-cloud/commit/ac6c2a1be122b8dd95465b40269a4da41fecb986)

### Landsgemeinde

##### Link to Liveticker during assembly

`Feature` | [OGC-1636](https://linear.app/onegovcloud/issue/OGC-1636) | [de76bf3199](https://github.com/onegov/onegov-cloud/commit/de76bf3199b9d3691bb8f984946d530f9d7d131f)

##### Redirect to ticker if assembly is active

`Feature` | [OGC-1622](https://linear.app/onegovcloud/issue/OGC-1622) | [325c2abd09](https://github.com/onegov/onegov-cloud/commit/325c2abd090958d425c46b2169a245d9351082c1)

##### Overwrite homepage rewrite if there is an ongoing assembly

`Feature` | [OGC-1621](https://linear.app/onegovcloud/issue/OGC-1621) | [b7dcf132dd](https://github.com/onegov/onegov-cloud/commit/b7dcf132ddf29b6a528e910478ec767e84876589)

##### Sidebar content in every window size

`Bugfix` | [OGC-1629](https://linear.app/onegovcloud/issue/OGC-1629) | [33b3af82e8](https://github.com/onegov/onegov-cloud/commit/33b3af82e87612a65dce33cab5564aed97ab8c54)

### Newsletter

##### Extend newsletter export by status column (confirmed)

`Feature` | [OGC-1645](https://linear.app/onegovcloud/issue/OGC-1645) | [201f97678e](https://github.com/onegov/onegov-cloud/commit/201f97678eb1bd58b73c73fad91cfe95013e5949)

### Org

##### IFrame button generating iFrame-Code

`Feature` | [WEB-42](#WEB-42) | [f92b94c797](https://github.com/onegov/onegov-cloud/commit/f92b94c797feb005a51718bf77592893f80d9772)

### Search

##### Fix search cli for index status

`Bugfix` | [OGC-508](https://linear.app/onegovcloud/issue/OGC-508) | [4da25c2ac4](https://github.com/onegov/onegov-cloud/commit/4da25c2ac4f51597f5c7e79529501e7430344fb8)

### Submission

##### Update submission title after editing

`Bugfix` | [OGC-1576](https://linear.app/onegovcloud/issue/OGC-1576) | [908964382d](https://github.com/onegov/onegov-cloud/commit/908964382d91e4f3291e29902753363da98e25cf)

### Town6

##### Move the save button for edit forms to edit bar

`Feature` | [OGC-1596](https://linear.app/onegovcloud/issue/OGC-1596) | [004cdbbac5](https://github.com/onegov/onegov-cloud/commit/004cdbbac52942e1bf45eeafc2abe72ea9837270)

## 2024.30

`2024-05-14` | [1ef85ef354...ca4867b42b](https://github.com/OneGov/onegov-cloud/compare/1ef85ef354^...ca4867b42b)

### Landsgemdeine

##### Display Timestamp for votum in ticker

`Feature` | [OGC-1624](https://linear.app/onegovcloud/issue/OGC-1624) | [d43dbcf670](https://github.com/onegov/onegov-cloud/commit/d43dbcf670bb74df925bdbe35f96b0a230921d7d)

### Landsgemeinde

##### Link agenda items in ticker to their own subpage

Agenda items, that are still "scheduled" so far had no working link. Now they are linkt to their own subpage so users can read the description even if the agenda item isn't ongoing yet.

`Feature` | [OGC-1623](https://linear.app/onegovcloud/issue/OGC-1623) | [1ef85ef354](https://github.com/onegov/onegov-cloud/commit/1ef85ef3545c000aba6050fe82cf0ecdd7315948)

##### Automaticaly fill in start time when "ongoing" is clicked in the form

`Feature` | [OGC-1626](https://linear.app/onegovcloud/issue/OGC-1626) | [db035bde73](https://github.com/onegov/onegov-cloud/commit/db035bde73c880ce114b84634c6329a6e8588b8a)

## 2024.29

`2024-05-14` | [7c8b77a2d0...972f8f5843](https://github.com/OneGov/onegov-cloud/compare/7c8b77a2d0^...972f8f5843)

**Upgrade hints**
- onegov-election-day --select /onegov_election_day/* migrate-subscribers
### Core

##### Ensures SMS spooler triggers on `onegov.core.utils.safe_move`

Previously we still triggered because we didn't ignore `.tmp` files, so
this bug was obscured.

`Bugfix` | [2ae44dacf1](https://github.com/onegov/onegov-cloud/commit/2ae44dacf104087cd25a9b4adc08459d1b9ae965)

### Election Day

##### Add notification segmentation.

If segmented_notifications is enabled for a principal, email and SMS subscribers can subscribe either to elections and votes of a specific municipality or everything else. Multiple subscriptions are possible.

`Feature` | [OGC-1150](https://linear.app/onegovcloud/issue/OGC-1150) | [d7d8195c22](https://github.com/onegov/onegov-cloud/commit/d7d8195c22530fe176230c41811d3b45b7fb907a)

##### Sort municipalities in subscription forms.

`Feature` | [OGC-1150](https://linear.app/onegovcloud/issue/OGC-1150) | [4444f815c0](https://github.com/onegov/onegov-cloud/commit/4444f815c0330c80dba0fc4ba418a6a2d621fc0c)

##### Add experimental support for eCH-0252 election compound import.

`Feature` | [OGC-1608](https://linear.app/onegovcloud/issue/OGC-1608) | [e7cdccb855](https://github.com/onegov/onegov-cloud/commit/e7cdccb855ae0bc2337996ce5f033b02f45f2f15)

### Forms

##### Left align input text with help text below for town6

`Bugfix` | [OGC-1593](https://linear.app/onegovcloud/issue/OGC-1593) | [a315bd300f](https://github.com/onegov/onegov-cloud/commit/a315bd300fa6c6d6a08af49163b4da7d8ee22236)

### Landsgemeinde

##### Links to video for vota

`Feature` | [OGC-1635](https://linear.app/onegovcloud/issue/OGC-1635) | [c7aa98c92b](https://github.com/onegov/onegov-cloud/commit/c7aa98c92bf47fcc6dcd82b2957c30e919660c33)

### Swissvotes

##### Update campaign website info button.

`Feature` | [SWI-48](https://linear.app/swissvotes/issue/SWI-48) | [0ba48e642e](https://github.com/onegov/onegov-cloud/commit/0ba48e642e41252a4eda49841dd88ce232673d13)

### Town 6

##### Fix Bug where Documents were displayed twice on resources

`Bugfix` | [OGC-1569](https://linear.app/onegovcloud/issue/OGC-1569) | [ffde31511a](https://github.com/onegov/onegov-cloud/commit/ffde31511a25d456c181400523be4e99f24911df)

## 2024.28

`2024-04-26` | [11cf0ad93b...e98118ace3](https://github.com/OneGov/onegov-cloud/compare/11cf0ad93b^...e98118ace3)

### Core

##### Avoids writing `.tmp` files to the SMS queue altogether

`Bugfix` | [1d7df063e1](https://github.com/onegov/onegov-cloud/commit/1d7df063e16e1b938da0b4e61bc51fe2ef989015)

## 2024.27

`2024-04-19` | [1dea349fd2...7fbfb3cbfe](https://github.com/OneGov/onegov-cloud/compare/1dea349fd2^...7fbfb3cbfe)

**Upgrade hints**
- onegov-election-day --select /onegov_election_day/* migrate-screens
### Election Day

##### Add JSON for screens.

`Feature` | [OGC-1591](https://linear.app/onegovcloud/issue/OGC-1591) | [c84dd22331](https://github.com/onegov/onegov-cloud/commit/c84dd2233132580fcabb14f3de710dbf899d3125)

##### Add type annotation for public vote json.

`Feature` | [OGC-1588](https://linear.app/onegovcloud/issue/OGC-1588) | [7fc0c07494](https://github.com/onegov/onegov-cloud/commit/7fc0c07494c221c649038eb48f09ade360375674)

##### Rename single word screen widgets.

`Feature` | [OGC-1589](https://linear.app/onegovcloud/issue/OGC-1589) | [4ddeca856f](https://github.com/onegov/onegov-cloud/commit/4ddeca856ff7c7be40fcc05c0ffa37ec6b069464)

##### Remove obsolete table and migration command.

`Other` | [OGC-1478](https://linear.app/onegovcloud/issue/OGC-1478) | [1dea349fd2](https://github.com/onegov/onegov-cloud/commit/1dea349fd2e9107edb6d6d1a6f0e94d000e992c7)

### Landsgemeinde

##### Automatically calculate timestamps

Timestamps get automatically calculated with the start time of the assembly and the start time of an agenda item. If a custom timestamp is given the calculated timestamp gets overwritten.

`Feature` | [OGC-1564](https://linear.app/onegovcloud/issue/OGC-1564) | [dfec2da074](https://github.com/onegov/onegov-cloud/commit/dfec2da0740cd41f6249e25c83e918f840b75de5)

##### Assembly Item displaced lines

`Bugfix` | [OGC-1566](https://linear.app/onegovcloud/issue/OGC-1566) | [e89b41a84b](https://github.com/onegov/onegov-cloud/commit/e89b41a84b0bb636525ff7733cb9a0f480fad564)

##### Convert Timestamp to seconds

YouTube Requires the timestamp as seconds. Added a utils-method to convert timestamps into seconds.

`Bugfix` | [OGC-1563](https://linear.app/onegovcloud/issue/OGC-1563) | [06e3675fd6](https://github.com/onegov/onegov-cloud/commit/06e3675fd62a2d6b97d05d19707d8e83e372b05f)

### News

##### News are now deletable when end date passed

`Bugfix` | [OGC-1560](https://linear.app/onegovcloud/issue/OGC-1560) | [4b83acb321](https://github.com/onegov/onegov-cloud/commit/4b83acb32159613c60db6ac15bc0e8c3e8271d67)

## 2024.26

`2024-04-16` | [d4483dac36...ebd814e2b5](https://github.com/OneGov/onegov-cloud/compare/d4483dac36^...ebd814e2b5)

### Event

##### Fix filter values may be displayed as single characters

`Bugfix` | [OGC-1578](https://linear.app/onegovcloud/issue/OGC-1578) | [d21a0ccfba](https://github.com/onegov/onegov-cloud/commit/d21a0ccfbab30e27ee1aebf8ac5b731095bff965)

### User

##### Extend cli for 'exists' with recursive flag in order to loop over schemas

`Feature` | [NONE](#NONE) | [a0a79622c1](https://github.com/onegov/onegov-cloud/commit/a0a79622c199d7102e44cecc1493e85f3047069b)

## 2024.25

`2024-04-16` | [f1ea705b17...0eb53b50a3](https://github.com/OneGov/onegov-cloud/compare/f1ea705b17^...0eb53b50a3)

### Election Day

##### Change relationships of party results from dynamic to lazy select.

`Feature` | [OGC-1478](https://linear.app/onegovcloud/issue/OGC-1478) | [61072947b0](https://github.com/onegov/onegov-cloud/commit/61072947b0bc09386ca0b21ced06300fad73aadb)

##### Refactor election compound relationships.

`Feature` | [OGC-1478](https://linear.app/onegovcloud/issue/OGC-1478) | [0d710f1490](https://github.com/onegov/onegov-cloud/commit/0d710f14906fe8a2fe0b56129ba6404784ae5f77)

##### Allow votes to be displayed as tie breakers.

This is a silly hack introduced by ZG and only available for them. All other principals use proper complex votes as this hack makes no sense at all.

`Feature` | [OGC-1572](https://linear.app/onegovcloud/issue/OGC-1572) | [0d34957fd5](https://github.com/onegov/onegov-cloud/commit/0d34957fd5ef79ac58ddc2f827968aad58607d3a)

### Org

##### Fix lxml usage in html annotation.

`Bugfix` | [7daa3c5347](https://github.com/onegov/onegov-cloud/commit/7daa3c53474fee24297cae3877f7e7f2e56737e9)

## 2024.24

`2024-04-12` | [776a135472...4f3b6f8f66](https://github.com/OneGov/onegov-cloud/compare/776a135472^...4f3b6f8f66)

### Org

##### Prevent negative page indexes, force to zero if necessary

`Bugfix` | [OGC-1573](https://linear.app/onegovcloud/issue/OGC-1573) | [cb72bae9e3](https://github.com/onegov/onegov-cloud/commit/cb72bae9e33226632f363cb60a6658a06c84eef0)

##### Fix adjusting registration window (end date) after first attendee confirmed

`Bugfix` | [OGC-1557](https://linear.app/onegovcloud/issue/OGC-1557) | [e8e9a1d2b9](https://github.com/onegov/onegov-cloud/commit/e8e9a1d2b9f5780cf768786029c6adee45558985)

### Swissvotes

##### Update translations.

`Feature` | [SWI-43](https://linear.app/swissvotes/issue/SWI-43) | [0cd82fb59b](https://github.com/onegov/onegov-cloud/commit/0cd82fb59b79dabdab02c38558a597766b8c540a)

##### Use separate column for BFS dashboard.

`Feature` | [SWI-46](https://linear.app/swissvotes/issue/SWI-46) | [68039c35c0](https://github.com/onegov/onegov-cloud/commit/68039c35c07d878a8dcf6ae45d634f75161ce3da)

### Town6

##### Bug Fix for hidden navigation in safari

`Bugfix` | [OGC-1570](https://linear.app/onegovcloud/issue/OGC-1570) | [776a135472](https://github.com/onegov/onegov-cloud/commit/776a1354729f0ab9dec5d7447e4008edd239a914)

## 2024.23

`2024-04-09` | [f190133e5d...74d1f1f871](https://github.com/OneGov/onegov-cloud/compare/f190133e5d^...74d1f1f871)

## 2024.22

`2024-04-09` | [09cb973ccf...30209b7988](https://github.com/OneGov/onegov-cloud/compare/09cb973ccf^...30209b7988)

### Town 6

##### Add second pagination above events

`Feature` | [1545](https://github.com/onegov/onegov-cloud/issues/1545) | [7223b1a1b2](https://github.com/onegov/onegov-cloud/commit/7223b1a1b27889c02ee8a9c1ee3d906f4389c54c)

## 2024.21

`2024-04-09` | [a1e973a06b...4dc50e0b50](https://github.com/OneGov/onegov-cloud/compare/a1e973a06b^...4dc50e0b50)

### Core

##### Introducing postgres full text search (fts) columns, indexer and orm event handler as well as db upgrade

`Feature` | [OGC-508](https://linear.app/onegovcloud/issue/OGC-508) | [57e10be96d](https://github.com/onegov/onegov-cloud/commit/57e10be96d66f704aa48082772474cf44b571d7a)

### Directories

##### Delete expired directory entries automatically if marked 'deletable'

`Feature` | [OGC-1541](https://linear.app/onegovcloud/issue/OGC-1541) | [a1e973a06b](https://github.com/onegov/onegov-cloud/commit/a1e973a06b4872df2c565648188b126174a41b98)

### Form

##### Adds missing `None` check.

`Bugfix` | [OGC-1561](https://linear.app/onegovcloud/issue/OGC-1561) | [8ae422d3a6](https://github.com/onegov/onegov-cloud/commit/8ae422d3a692b46974a2159ca94b5fab68463178)

## 2024.20

`2024-04-08` | [ad3f49975e...240dbfcc0a](https://github.com/OneGov/onegov-cloud/compare/ad3f49975e^...240dbfcc0a)

### Core

##### Avoids queuing temporary files created by `safe_move`

`Bugfix` | [11990566de](https://github.com/onegov/onegov-cloud/commit/11990566debe64530842269a4f0d96c89d854318)

##### Add realname to default local admin user.

Required if testing the feature
onegov.translator_directory.views.translator.view_mail_templates

`Other` | [OGC-1558](https://linear.app/onegovcloud/issue/OGC-1558) | [bd092e2cca](https://github.com/onegov/onegov-cloud/commit/bd092e2cca942f951d32844265c32911e0328807)

### Event

##### Resolve 'fixme' after code review

`Bugfix` | [OGC-1536](https://linear.app/onegovcloud/issue/OGC-1536) | [d4cdc0cf11](https://github.com/onegov/onegov-cloud/commit/d4cdc0cf11e53a20f8a1fe6911a44a7e5feb310c)

### Newsletter

##### Show full news in email newsletter and add option to newsletter to show full content instead of tiles only

`Feature` | [OGC-1492](https://linear.app/onegovcloud/issue/OGC-1492) | [04f6fd971e](https://github.com/onegov/onegov-cloud/commit/04f6fd971ea6cd433d1e93b7b42ea1f95f932a92)

### Org

##### Add option for adding iFrames

`Feature` | [OGC-1429](https://linear.app/onegovcloud/issue/OGC-1429) | [b6f33c4a76](https://github.com/onegov/onegov-cloud/commit/b6f33c4a763b086a437b3b21eab9814377a15b2d)

## 2024.19

`2024-03-28` | [aaa823d7d9...b238279400](https://github.com/OneGov/onegov-cloud/compare/aaa823d7d9^...b238279400)

## 2024.18

`2024-03-28` | [ed9dcdad14...8f182f3b09](https://github.com/OneGov/onegov-cloud/compare/ed9dcdad14^...8f182f3b09)

### Election Day

##### Cleanup unused code and increase test coverage.

`Feature` | [53e2a262b3](https://github.com/onegov/onegov-cloud/commit/53e2a262b3352a1ca87820d1b9bd483507b00fbc)

### Swissvotes

##### Add english bfs map link and transform bfs map url when embedding the new dashboard.

`Feature` | [SWI-46](https://linear.app/swissvotes/issue/SWI-46) | [17c12a396f](https://github.com/onegov/onegov-cloud/commit/17c12a396fd92b05af440acd1569ee38e0eb39cb)

##### Adds missing upgrade step and resolves fixmes.

`Bugfix` | [OGC-1546](https://linear.app/onegovcloud/issue/OGC-1546) | [e6401e1843](https://github.com/onegov/onegov-cloud/commit/e6401e1843ac871add5464f604c662620579be93)

##### Update display of campaign finances.

`Other` | [SWI-43](https://linear.app/swissvotes/issue/SWI-43) | [253d3bccfe](https://github.com/onegov/onegov-cloud/commit/253d3bccfe5f3697f030c8bf8c6a6eba91da9fb8)

## 2024.17

`2024-03-26` | [167b7bf9ea...254edb538b](https://github.com/OneGov/onegov-cloud/compare/167b7bf9ea^...254edb538b)

### Election Day

##### Resolve various fixmes.

`Bugfix` | [OGC-1525](https://linear.app/onegovcloud/issue/OGC-1525) | [cde18e9870](https://github.com/onegov/onegov-cloud/commit/cde18e98702f704e838114ba41548a0e1721cb2b)

### Forms

##### Adds user snippet for subfields to formcode

Feature

`Other` | [OGC-977](https://linear.app/onegovcloud/issue/OGC-977) | [c1c61d976b](https://github.com/onegov/onegov-cloud/commit/c1c61d976b9767452f629dfa5f6336ba556e5296)

### Landsgemeinde

##### Resolve various fixmes

`Bugfix` | [OGC-1535](https://linear.app/onegovcloud/issue/OGC-1535) | [196c4654fd](https://github.com/onegov/onegov-cloud/commit/196c4654fd45ac72f9069feb68ebf8c360166a16)

### Org

##### Side-panel fixes and improvements

- Added missing files sidepanel for resources and directories
- Redesigned edit-button for uploaded files

`Other` | [dd80494160](https://github.com/onegov/onegov-cloud/commit/dd804941608b6c0233593610fd876ee8af492a49)

### Swissvotes

##### Add french translations for initiator and recommendations.

`Feature` | [SWI-44](https://linear.app/swissvotes/issue/SWI-44) | [b145c2a303](https://github.com/onegov/onegov-cloud/commit/b145c2a303d79e7b4a58d4600f3bc6e5f57e1b6f)

##### Add campaign links.

`Feature` | [SWI-45](https://linear.app/swissvotes/issue/SWI-45) | [95ac77f6fe](https://github.com/onegov/onegov-cloud/commit/95ac77f6fe57e87a87e5e57c80be14762e82a286)

##### Add campaign finances.

`Feature` | [SWI-43](https://linear.app/swissvotes/issue/SWI-43) | [979352dd64](https://github.com/onegov/onegov-cloud/commit/979352dd645303f7de8e3615a79667dbeab1aeea)

##### Add link to BFS map.

`Feature` | [SWI-46](https://linear.app/swissvotes/issue/SWI-46) | [808676e5c0](https://github.com/onegov/onegov-cloud/commit/808676e5c0e38aa99126b20d12af8970354e7d56)

### Town6

##### Show RSS button always, not just if filter tags enabled.

`Feature` | [OGC-1511](https://linear.app/onegovcloud/issue/OGC-1511) | [167b7bf9ea](https://github.com/onegov/onegov-cloud/commit/167b7bf9ea83e3b6fd734f9e01d0f9684ee03fc3)

##### Remove gap above homepage video

`Bugfix` | [OGC-1522](https://linear.app/onegovcloud/issue/OGC-1522) | [a5c5571a44](https://github.com/onegov/onegov-cloud/commit/a5c5571a44e5cf818987d4315be5f9d15a6f7d90)

##### Styling of search results

`Bugfix` | [OGC-1125](https://linear.app/onegovcloud/issue/OGC-1125) | [12810ba2e4](https://github.com/onegov/onegov-cloud/commit/12810ba2e495e99c808849a976f2b06d9f665c03)

### Winterthur

##### Roadwork view misses location

`Bugfix` | [OGC-1520](https://linear.app/onegovcloud/issue/OGC-1520) | [ed130b1f13](https://github.com/onegov/onegov-cloud/commit/ed130b1f132aefb06d2bcfc6ab4f3d90bc97a3a8)

## 2024.16

`2024-03-19` | [8a532a45af...b7196b1406](https://github.com/OneGov/onegov-cloud/compare/8a532a45af^...b7196b1406)

### Agency

##### Add back translation that was removed.

`Bugfix` | [OGC-1508](https://linear.app/onegovcloud/issue/OGC-1508) | [260d09ce2a](https://github.com/onegov/onegov-cloud/commit/260d09ce2a7edc4688f702160802c124e69f21df)

### Feriennet

##### Remove offset which ignored preferred bookings if attendee is also in a group

`Bugfix` | [PRO-1262](https://linear.app/projuventute/issue/PRO-1262) | [d327fb00ee](https://github.com/onegov/onegov-cloud/commit/d327fb00ee08bcf873ccb63f78ede60f14535a7b)

### Form

##### Actually use upload limit, instead of a number

`Other` | [81b4d41267](https://github.com/onegov/onegov-cloud/commit/81b4d412670793f4b925a1721360984aae9cf3a9)

### Org

##### Delete root pages:.

`Feature` | [OGC-1108](https://linear.app/onegovcloud/issue/OGC-1108) | [0dd076c4e0](https://github.com/onegov/onegov-cloud/commit/0dd076c4e026727e2821dffc45203c3c84104c7a)

##### Adds missing translations.

`Bugfix` | [OGC-1137](https://linear.app/onegovcloud/issue/OGC-1137) | [18900b4e93](https://github.com/onegov/onegov-cloud/commit/18900b4e93e9c46f325f0fcdb185da1953f7e723)

### Pas

##### Add base models.

`Feature` | [OGC-1502](https://linear.app/onegovcloud/issue/OGC-1502) | [22e80828e6](https://github.com/onegov/onegov-cloud/commit/22e80828e6645b5daefa03b0508a554d53b9bdc2)

### Town6

##### Add missing style for chosen selects.

`Bugfix` | [8a532a45af](https://github.com/onegov/onegov-cloud/commit/8a532a45afa8a159819e63d08d5d1ebf2df070d2)

## 2024.15

`2024-03-15` | [c5e23a0e51...2fd12fd218](https://github.com/OneGov/onegov-cloud/compare/c5e23a0e51^...2fd12fd218)

### File

##### Adds compatibility with filedepot 0.11.

`Feature` | [OGC-1480](https://linear.app/onegovcloud/issue/OGC-1480) | [9efea02b1b](https://github.com/onegov/onegov-cloud/commit/9efea02b1bf0b6a30a13f807b7d379398c29b87e)

### Form

##### Add a select field which translates the choice labels.

`Feature` | [OGC-1518](https://linear.app/onegovcloud/issue/OGC-1518) | [cf68edb7ec](https://github.com/onegov/onegov-cloud/commit/cf68edb7ec1e3a018746174a8acf58685ca0eff1)

### Gis

##### Adds a geolocation button to the map input

`Feature` | [OGC-1513](https://linear.app/onegovcloud/issue/OGC-1513) | [572406c6ad](https://github.com/onegov/onegov-cloud/commit/572406c6adf9cb6d851c8a26259f1cdde42891fc)

### Org

##### Add Option for links in side-panel

`Feature` | [OGC-1321](https://linear.app/onegovcloud/issue/OGC-1321) | [bc29f9d879](https://github.com/onegov/onegov-cloud/commit/bc29f9d8799c843895697e915fdd70efa8c0ab82)

##### Fix missing translations for files in sidebar option

`Bugfix` | [OGC-1500](https://linear.app/onegovcloud/issue/OGC-1500) | [eac0af05b0](https://github.com/onegov/onegov-cloud/commit/eac0af05b0ba36c565de8587d7e1809233856c70)

##### Fix message so iOS can autofill

`Bugfix` | [OGC-1415](https://linear.app/onegovcloud/issue/OGC-1415) | [1e08464519](https://github.com/onegov/onegov-cloud/commit/1e08464519e3346eb9328f99ddbca46393b5166c)

##### Sort photo albums by newest first.

`Bugfix` | [OGC-1452](https://linear.app/onegovcloud/issue/OGC-1452) | [3ab63eb00e](https://github.com/onegov/onegov-cloud/commit/3ab63eb00e6960acfaa0b97480937d633d0fafbe)

##### Implement logic to prevent premature archiving of reservations.

Imagine a reservation made a year in advance (which happens in practice)
After a year, `ticket.last_change` would indicate it shall be archived.
However, some reservations of this ticket might be fairly recent, like a
month ago. Therefore it is a bit premature to be considered for archive.

`Bugfix` | [OGC-1481](https://linear.app/onegovcloud/issue/OGC-1481) | [9a8da1bca0](https://github.com/onegov/onegov-cloud/commit/9a8da1bca00091f7bf6d3838ab421afaaf85cd4f)

##### Bugfix of deleting files

Some files in the FileLinkExtension could not be deleted, they will return to the list if they are still linked in the text. Some files were invisibly linked in the text. This change will delete all invisible links on save and adds a command for deleting all current invisible links.

`Bugfix` | [PRO-1248](https://linear.app/projuventute/issue/PRO-1248) | [e02233f3ca](https://github.com/onegov/onegov-cloud/commit/e02233f3cac2b3ed7d5c826642f426656fa08f14)

##### Improve styling of alerts and errors.

`Bugfix` | [OGC-1517](https://linear.app/onegovcloud/issue/OGC-1517) | [d91183ca7b](https://github.com/onegov/onegov-cloud/commit/d91183ca7bf796b57ff2aa3d0514953c217ded7f)

##### Makes autofill of honeypot field in mTAN forms less likely

`Bugfix` | [OGC-1484](https://linear.app/onegovcloud/issue/OGC-1484) | [6d6eb3ae16](https://github.com/onegov/onegov-cloud/commit/6d6eb3ae168533edf7004963a0661809e90d9068)

### Tests

##### Fixing failing test

`Bugfix` | [OGC-1477](https://linear.app/onegovcloud/issue/OGC-1477) | [6956dc96b8](https://github.com/onegov/onegov-cloud/commit/6956dc96b87b7231cb46f45f5f9bf3d10b76d659)

### Town6

##### Allow generic search results without a lead.

`Feature` | [34f5a9580a](https://github.com/onegov/onegov-cloud/commit/34f5a9580a1452e4c8d340f5313c3160f2ae1ca4)

##### Add RSS to news (#1236)

`Feature` | [OGC-1512](https://linear.app/onegovcloud/issue/OGC-1512) | [fae58f3a9a](https://github.com/onegov/onegov-cloud/commit/fae58f3a9a6da931b6f4ed8f7cea1334b683a320)

##### Remove newline between icon and text

`Bugfix` | [OGC-1501](https://linear.app/onegovcloud/issue/OGC-1501) | [cd7e306b4b](https://github.com/onegov/onegov-cloud/commit/cd7e306b4be51587acdd8c289dba52b3ac12a263)

##### Use closure to capture free variables

`Bugfix` | [OGC-1255](https://linear.app/onegovcloud/issue/OGC-1255) | [088d5fc19f](https://github.com/onegov/onegov-cloud/commit/088d5fc19f479eea29beee1a0e9ce271dd42fe0e)

## 2024.14

`2024-03-08` | [39058784ad...c181f4f875](https://github.com/OneGov/onegov-cloud/compare/39058784ad^...c181f4f875)

## 2024.13

`2024-03-08` | [63430a80b0...1b15796fc5](https://github.com/OneGov/onegov-cloud/compare/63430a80b0^...1b15796fc5)

## 2024.12

`2024-03-08` | [1d64c923a1...c9d492e36a](https://github.com/OneGov/onegov-cloud/compare/1d64c923a1^...c9d492e36a)

### Election Day

##### Improve relationships of elections.

Uses lazy relationships for election models.

`Feature` | [OGC-1478](https://linear.app/onegovcloud/issue/OGC-1478) | [d0766448db](https://github.com/onegov/onegov-cloud/commit/d0766448db4eeb1117f47879ebaaa0d1c8344044)

##### Add experimental eCH-0252 import for elections.

`Feature` | [OGC-1172](https://linear.app/onegovcloud/issue/OGC-1172) | [047da42ae9](https://github.com/onegov/onegov-cloud/commit/047da42ae9b8a0bea2c977dadedf22a725b950b7)

### Org

##### Per page option to switch off showing files in the sidebar

`Feature` | [OGC-1477](https://linear.app/onegovcloud/issue/OGC-1477) | [1d64c923a1](https://github.com/onegov/onegov-cloud/commit/1d64c923a12c9236447887c8c5511f9f309c51a1)

## 2024.11

`2024-03-07` | [fa71605125...cb806d1926](https://github.com/OneGov/onegov-cloud/compare/fa71605125^...cb806d1926)

### Core

##### Avoids SMS spooler stopping after encountering exceptions

`Bugfix` | [fb47347bc8](https://github.com/onegov/onegov-cloud/commit/fb47347bc8dde8ea26cd7ca280fd88565190bbb2)

### Election Day

##### Improves relationship loading for votes, ballots and ballots result.

Uses joined loading for ballots, lazy loading for ballot results.

`Feature` | [OGC-1478](https://linear.app/onegovcloud/issue/OGC-1478) | [fa71605125](https://github.com/onegov/onegov-cloud/commit/fa71605125f4dd5a7f00ccb71f93ca1a1d8786f9)

##### Updates experimental eCH-0252 Import for Votes.

`Feature` | [OGC-1152](https://linear.app/onegovcloud/issue/OGC-1152) | [43a93acde2](https://github.com/onegov/onegov-cloud/commit/43a93acde29038f272997eafeca68fbfd65243de)

##### Remove obsolete election compound creation.

`Feature` | [OGC-168](https://linear.app/onegovcloud/issue/OGC-168) | [42836e725e](https://github.com/onegov/onegov-cloud/commit/42836e725e2e97d311dce312b3c8402b68ee215b)

##### Remove websocket notifications.

`Feature` | [OGC-1494](https://linear.app/onegovcloud/issue/OGC-1494) | [50af518e2d](https://github.com/onegov/onegov-cloud/commit/50af518e2dd565459b4272a6760732190dd2f331)

##### Optionally keep candidates, lists and list connections when clearing results.

`Feature` | [OGC-1478](https://linear.app/onegovcloud/issue/OGC-1478) | [0c920edfd2](https://github.com/onegov/onegov-cloud/commit/0c920edfd28dedd52ddaaa2a7198c7f34f5b0cb8)

### Form

##### Increase Upload limit to 50MB

`Bugfix` | [OGC-1498](https://linear.app/onegovcloud/issue/OGC-1498) | [07dce87114](https://github.com/onegov/onegov-cloud/commit/07dce87114d35391f456cf555f80b61828f83245)

### Town6

##### Add description for all homepage widgets

`Feature` | [ae473461d4](https://github.com/onegov/onegov-cloud/commit/ae473461d435487f97775eafe110b038fb383985)

## 2024.10

`2024-03-04` | [025b142f8e...34862b137f](https://github.com/OneGov/onegov-cloud/compare/025b142f8e^...34862b137f)

### Election Day

##### Remove obsolete import formats.

`Feature` | [OGC-1479](https://linear.app/onegovcloud/issue/OGC-1479) | [025b142f8e](https://github.com/onegov/onegov-cloud/commit/025b142f8e394a8a256becf5d154edc19ea1a3f7)

### Org

##### Pinning pycurl to 7.45.2

pycurl/pycurl#834

`Hotfix` | [42668819a3](https://github.com/onegov/onegov-cloud/commit/42668819a37c18a6556851bb24308480bf86a777)

## 2024.9

`2024-03-01` | [b83c467389...0fe9e974cd](https://github.com/OneGov/onegov-cloud/compare/b83c467389^...0fe9e974cd)

### Core

##### Adds horizontal movement and history to the shell.

`Feature` | [b422b58bef](https://github.com/onegov/onegov-cloud/commit/b422b58bef203cbe859332ce853ab89160a18d9a)

### Directory

##### Fixes key error for keyword extraction in directory configuration

`Bugfix` | [OGC-1475](https://linear.app/onegovcloud/issue/OGC-1475) | [ddcb7262be](https://github.com/onegov/onegov-cloud/commit/ddcb7262beedab59f2c0e30751e9a5eabab27f03)

### Election Day

##### Remove experimental eCH-0252 export.

`Feature` | [OGC-1151](https://linear.app/onegovcloud/issue/OGC-1151) | [00a13c0f3a](https://github.com/onegov/onegov-cloud/commit/00a13c0f3ac9f810f5798ac15e635cee734844eb)

### Feriennet

##### Occasion: Fix omitting verification of max age must be higher than min age for max age

max age higher than min age check can be omitted by setting max age to 0 (zero)

`Bugfix` | [OGC-1257](https://linear.app/onegovcloud/issue/OGC-1257) | [008ecacdf5](https://github.com/onegov/onegov-cloud/commit/008ecacdf5a4d677b4ae3a9d51965bf0ab89f8e6)

### File

##### Prevent duplicate `Cache-Control` headers.

`Bugfix` | [OGC-1476](https://linear.app/onegovcloud/issue/OGC-1476) | [f68ce1ac0d](https://github.com/onegov/onegov-cloud/commit/f68ce1ac0df4d8f7a9e3cf7fd1b27604982dc49d)

### Form

##### Adds icon in front of filename

`Feature` | [OGC-1393](https://linear.app/onegovcloud/issue/OGC-1393) | [3258886a82](https://github.com/onegov/onegov-cloud/commit/3258886a828fd78f79c834766cf640838e7b9f8e)

### Org

##### Sort photoalbums by creation date.

`Feature` | [OGC-1452](https://linear.app/onegovcloud/issue/OGC-1452) | [58e7dca541](https://github.com/onegov/onegov-cloud/commit/58e7dca541609fc7f5b29c5014730c2136c96fd0)

##### Reduce number of queries.

`Bugfix` | [OGC-1455](https://linear.app/onegovcloud/issue/OGC-1455) | [164d4b7e71](https://github.com/onegov/onegov-cloud/commit/164d4b7e71c4ce1619918072e8d83cae8bbbf8c1)

### Town6

##### Option to define own Chat-Topics

`Feature` | [OGC-1457](https://linear.app/onegovcloud/issue/OGC-1457) | [c750093d53](https://github.com/onegov/onegov-cloud/commit/c750093d53fd8d12ea88d51d5a9b8e69a0417b79)

##### Option for title on image for focus widget

`Feature` | [OGC-1445](https://linear.app/onegovcloud/issue/OGC-1445) | [895a02097f](https://github.com/onegov/onegov-cloud/commit/895a02097ffeff1f5c33e6511747d933fdb59ba5)

## 2024.8

`2024-02-16` | [61d0b56270...d9dcaa19fe](https://github.com/OneGov/onegov-cloud/compare/61d0b56270^...d9dcaa19fe)

### Election Day

##### Add answer by ballot type to export.

`Feature` | [7cd873e8aa](https://github.com/onegov/onegov-cloud/commit/7cd873e8aaa5262fd8b34c4274bb72a19d30e4b8)

##### Sort entities tables widgets by names.

`Feature` | [OGC-1466](https://linear.app/onegovcloud/issue/OGC-1466) | [c0d4192c6b](https://github.com/onegov/onegov-cloud/commit/c0d4192c6b3f7da3dfbee0894a0070bf808bfc2f)

##### Fix JSON views.

`Bugfix` | [7dd0a647fd](https://github.com/onegov/onegov-cloud/commit/7dd0a647fd6c0de71825e7d57f19157032984013)

##### Fixes eCH-0252 domain identification for cantons.

`Bugfix` | [ba76c573ab](https://github.com/onegov/onegov-cloud/commit/ba76c573ab8e5e24bfdd13f07bb1cc523e846741)

##### Avoid loading browser-cached group screens.

`Bugfix` | [OGC-1467](https://linear.app/onegovcloud/issue/OGC-1467) | [eb59632925](https://github.com/onegov/onegov-cloud/commit/eb5963292587165f0fea47aeae34230c57b4ccf2)

### Feriennet

##### Fix error when deleting prebooking date

`Bugfix` | [PRO-1244](https://linear.app/projuventute/issue/PRO-1244) | [a0a262000c](https://github.com/onegov/onegov-cloud/commit/a0a262000c28367022904762442111999cf04458)

##### Rename CLI method

`Bugfix` | [PRO-1237](https://linear.app/projuventute/issue/PRO-1237) | [3c5e8ddd6e](https://github.com/onegov/onegov-cloud/commit/3c5e8ddd6e36cb7bc65bcf9bf4007291adf00cc3)

### Landsgemeinde

##### Add agenda item start time.

`Feature` | [OGC-1304](https://linear.app/onegovcloud/issue/OGC-1304) | [14fd64d989](https://github.com/onegov/onegov-cloud/commit/14fd64d9892a97cc0704cd7b5afbc3d2e80fd600)

##### Only preload metadata of mp3.

`Feature` | [ff7769c264](https://github.com/onegov/onegov-cloud/commit/ff7769c2642a5fddcf53745607622559256bb997)

### Org

##### Adds option to Topics and News to show people on bottom of main page instead of sidebar

`Feature` | [OGC-1454](https://linear.app/onegovcloud/issue/OGC-1454) | [e641db1512](https://github.com/onegov/onegov-cloud/commit/e641db15128b3e337e1fa28b296a902a7a80b252)

##### Reservation note is always shown and adjusted to inform user multiple selections are possible

`Feature` | [OGC-1450](https://linear.app/onegovcloud/issue/OGC-1450) | [f2dfceab9e](https://github.com/onegov/onegov-cloud/commit/f2dfceab9e63ab3be2811bc327c3095a8fd1f7da)

##### Adds support for videos in directory entries

`Feature` | [OGC-1408](https://linear.app/onegovcloud/issue/OGC-1408) | [6ddc85ec7a](https://github.com/onegov/onegov-cloud/commit/6ddc85ec7ab67882a7a58f21dff2bcfb4de1c8e2)

##### Fixed unpublished news invisible for admins

News with a start date in the future were completely hidden in the news overview. Even admins couldn't see them.

`Bugfix` | [PRO-1246](https://linear.app/projuventute/issue/PRO-1246) | [c3b208846d](https://github.com/onegov/onegov-cloud/commit/c3b208846d42d59ac7e6e4bfdfdbae57b158e7fa)

## 2024.7

`2024-02-07` | [8e2c4fa844...5532e11628](https://github.com/OneGov/onegov-cloud/compare/8e2c4fa844^...5532e11628)

### Agency

##### Load agency content in API.

Avoids N+1 queries.

`Bugfix` | [c1334efee4](https://github.com/onegov/onegov-cloud/commit/c1334efee4fbef92e7749ad827e05a2e43221864)

### Election Day

##### Use official municipalitites and maps for 2024.

`Feature` | [OGC-1280](https://linear.app/onegovcloud/issue/OGC-1280) | [8e2c4fa844](https://github.com/onegov/onegov-cloud/commit/8e2c4fa844585c47764eb7a2bd8b269dcd90bf70)

##### Remove lexwork PDF signing.

`Feature` | [OGC-1421](https://linear.app/onegovcloud/issue/OGC-1421) | [df88a84a8a](https://github.com/onegov/onegov-cloud/commit/df88a84a8a285b51c4b193edad130e097071d6b3)

##### Add ID to internal exports.

`Feature` | [OGC-1459](https://linear.app/onegovcloud/issue/OGC-1459) | [d4c6e2092d](https://github.com/onegov/onegov-cloud/commit/d4c6e2092d7d507cee00bafa27d2078a147c6e84)

##### Add country validator to SMS subscriber form.

`Feature` | [OGC-1460](https://linear.app/onegovcloud/issue/OGC-1460) | [712915c63c](https://github.com/onegov/onegov-cloud/commit/712915c63c51df32b5f68041173c9d26f6aaae36)

##### Update translations.

`Feature` | [OGC-905](https://linear.app/onegovcloud/issue/OGC-905) | [901dcd7b10](https://github.com/onegov/onegov-cloud/commit/901dcd7b102f0c7d9075238681cc045fb8c32f4b)

##### Add heatmap captions and clearify the related view titles.

`Feature` | [OGC-1279](https://linear.app/onegovcloud/issue/OGC-1279) | [0437d9a422](https://github.com/onegov/onegov-cloud/commit/0437d9a422549fb28a594fc01dbb77495339a4b6)

##### Add answer to internal export.

`Feature` | [OGC-1461](https://linear.app/onegovcloud/issue/OGC-1461) | [79ef61c250](https://github.com/onegov/onegov-cloud/commit/79ef61c250cf54f2443c110fb19c9e459fb081c2)

##### Add party results to archive.

`Feature` | [OGC-877](https://linear.app/onegovcloud/issue/OGC-877) | [9191b9d9a1](https://github.com/onegov/onegov-cloud/commit/9191b9d9a10c463f723778835e5ce17777a1cc90)

### Event

##### Load event content before ical export.

Avoids N+1 queries.

`Bugfix` | [7bba1f5c4e](https://github.com/onegov/onegov-cloud/commit/7bba1f5c4ed8c0c47f16cd778da0612036fe3867)

### Feriennet

##### Fix day labels

Add CLI for re-calculating occasion durations, filter for current period only.

`Bugfix` | [PRO-1237](https://linear.app/projuventute/issue/PRO-1237) | [9de9ee1262](https://github.com/onegov/onegov-cloud/commit/9de9ee1262b09752850c89e016f35c75c1b9c8e3)

### Org

##### Don't redirect to the mTAN view if the view cannot be accessed

E.g. in the case of a view with a publication the mTAN check would
happen even when the object isn't published, so you would do the
authentication only to then be greeted with a 403 error.

`Bugfix` | [OGC-1451](https://linear.app/onegovcloud/issue/OGC-1451) | [0df1b828e0](https://github.com/onegov/onegov-cloud/commit/0df1b828e066e38228aad5a978541eae7eb07cc7)

### Town6

##### Add Chat Archive

`Feature` | [9d9f0c516c](https://github.com/onegov/onegov-cloud/commit/9d9f0c516ce54823557b86523453534b5018ab2c)

## 2024.6

`2024-02-05` | [a97af2900a...5d723fdb5d](https://github.com/OneGov/onegov-cloud/compare/a97af2900a^...5d723fdb5d)

### Town6

##### Adds option to Topics and News to show people on bottom of main page instead of sidebar

`Feature` | [OGC-1454](https://linear.app/onegovcloud/issue/OGC-1454) | [a97af2900a](https://github.com/onegov/onegov-cloud/commit/a97af2900a49c8d45498985873d58dec7ca941f3)

## 2024.5

`2024-02-02` | [0246e2c3ec...b231f4dc93](https://github.com/OneGov/onegov-cloud/compare/0246e2c3ec^...b231f4dc93)

### Feriennet

##### Update Banner

`Feature` | [PRO-1238](https://linear.app/projuventute/issue/PRO-1238) | [61b3721283](https://github.com/onegov/onegov-cloud/commit/61b372128372ea4c8d7d4b33d16fcc7626c9e397)

##### Delete rule that hides last navigation Element

`Feature` | [PRO-1239](https://linear.app/projuventute/issue/PRO-1239) | [0c50f032cc](https://github.com/onegov/onegov-cloud/commit/0c50f032cc2e9020573b55fbfb768d85372ab72d)

### Org

##### Protect `DirectoryFile` when linked to an entry with mTAN access

Previously we relied on file links being impossible to predict, but
since someone still may maliciously share a link, we're better off
actually protecting the file in simple cases like this.

`Feature` | [OGC-1428](https://linear.app/onegovcloud/issue/OGC-1428) | [45369e511b](https://github.com/onegov/onegov-cloud/commit/45369e511b2fe9d88ce88931b36b5e605d5504ab)

##### Adds reservation details to initial reservation email

`Feature` | [OGC-1334](https://linear.app/onegovcloud/issue/OGC-1334) | [88c7597c18](https://github.com/onegov/onegov-cloud/commit/88c7597c18589c360f310d2df4ae411674d10c5b)

##### Adds reservation details to initial reservation email

`Feature` | [OGC-1334](https://linear.app/onegovcloud/issue/OGC-1334) | [374f35cfc2](https://github.com/onegov/onegov-cloud/commit/374f35cfc2d5a058ebfc7a511dd26f7b17780b5a)

##### Change directory url independent of name.

`Feature` | [OGC-110](https://linear.app/onegovcloud/issue/OGC-110) | [254ea44fc7](https://github.com/onegov/onegov-cloud/commit/254ea44fc72bc8c8f4362ab19304a0d1ed1eaa95)

##### Allows uploaded files to appear in public search results more often

Previously only files marked as a publication would appear in search
results, but now it will also check for any public objects linking to the
file in which case it will appear in the search results as well.

This also creates an explicit link for any files linked within a object's
content (usually its text field).

`Feature` | [OGC-921](https://linear.app/onegovcloud/issue/OGC-921) | [2008047aa3](https://github.com/onegov/onegov-cloud/commit/2008047aa324d47f96ccd0aa1eb8326bd7eda806)

##### Automated ticket archival/deletion scheduled based on last change

Previously this was scheduled based on ticket creation date, but this
can lead to erratic behavior when closing old tickets.

`Bugfix` | [OGC-1426](https://linear.app/onegovcloud/issue/OGC-1426) | [16497083f7](https://github.com/onegov/onegov-cloud/commit/16497083f7497c945af3871b9739f599b67ab3a8)

### Reservation

##### Reservation ticket now have a link to the resource

`Feature` | [1fb1e2356e](https://github.com/onegov/onegov-cloud/commit/1fb1e2356e12cb9ff63533282fb284fc79c570f9)

### Town6

##### Add field for event registration URL

`Feature` | [OGC-1420](https://linear.app/onegovcloud/issue/OGC-1420) | [08ded58541](https://github.com/onegov/onegov-cloud/commit/08ded585411bd69b260bd87608ab9da88556879f)

##### Adjustable opening hours for chat

`Feature` | [7204f93b85](https://github.com/onegov/onegov-cloud/commit/7204f93b855ed1532f2aa9020fd688d193cc1666)

##### Fixes another incorrect icon.

`Bugfix` | [0246e2c3ec](https://github.com/onegov/onegov-cloud/commit/0246e2c3ecd81dc9188ae3cbc76e486ee9a3664e)

##### Fix hidden sidebar-toggler

`Bugfix` | [OGC-1422](https://linear.app/onegovcloud/issue/OGC-1422) | [fa52f584b8](https://github.com/onegov/onegov-cloud/commit/fa52f584b8b8fae5c6c21742386db593bc9a118c)

## 2024.4

`2024-01-19` | [d94ed32687...50ffc2f66d](https://github.com/OneGov/onegov-cloud/compare/d94ed32687^...50ffc2f66d)

### Org

##### Shorten mTAN message.

`Feature` | [OGC-1415](https://linear.app/onegovcloud/issue/OGC-1415) | [22973c83fe](https://github.com/onegov/onegov-cloud/commit/22973c83fea7f3fc3da4a34fa001a3477cc76c93)

### Town 6

##### Adjust width of left column for more map space

`Feature` | [OGC-1414](https://linear.app/onegovcloud/issue/OGC-1414) | [4f1a129a20](https://github.com/onegov/onegov-cloud/commit/4f1a129a200c3c8b8127c994024f3a483f128fc3)

### Town6

##### Editor Form Translation

`Feature` | [OGC-1402](https://linear.app/onegovcloud/issue/OGC-1402) | [ea2d44bbf7](https://github.com/onegov/onegov-cloud/commit/ea2d44bbf7cf0816675db77dc1cd2b956d9a7346)

##### Optimize print view

Make print view more readable (and printable)

`Bugfix` | [OGC-822](https://linear.app/onegovcloud/issue/OGC-822) | [2477e41fc0](https://github.com/onegov/onegov-cloud/commit/2477e41fc0157cee88e01a9c627a8e1ae5566a78)

##### Cleanup

Cleaning up CSS and HTML Templates, removing unused code.

`Other` | [5a3f3463e6](https://github.com/onegov/onegov-cloud/commit/5a3f3463e67ff3ef30c799a5442e621781cd875e)

##### Fix icon.

`Bugfix` | [OGC-1418](https://linear.app/onegovcloud/issue/OGC-1418) | [ab98959387](https://github.com/onegov/onegov-cloud/commit/ab98959387e65917e08072c25122e3922ce78727)

### Winterthur

##### Increases logging for roadworks PDB curl request.

`Bugfix` | [OGC-1370](https://linear.app/onegovcloud/issue/OGC-1370) | [82800c6d50](https://github.com/onegov/onegov-cloud/commit/82800c6d501ca9542a49f64d20585542f6a60897)

## 2024.3

`2024-01-16` | [67940f955e...9ed1e1a708](https://github.com/OneGov/onegov-cloud/compare/67940f955e^...9ed1e1a708)

### Org

##### Sorts rendered `UploadMultipleField` in template macros

Previous solution caused labels and links to go out of sync

`Bugfix` | [OGC-1410](https://linear.app/onegovcloud/issue/OGC-1410) | [4490106343](https://github.com/onegov/onegov-cloud/commit/4490106343bd57daf1f530699ff19c0e1963dbf1)

### Topics

##### Prevents topics can be moved under a news page

`Bugfix` | [OGC-1282](https://linear.app/onegovcloud/issue/OGC-1282) | [67940f955e](https://github.com/onegov/onegov-cloud/commit/67940f955e98c2c2290ea9bdebe8d536f42fe644)

### Town 6

##### People Display

Use two columns to display people and don't display icons if person has no image.

`Feature` | [OGC-1353](https://linear.app/onegovcloud/issue/OGC-1353) | [afac081def](https://github.com/onegov/onegov-cloud/commit/afac081def7c83cb130e868e9eb1e6658415d3c2)

### Town6

##### Fix missing `MTANAuth` view

`Bugfix` | [OGC-1401](https://linear.app/onegovcloud/issue/OGC-1401) | [3c51955881](https://github.com/onegov/onegov-cloud/commit/3c5195588146cf47616d549d7089b2a7b63500c9)

## 2024.2

`2024-01-12` | [f1d8178342...bafd66f93e](https://github.com/OneGov/onegov-cloud/compare/f1d8178342^...bafd66f93e)

### Org

##### Adds an internal notes field to directory entries

`Feature` | [OGC-1403](https://linear.app/onegovcloud/issue/OGC-1403) | [bbeb771f86](https://github.com/onegov/onegov-cloud/commit/bbeb771f86a1933c7b73958ef1357fecaa3a7c4c)

##### Shortens URL used in mTAN SMS

`Bugfix` | [OGC-1401](https://linear.app/onegovcloud/issue/OGC-1401) | [06f489d75f](https://github.com/onegov/onegov-cloud/commit/06f489d75fa5739a83bf2e30c713ab216507fe28)

### Town6

##### Make newlines possible in lead.

`Feature` | [OGC-1328](https://linear.app/onegovcloud/issue/OGC-1328) | [11cf90d104](https://github.com/onegov/onegov-cloud/commit/11cf90d1041d17ebb7aa4b11ad7289bc6a726521)

##### Sidebar fix

Use different script for fixed sidebar on scroll.

`Bugfix` | [OGC-1390](https://linear.app/onegovcloud/issue/OGC-1390) | [d6ccc6b274](https://github.com/onegov/onegov-cloud/commit/d6ccc6b2746c508f60e089259a1e5a50cd098fa2)

## 2024.1

`2024-01-05` | [3e39a88295...42efb33f07](https://github.com/OneGov/onegov-cloud/compare/3e39a88295^...42efb33f07)

### Org

##### Don't send an mTAN report if no mTANs have been created

`Bugfix` | [OGC-1340](https://linear.app/onegovcloud/issue/OGC-1340) | [1d92659e8b](https://github.com/onegov/onegov-cloud/commit/1d92659e8b79f5de8b82e6f087c6719922fa3070)

### Topics

##### Extend feature 'western name order' to resources and default variable in template

`Bugfix` | [OGC-1383](https://linear.app/onegovcloud/issue/OGC-1383) | [d67dbc756f](https://github.com/onegov/onegov-cloud/commit/d67dbc756f14d0756ca52c4af453191c64b8ce54)

## 2023.63

`2023-12-22` | [ceb6766745...e75dab14a2](https://github.com/OneGov/onegov-cloud/compare/ceb6766745^...e75dab14a2)

### Directory

##### Avoids `AttributeError` on entry with multiple files

`Bugfix` | [OGC-1378](https://linear.app/onegovcloud/issue/OGC-1378) | [ff6bb2dbf8](https://github.com/onegov/onegov-cloud/commit/ff6bb2dbf8ad60ebf4b39ec1dafcaaf76aa56bf3)

### Form

##### Sorts files by name when displaying a `MultipleUploadField`

`Feature` | [OGC-1392](https://linear.app/onegovcloud/issue/OGC-1392) | [682460c455](https://github.com/onegov/onegov-cloud/commit/682460c45597b4a0c8970501d60351762caea38f)

### Org

##### Show QRCode in directory entries

`Feature` | [OGC-1333](https://linear.app/onegovcloud/issue/OGC-1333) | [b335d3b9a4](https://github.com/onegov/onegov-cloud/commit/b335d3b9a43e6e8f71442da6d7e25490bb34026c)

##### Restrict mTAN access to numbers from CH, AT, DE, FR, IT, LI

`Feature` | [OGC-1391](https://linear.app/onegovcloud/issue/OGC-1391) | [31a3dd260b](https://github.com/onegov/onegov-cloud/commit/31a3dd260bd7fb57d158ab1d11f1bdd5ed998779)

##### Adds minimal mTAN reporting for billing purposes

This also increases the data retention period on TAN objects

`Feature` | [OGC-1340](https://linear.app/onegovcloud/issue/OGC-1340) | [bb51ef4c07](https://github.com/onegov/onegov-cloud/commit/bb51ef4c07fbe2a7e50b25d914f2cb94883509b5)

##### Fix marker visibility in directories for new access types

`Bugfix` | [OGC-1395](https://linear.app/onegovcloud/issue/OGC-1395) | [edf7be212d](https://github.com/onegov/onegov-cloud/commit/edf7be212db5ef1fc6a46e5f3d2b63be569a998a)

### Topics

##### For each topic, one can choose between 'eastern' and 'western' name order for listed persons

eastern order: family name, given name
western order: given name, family name

`Feature` | [OGC-1383](https://linear.app/onegovcloud/issue/OGC-1383) | [3b3b08f5ce](https://github.com/onegov/onegov-cloud/commit/3b3b08f5ced9d8e142ef18174f32376a69dfc2f0)

### Town

##### Submissions are now ordered by name

`Feature` | [OGC-1345](https://linear.app/onegovcloud/issue/OGC-1345) | [d6b4438fe0](https://github.com/onegov/onegov-cloud/commit/d6b4438fe038d16a980bee7973c7c566e67cf14e)

## 2023.62

`2023-12-12` | [a6bf5cf964...a780435e85](https://github.com/OneGov/onegov-cloud/compare/a6bf5cf964^...a780435e85)

### Directories

##### Fix typo in translation in directory export view

`Bugfix` | [OGC-1348](https://linear.app/onegovcloud/issue/OGC-1348) | [1fb939568d](https://github.com/onegov/onegov-cloud/commit/1fb939568d35c6a4fd2619b4de9e123c5319c1e8)

### Directory

##### Fixes `MultipleFileinputField` not working in archives

`Bugfix` | [8668917b4f](https://github.com/onegov/onegov-cloud/commit/8668917b4f5684a33b60091e0665701c6486dabd)

### Election Day

##### Fixes ElectionCompound not being used for export.

`Bugfix` | [OGC-1342](https://linear.app/onegovcloud/issue/OGC-1342) | [aa7ec31486](https://github.com/onegov/onegov-cloud/commit/aa7ec3148662b7c674616cfa3fa5a24ae34cb0e5)

### Landsgemeinde

##### Logo and search placement

Place search in navigation and move logo to the right

`Feature` | [OGC-1288](https://linear.app/onegovcloud/issue/OGC-1288) | [ad58620539](https://github.com/onegov/onegov-cloud/commit/ad5862053949721e53823a1846eb73280ebadf37)

### Org

##### Send assign ticket email regardless of its notification settings.

`Feature` | [OGC-1138](https://linear.app/onegovcloud/issue/OGC-1138) | [8325f801c0](https://github.com/onegov/onegov-cloud/commit/8325f801c0388910415b3611f0f900af901781eb)

##### Show QRCode in directories.

`Feature` | [OGC-1333](https://linear.app/onegovcloud/issue/OGC-1333) | [914f7ca83c](https://github.com/onegov/onegov-cloud/commit/914f7ca83cdff3cf670ff6928aece43953abf346)

##### Adds BCC field and attachments to Messages.

`Feature` | [OGC-982](https://linear.app/onegovcloud/issue/OGC-982) | [1b94df97f1](https://github.com/onegov/onegov-cloud/commit/1b94df97f18bd454e9027309c45836ad688542e5)

##### Show the fact that a batch email has been sent in ticket.

`Feature` | [OGC-1301](https://linear.app/onegovcloud/issue/OGC-1301) | [0bfb175214](https://github.com/onegov/onegov-cloud/commit/0bfb175214aa1b751bf30183d30cd9f33f098f27)

##### Adds new UserGroup functionality for directory.

`Feature` | [OGC-1265](https://linear.app/onegovcloud/issue/OGC-1265) | [8cd0c5fc0b](https://github.com/onegov/onegov-cloud/commit/8cd0c5fc0bd65f550dc1f953fcfef8b59758b8cd)

##### Fixes Subject header of rejected reservation email.

`Bugfix` | [OGC-1347](https://linear.app/onegovcloud/issue/OGC-1347) | [15fe64fc29](https://github.com/onegov/onegov-cloud/commit/15fe64fc29eb28510e0b780cc7c8e7c84ac4c22d)

### People

##### Prevent index error and allow multi word community name

`Bugfix` | [OGC-1349](https://linear.app/onegovcloud/issue/OGC-1349) | [bc717a18be](https://github.com/onegov/onegov-cloud/commit/bc717a18becbd6d537b2d8c203a8279d25d61bf5)

### Reservations

##### Show pending approval tool tip only if reservation pending

`Bugfix` | [OGC-1338](https://linear.app/onegovcloud/issue/OGC-1338) | [a6bf5cf964](https://github.com/onegov/onegov-cloud/commit/a6bf5cf964e03046d845306219506e3884a112c3)

### Town6

##### Scrollbar on open navigation

Scrollbar in Safari and Chrome now looks nicer when you open the navigation and it gets longer than the page. Also there is no vertical scrollbar anymore if you open the menu.

`Feature` | [OGC-1258](https://linear.app/onegovcloud/issue/OGC-1258) | [a73b14009c](https://github.com/onegov/onegov-cloud/commit/a73b14009cb8873c0c39ef37d89a58eba5f669b4)

##### Add option for header images

Adds option to set the page images as fullscreen header images instead of content images.

`Feature` | [OGC-1202](https://linear.app/onegovcloud/issue/OGC-1202) | [c1e978775c](https://github.com/onegov/onegov-cloud/commit/c1e978775c46de87a3e0822d998fb21525b096f3)

##### Various fixes for chat

`Bugfix` | [27e97f6e34](https://github.com/onegov/onegov-cloud/commit/27e97f6e34890b732ecf900db4e46135b182cc2f)

##### Editor-Toolbar Position

`Bugfix` | [OGC-1315](https://linear.app/onegovcloud/issue/OGC-1315) | [2301997399](https://github.com/onegov/onegov-cloud/commit/2301997399113af660f43054fc638dd96c13fe88)

##### Some hover effect fixes

`Bugfix` | [e212b9f654](https://github.com/onegov/onegov-cloud/commit/e212b9f65420154c0560dc4b8221884ec51e8405)

##### Editor toolbar

Fix position of toolbar according to header-size

`Bugfix` | [OGC-1315](https://linear.app/onegovcloud/issue/OGC-1315) | [f5020c71f7](https://github.com/onegov/onegov-cloud/commit/f5020c71f74d95aa5cc6070caac948281e1dffa5)

##### Fix sidebar overlapping footer

`Bugfix` | [OGC-1341](https://linear.app/onegovcloud/issue/OGC-1341) | [77296f796d](https://github.com/onegov/onegov-cloud/commit/77296f796d3a7318b9cde80e25be6bb01e51a319)

##### Resizing of video and slider according to navigation height

`Bugfix` | [2d75dd31ca](https://github.com/onegov/onegov-cloud/commit/2d75dd31cabb2239ecfc5699f546f9fb1e45578e)

## 2023.61

`2023-11-20` | [e4dc73f14a...1373c4a408](https://github.com/OneGov/onegov-cloud/compare/e4dc73f14a^...1373c4a408)

### Town6

##### Add translations and fix schema-problem with chat server

`Bugfix` | [d6b36df22f](https://github.com/onegov/onegov-cloud/commit/d6b36df22fa4d2fa1b10e4ebf64fa52bd0b0b04e)

##### Remove Gray line at top of page

`Bugfix` | [OGC-1268](https://linear.app/onegovcloud/issue/OGC-1268) | [d4a73a454f](https://github.com/onegov/onegov-cloud/commit/d4a73a454f7fb7fad231cb13f9fad5919fd42bed)

##### Fix opening times, use fresh session, explicitely commit transactions.

In some cases, websocket-server was not able to find the Chats table
because the schema was not present in this session. This seemed to be
the case only for cached sessions (using SESSIONS). Using a fresh
session obtained from session_manager works, because session_manager
explicitely configures schema for each session.

Outside of a morepath environment, transactions are not automatically
committed (e.g., after a request). Hence, chat has had some open
transactions in idle state. Explicitely commit()ing closes the
transaction and avoids eventual problems with postgres closing the
connections.

`Bugfix` | [8c67b2ec59](https://github.com/onegov/onegov-cloud/commit/8c67b2ec594123fe0968e986a3b99fe8a1800b37)

## 2023.60

`2023-11-17` | [971ba389e7...c6deafa7a4](https://github.com/OneGov/onegov-cloud/compare/971ba389e7^...c6deafa7a4)

### Search

##### Search results for events now also show the event start time

`Bugfix` | [OGC-1331](https://linear.app/onegovcloud/issue/OGC-1331) | [fa0d2b9393](https://github.com/onegov/onegov-cloud/commit/fa0d2b9393a4ee822b0faac11fe8c0087e407485)

### Tickets

##### Condense ticket status message when closed

`Feature` | [OGC-1330](https://linear.app/onegovcloud/issue/OGC-1330) | [971ba389e7](https://github.com/onegov/onegov-cloud/commit/971ba389e7fc561db09c07ff4591e3c6541ef0ff)

### Town6

##### Add Test Version of Chat-Function

Town6: Add Test Version of Chat-Function

`Feature` | [16c237773f](https://github.com/onegov/onegov-cloud/commit/16c237773f211243a82f6382ffdb17b8a71a962f)

## 2023.59

`2023-11-13` | [3f2cc6c3b1...90927b7ecb](https://github.com/OneGov/onegov-cloud/compare/3f2cc6c3b1^...90927b7ecb)

### Test

##### Mark occasionally failing web test as 'flaky' and fix splinter api change

`Bugfix` | [NONE](#NONE) | [3f2cc6c3b1](https://github.com/onegov/onegov-cloud/commit/3f2cc6c3b142264de1ec60e9d695f95a0bed9fce)

## 2023.58

`2023-11-10` | [e42602c1ec...cedb02aae2](https://github.com/OneGov/onegov-cloud/compare/e42602c1ec^...cedb02aae2)

## 2023.57

`2023-11-10` | [7602e5eefc...97404f538b](https://github.com/OneGov/onegov-cloud/compare/7602e5eefc^...97404f538b)

**Upgrade hints**
- Change map settings of all instances from Zug
### Events

##### Anthrazit xml export: Fix missing event if series started in the past

`Bugfix` | [OGC-1320](https://linear.app/onegovcloud/issue/OGC-1320) | [6cb0177c17](https://github.com/onegov/onegov-cloud/commit/6cb0177c177eb2b4936ed5ab6800a8bffe39aeb0)

##### Anthrazit xml export: Replace CR, LF with html br tag

`Bugfix` | [OGC-1320](https://linear.app/onegovcloud/issue/OGC-1320) | [30992412df](https://github.com/onegov/onegov-cloud/commit/30992412df8e955a2556535eb748de9091fbde71)

### Feriennet

##### Replace old logo, remove rega from sponsors

`Bugfix` | [PRO-1217](https://linear.app/projuventute/issue/PRO-1217) | [5fd81a7a02](https://github.com/onegov/onegov-cloud/commit/5fd81a7a02c8db8d35d2ae81b3acf56f965c104f)

### Landsgemeinde

##### Add Dropdown for filling out people from person directory

`Feature` | [OGC-1287](https://linear.app/onegovcloud/issue/OGC-1287) | [7602e5eefc](https://github.com/onegov/onegov-cloud/commit/7602e5eefc9cddcd5cb16b9a9ab810e72acd534c)

### Org

##### Add Zugmap

`Feature` | [OGC-631](https://linear.app/onegovcloud/issue/OGC-631) | [ae9e129f87](https://github.com/onegov/onegov-cloud/commit/ae9e129f87839387016ff6079f611e876988cabe)

##### Adds a secret variant of mTAN access (i.e. not listed)

`Feature` | [OGC-1327](https://linear.app/onegovcloud/issue/OGC-1327) | [4bf3ac918e](https://github.com/onegov/onegov-cloud/commit/4bf3ac918ea63db5c093b3481b0ab4a5c8018e0b)

## 2023.56

`2023-11-07` | [f5311dbb5a...5bb23c1473](https://github.com/OneGov/onegov-cloud/compare/f5311dbb5a^...5bb23c1473)

### Events

##### Winterthur: Extend xml interface Anthrazit format and rework

`Feature` | [OGC-1320](https://linear.app/onegovcloud/issue/OGC-1320) | [30efa28176](https://github.com/onegov/onegov-cloud/commit/30efa28176945afa6400c490c4005c775ba38ba6)

##### Add assets for event form independent of tag usage

`Bugfix` | [OGC-1318](https://linear.app/onegovcloud/issue/OGC-1318) | [edc89417b7](https://github.com/onegov/onegov-cloud/commit/edc89417b74d1490c03164f98cb09fcb9086b949)

### Fsi

##### Adds missing file extension for vCalendar.

`Bugfix` | [OGC-1319](https://linear.app/onegovcloud/issue/OGC-1319) | [07d52355b4](https://github.com/onegov/onegov-cloud/commit/07d52355b4a4d4cf8d18b9f199434236e4c626e3)

### Org

##### Fixes view title

`Bugfix` | [e08fdc98db](https://github.com/onegov/onegov-cloud/commit/e08fdc98dbcdd277fb07c3fd374a2d979d6f6f0d)

### Winterthur

##### Filter items accordeon

`Feature` | [OGC-1221](https://linear.app/onegovcloud/issue/OGC-1221) | [da4c4ed5cd](https://github.com/onegov/onegov-cloud/commit/da4c4ed5cdee635a332bc3e64257f1dc853a6097)

##### Fix back button visibility

`Bugfix` | [OGC-1047](https://linear.app/onegovcloud/issue/OGC-1047) | [0a4ad00dcc](https://github.com/onegov/onegov-cloud/commit/0a4ad00dcc79227af85658ce71b252f490ef38f2)

