# Changes

## 2025.17

`2025-04-04` | [1615b9b227...3a749ca7b9](https://github.com/OneGov/onegov-cloud/compare/1615b9b227^...3a749ca7b9)

### Core

##### Make AdjacencyList use midpoint for insertion of new items.

It's essentially implementing a sparse ordering system where new
items can be inserted between existing ones. This means we can
now insert news items without having to reorder everything.

`Performance` | [OGC-2134](https://linear.app/onegovcloud/issue/OGC-2134) | [40fd71992d](https://github.com/onegov/onegov-cloud/commit/40fd71992d385daddcac12c513239c66f39cf9e3)

### Feriennet

##### Replace banners

Replace banners, create banner macro, add position classes

`Feature` | [PRO-1379](https://linear.app/projuventute/issue/PRO-1379) | [8c0c594b47](https://github.com/onegov/onegov-cloud/commit/8c0c594b470539f5d4f45e530168f2edf25d52d7)

### Org

##### Option to hide personal mail in tickets

Option to display a defined general mail instead of the personal admin/editor-mails for external users.

`Feature` | [OGC-2050](https://linear.app/onegovcloud/issue/OGC-2050) | [faa3540d13](https://github.com/onegov/onegov-cloud/commit/faa3540d138e6de4f3d024cf7615ac5d0598ca06)

##### Add organization hierarchy and option to assign multiple organizations

-    The organization hierarchy can be created in the people-settings
-    People can be assigned to multiple organizations and sub-organizations
-    The sub-organizations in the filter drop-down on the people view get reduced to possible choices according to the chosen organization

`Feature` | [OGC-2096](https://linear.app/onegovcloud/issue/OGC-2096) | [7082f4d0e4](https://github.com/onegov/onegov-cloud/commit/7082f4d0e4211fe7229346e7bae16e357178b0cc)

##### Adds a date picker to the reservation calendar

`Feature` | [OGC-2149](https://linear.app/onegovcloud/issue/OGC-2149) | [e3fb87113b](https://github.com/onegov/onegov-cloud/commit/e3fb87113b923c08f33f7c84ca0d5bfd9f3208ac)

##### Show newest PushNotifications first.

`Feature` | [OGC-2134](https://linear.app/onegovcloud/issue/OGC-2134) | [3a749ca7b9](https://github.com/onegov/onegov-cloud/commit/3a749ca7b92e2705546bb4c3c242b5bda9051c69)

### Pay

##### Avoids crash when generating payment button fails

Decreases the log level for failed payment provider connections.

`Bugfix` | [883bd2bf77](https://github.com/onegov/onegov-cloud/commit/883bd2bf778e7a1faaa7c5ff43a4052c6ad5813e)

### User

##### Fixes crash in `User.get_initials`

`Bugfix` | [5360b64cc6](https://github.com/onegov/onegov-cloud/commit/5360b64cc6461aea4298df64e76b8a1ebf9801ab)

## 2025.16

`2025-03-28` | [fb3aa7cd1f...1b2949f6c2](https://github.com/OneGov/onegov-cloud/compare/fb3aa7cd1f^...1b2949f6c2)

### Form

##### Switches from native URL field to a text field with URL validation

`Feature` | [OGC-2055](https://linear.app/onegovcloud/issue/OGC-2055) | [de7e75b638](https://github.com/onegov/onegov-cloud/commit/de7e75b6389e11650f7a44f29668cfbc264529f5)

### Fsi

##### Ignore 6 year limits for admins

Admins can now register attendees without the 6 year limit.
CSRF messages now contain instruction.

`Feature` | [OGC-2102](https://linear.app/onegovcloud/issue/OGC-2102) | [a8c52f80c1](https://github.com/onegov/onegov-cloud/commit/a8c52f80c1a6cc09b50e971af78e51874dbd9e73)

### Org

##### Additional Field in Newsletter

Add Field "closing remark" to newsletter

`Feature` | [OGC-2006](https://linear.app/onegovcloud/issue/OGC-2006) | [fa483b81e4](https://github.com/onegov/onegov-cloud/commit/fa483b81e418de0af0098426220c42f6bc1218aa)

##### Integrate email bounce statistics in directory entry subscriptions

`Feature` | [OGC-2070](https://linear.app/onegovcloud/issue/OGC-2070) | [992f131ce6](https://github.com/onegov/onegov-cloud/commit/992f131ce6c26565776e304d09462067a35fa7bd)

##### Add extensions to document form

`Feature` | [OGC-2142](https://linear.app/onegovcloud/issue/OGC-2142) | [f45acf604f](https://github.com/onegov/onegov-cloud/commit/f45acf604f30cf667f49fdaa3e61c4a81b9fb9ac)

##### Fixes rendering of newsletter categories

`Bugfix` | [OGC-2118](https://linear.app/onegovcloud/issue/OGC-2118) | [02d2615681](https://github.com/onegov/onegov-cloud/commit/02d2615681b1f4b6caf581cd1acf9797b17a82b1)

##### Fix reoccurring dates bug

Fix bug where editing an event with reoccurring dates lost the dates.

`Bugfix` | [OGC-2133](https://linear.app/onegovcloud/issue/OGC-2133) | [737819e1f3](https://github.com/onegov/onegov-cloud/commit/737819e1f350097ba9323ed0ded577ec2e4ad04c)

##### Adds pagination for News and refactors logic into `NewsCollection`

`Performance` | [OGC-2146](https://linear.app/onegovcloud/issue/OGC-2146) | [fe76277190](https://github.com/onegov/onegov-cloud/commit/fe762771908fcad427f2f6ce838206e755b1507c)

### User

##### Extend cli list command to run over all instances

`Feature` | [NONE](#NONE) | [f770378d11](https://github.com/onegov/onegov-cloud/commit/f770378d1191fa3a7ac7cada483f24ccf763da02)

## 2025.15

`2025-03-21` | [3b0cdefbe6...97478cf310](https://github.com/OneGov/onegov-cloud/compare/3b0cdefbe6^...97478cf310)

### Agency

##### Fixes N+1 query in the people endpoint for the API

`Performance` | [9b1a46148f](https://github.com/onegov/onegov-cloud/commit/9b1a46148fe881bed0ac73a1f12ea8b871ad0f09)

##### Fixes N+1 queries in the agency/membership endpoints for the API

`Performance` | [affcdc40a7](https://github.com/onegov/onegov-cloud/commit/affcdc40a797c5e456564488cb6f78eb3a051dfc)

##### Fixes N+1 query in the agency view

`Performance` | [8aa5b95507](https://github.com/onegov/onegov-cloud/commit/8aa5b95507fc3a0dd59613d0036fecf075d97336)

### Api

##### Avoids logging `None` when no exception is set

`Bugfix` | [5ac460a417](https://github.com/onegov/onegov-cloud/commit/5ac460a41733624f6b7879d0029da11d90c3f22f)

### Auth

##### Extends test coverage for LDAPProvider

`Feature` | [OGC-2137](https://linear.app/onegovcloud/issue/OGC-2137) | [b279e33037](https://github.com/onegov/onegov-cloud/commit/b279e330376bbd4be35b654ef5eaab348d81a3b9)

### Newsletter

##### Remove org_name from Newsletter Category Definition

`Feature` | [OGC-2128](https://linear.app/onegovcloud/issue/OGC-2128) | [604e3c2ea3](https://github.com/onegov/onegov-cloud/commit/604e3c2ea36625bca09a970310f6a02daea88852)

### Org

##### Renders a custom error page for exceeding the mTAN access limit

`Feature` | [OGC-2139](https://linear.app/onegovcloud/issue/OGC-2139) | [4a3cc04258](https://github.com/onegov/onegov-cloud/commit/4a3cc0425888951b41b4c5d116fa62f887c8ee21)

##### Removes unnecessary `print()` statements.

Prevent spamming `/var/log/syslog`. No credentials configured
is the default and can safely be ignored.

`Bugfix` | [NONE](#NONE) | [750dfecc8f](https://github.com/onegov/onegov-cloud/commit/750dfecc8f10dcaf18bdb18f4c5b72b179adbb9f)

##### Fixes regression in `RolesMapping.match`

`Bugfix` | [OGC-2137](https://linear.app/onegovcloud/issue/OGC-2137) | [007b2c904e](https://github.com/onegov/onegov-cloud/commit/007b2c904e937949cf5edd69f9af33e629e3d865)

### Search

##### Reduce log level for ObjectDeletedError

`Feature` | [OGC-1999](https://linear.app/onegovcloud/issue/OGC-1999) | [92d5f89676](https://github.com/onegov/onegov-cloud/commit/92d5f89676efcb0ff1863fb25ea57cbab17fa036)

### Swissvotes

##### Avoids N+1 query for page slides

`Performance` | [c88b3b5493](https://github.com/onegov/onegov-cloud/commit/c88b3b5493bf2fee8e0d73d2c9df8734f6ee7e23)

## 2025.14

`2025-03-14` | [d54f9470e7...d92404c116](https://github.com/OneGov/onegov-cloud/compare/d54f9470e7^...d92404c116)

### Org

##### Display phone numbers in international format

The international format prefixes the country code e.g. +41 for Switzerland

`Feature` | [OGC-2113](https://linear.app/onegovcloud/issue/OGC-2113) | [d54f9470e7](https://github.com/onegov/onegov-cloud/commit/d54f9470e7636d9140199e75a3ab827322115856)

## test

`2025-03-12` | [9c3aee5da3...db0da8dbdf](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...db0da8dbdf)

### Core

##### Switches Redis cache serialization over to MessagePack

`Feature` | [OGC-1893](https://linear.app/onegovcloud/issue/OGC-1893) | [b33e6c99a9](https://github.com/onegov/onegov-cloud/commit/b33e6c99a98040b05efc03099532f483a519a8b3)

### Org

##### Adds a button to show a modal with file links in the file details

`Feature` | [OGC-2077](https://linear.app/onegovcloud/issue/OGC-2077) | [65267dc3b5](https://github.com/onegov/onegov-cloud/commit/65267dc3b5c03a5ee84e79e25e8e8eed68496ca5)

## 2025.13

`2025-03-11` | [2f9d78d9fb...e6692a77d8](https://github.com/OneGov/onegov-cloud/compare/2f9d78d9fb^...e6692a77d8)

### Form

##### Add new format to formcode

New possible format for animal identification number (15 digits)

`Feature` | [OGC-2052](https://linear.app/onegovcloud/issue/OGC-2052) | [809bbfd4cf](https://github.com/onegov/onegov-cloud/commit/809bbfd4cfe0b8ba3e434490d53512e42f15ac60)

### Org

##### Rearrange fields in upload-div

`Feature` | [OGC-2078](https://linear.app/onegovcloud/issue/OGC-2078) | [f8e1511849](https://github.com/onegov/onegov-cloud/commit/f8e151184979f312786e7196661e82beeec938da)

##### Don't allow to paste topic into news and vice versa

`Feature` | [OGC-2105](https://linear.app/onegovcloud/issue/OGC-2105) | [08eb4146de](https://github.com/onegov/onegov-cloud/commit/08eb4146de81cf86a91745f326526db280bb71ef)

##### Small adjustment in body of push notification message.

`Feature` | [OGC-2123](https://linear.app/onegovcloud/issue/OGC-2123) | [90b33b586d](https://github.com/onegov/onegov-cloud/commit/90b33b586da9f8952ebf3e71f27e19c4591d8ca7)

##### Checkbox for automatic newsletter subscription

Add a checkbox for confirming the recipient subscribed by the admin agreed to this.

`Feature` | [OGC-2065](https://linear.app/onegovcloud/issue/OGC-2065) | [6f23ad1242](https://github.com/onegov/onegov-cloud/commit/6f23ad124205991fa509bda2711dfcbee37a9ea5)

##### Adds a supporter role which can only receive and process tickets

Additionally this makes sure that actions on the ticket go through the
ticket or a different proxy model which supporters have private access
to, so supporters can apply changes relevant to the ticket.

`Feature` | [OGC-1865](https://linear.app/onegovcloud/issue/OGC-1865) | [7a52db6883](https://github.com/onegov/onegov-cloud/commit/7a52db6883dc7ea8ad444dc1c546d633da9ee506)

##### Show only topics in 'Edited Topics` boardlet on dashboard

`Bugfix` | [OGC-2121](https://linear.app/onegovcloud/issue/OGC-2121) | [cd84b19459](https://github.com/onegov/onegov-cloud/commit/cd84b194596e57b0d6cd7f68caf3afa5437fc97e)

##### Fix dashboard translations get lost

Executing `do/translate onegov.town6` made dashboard translations disappear

`Bugfix` | [NONE](#NONE) | [7febe10d80](https://github.com/onegov/onegov-cloud/commit/7febe10d80fa9e60e8475fc1bf419793630c11df)

##### Fixes tests afer new message format.

`Bugfix` | [6c99360456](https://github.com/onegov/onegov-cloud/commit/6c99360456640d1a1c8976571c62f619376a55b1)

### Town6

##### Sidebar name

Create title of sidebar from h3 elements

`Feature` | [OGC-2043](https://linear.app/onegovcloud/issue/OGC-2043) | [6d862946df](https://github.com/onegov/onegov-cloud/commit/6d862946dfa2ccd4b621dafff166c5873a688ce5)

##### Display sidebar contact links like sidebar links

`Feature` | [OGC-2112](https://linear.app/onegovcloud/issue/OGC-2112) | [8fe36d71b2](https://github.com/onegov/onegov-cloud/commit/8fe36d71b2cf5ffd51f206d4afc4d5e5b0e3ff31)

##### Directory preview

Fix display of preview text

`Bugfix` | [OGC-2114](https://linear.app/onegovcloud/issue/OGC-2114) | [e35b22bb72](https://github.com/onegov/onegov-cloud/commit/e35b22bb72f8da252115bfb7708eb0fa5a309f61)

##### Fix margin for plus and minus button

`Bugfix` | [NONE](#NONE) | [5ad5e4e0b6](https://github.com/onegov/onegov-cloud/commit/5ad5e4e0b6581525998801bc3c39893f7074a2e7)

##### Firebase bugfixes.

Fixes a number of issues OGC-2122, OGC-2120, OGC-2119, OGC-2109

- Fix an issue where news published only 1 min in the future was not sent
- Link to the `/push-notifications`
- Show hint in UI if message already sent and it won't send again
- Make deleting News with push notifications possible

`Bugfix` | [771272f75e](https://github.com/onegov/onegov-cloud/commit/771272f75e100045de2b07cae6ff55a2615e8c6d)

### User

##### Allows users to be part of more than one group

`Feature` | [OGC-2079](https://linear.app/onegovcloud/issue/OGC-2079) | [676ffb72a0](https://github.com/onegov/onegov-cloud/commit/676ffb72a0531b5010f071641037e7e0e40d9722)

## 2025.12

`2025-03-04` | [aeeac42f56...1ad5188fed](https://github.com/OneGov/onegov-cloud/compare/aeeac42f56^...1ad5188fed)

### Ticket

##### Make db upgrade for ticket closed_on column more performant

`Feature` | [NONE](#NONE) | [f59d7a9b0f](https://github.com/onegov/onegov-cloud/commit/f59d7a9b0fe658317e5dec8ba1381684d6364b09)

## 2025.11

`2025-03-03` | [0c2dd4a07e...c321b6c196](https://github.com/OneGov/onegov-cloud/compare/0c2dd4a07e^...c321b6c196)

## 2025.10

`2025-03-03` | [753d4737ed...a33c968d71](https://github.com/OneGov/onegov-cloud/compare/753d4737ed^...a33c968d71)

### Agency

##### Staka LU: Handle Sekretariat in column lastname as agency

`Feature` | [OGC-2106](https://linear.app/onegovcloud/issue/OGC-2106) | [8ad24bda89](https://github.com/onegov/onegov-cloud/commit/8ad24bda897a91dadd9891857afdaf83a75fb2ea)

##### Staka LU: Use membership title as export field (instead of person function)

`Feature` | [OGC-2107](https://linear.app/onegovcloud/issue/OGC-2107) | [4c6118e20a](https://github.com/onegov/onegov-cloud/commit/4c6118e20a2856746669c5386f23bb851ec63cb2)

### Org

##### Prevent duplicates in push notifications and other improvements.

- Auto-select default topic when only one exists and checkbox is ticked
- Preventing duplicates in push notifications
- Fix default choices not being in nested list
- Prevent user from being able to submit an empty list if checkbox ticked
- Fix inconsistent UI labels (Themen-ID ...) 

The implementation now uses database constraints to ensure notification
 uniqueness even during simultaneous processing.

`Feature` | [OGC-1951](https://linear.app/onegovcloud/issue/OGC-1951) | [5eac37b6e2](https://github.com/onegov/onegov-cloud/commit/5eac37b6e23c15470dc88e407c5332b0ba77fd19)

### Swissvotes

##### Allow English documents in vote search results

`Bugfix` | [SWI-60](https://linear.app/swissvotes/issue/SWI-60) | [023147a26e](https://github.com/onegov/onegov-cloud/commit/023147a26ef0f1281909ce3638349a8e0ecb693b)

##### Allow English documents in vote search results

`Bugfix` | [SWI-60](https://linear.app/swissvotes/issue/SWI-60) | [cfa9246bb4](https://github.com/onegov/onegov-cloud/commit/cfa9246bb4ec9698d3d009b78b2fb713bf089fba)

### Town6

##### Add push notifications overview.

`Feature` | [OGC-1951](https://linear.app/onegovcloud/issue/OGC-1951) | [23dbcc0a85](https://github.com/onegov/onegov-cloud/commit/23dbcc0a8583baf530842e4c6d3d80f8e5376c59)

## 2025.9

`2025-02-27` | [199f1a8282...46d6aba65d](https://github.com/OneGov/onegov-cloud/compare/199f1a8282^...46d6aba65d)

### Core

##### Switches Redis cache serialization over to MessagePack

`Feature` | [OGC-1893](https://linear.app/onegovcloud/issue/OGC-1893) | [101a9ae5dc](https://github.com/onegov/onegov-cloud/commit/101a9ae5dcf6e91047790aa5000cf9409dff6deb)

##### Use orjson for JSON serialization/deserialization

`Performance` | [2954d7ead4](https://github.com/onegov/onegov-cloud/commit/2954d7ead433c92adab96d424a1c2ff77d347b9d)

### Org

##### Show total price in ticket and confirmation email

`Feature` | [OGC-2053](https://linear.app/onegovcloud/issue/OGC-2053) | [b1a7c0afb6](https://github.com/onegov/onegov-cloud/commit/b1a7c0afb6eb906bc74273e561891e5b647b917a)

### Pas

##### Fix parliamentary settlement calculations and export functionality.

- Only show exports that have at least one entry in table
- Fix expense calculation to prevent double-counting of base totals
- Implement missing cost-of-living adjustment in parliamentarian export
- Perform the calculation for getting the Quartal with no assumptions
- Make sure parliamentarians are correctly linked to their parties during
 the times they attended, not just when they first joined. Indeed, party 
changes should be expected and accounted for
- Ensure role activity is verified at specific attendance times.
- Replace manual HTML string formatting

`Bugfix` | [OGC-1503](https://linear.app/onegovcloud/issue/OGC-1503) | [199f1a8282](https://github.com/onegov/onegov-cloud/commit/199f1a828264e7a089a9383771ce55b905307cfb)

### Town6

##### Adds a dashboard with basic figures

`Feature` | [OGC-1528](https://linear.app/onegovcloud/issue/OGC-1528) | [48df75dc30](https://github.com/onegov/onegov-cloud/commit/48df75dc3055387bddd9f76677590ab01b040d58)

##### Adding firebase push notifications.

Town6: Adds firebase push notifications.

`Feature` | [OGC-1951](https://linear.app/onegovcloud/issue/OGC-1951) | [b137397a09](https://github.com/onegov/onegov-cloud/commit/b137397a095f27d1854494a238a2cdb9e8f8724c)

### Websockets

##### Switches away from the deprecated legacy websockets

`Feature` | [OGC-1735](https://linear.app/onegovcloud/issue/OGC-1735) | [61931a3714](https://github.com/onegov/onegov-cloud/commit/61931a3714f26baa84312a2a69f87250b52f4686)

## test

No changes since last release

## test

`2025-02-24` | [9c3aee5da3...0b99952075](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...0b99952075)

### Org

##### Remove unconfirmed subscribers

Remove unconfirmed subscribers after 7 days of initial subscription. Also display date of subscription on recipients-view and export.

`Feature` | [OGC-2017](https://linear.app/onegovcloud/issue/OGC-2017) | [b76a07b02c](https://github.com/onegov/onegov-cloud/commit/b76a07b02c2e6d8385b97694edd24c6f6955df71)

## 2025.8

`2025-02-20` | [7b612693f4...d2765ca4af](https://github.com/OneGov/onegov-cloud/compare/7b612693f4^...d2765ca4af)

### Agency

##### Make the `--clean` option significantly faster.

`Feature` | [OGC-2081](https://linear.app/onegovcloud/issue/OGC-2081) | [7a0f68d105](https://github.com/onegov/onegov-cloud/commit/7a0f68d10518736048552d8668b34aef5be13226)

##### Staka LU PDF with proper spacer

`Bugfix` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [7b612693f4](https://github.com/onegov/onegov-cloud/commit/7b612693f48a8a9484e65558d948e9eb39cfdbe7)

##### Be slighly more robust with added None check.

`Bugfix` | [OGC-2083](https://linear.app/onegovcloud/issue/OGC-2083) | [e74895ad7a](https://github.com/onegov/onegov-cloud/commit/e74895ad7aebdedb89013f8029aa0dd14de56c25)

### Feriennet

##### New weights for admin and organizer children and groups in matching

`Feature` | [PRO-1360](https://linear.app/projuventute/issue/PRO-1360) | [3a359413f1](https://github.com/onegov/onegov-cloud/commit/3a359413f1b649c8b4283a387c70f41a648d86b3)

### Org

##### Improves the ergonomics of find my spot reservations

`Feature` | [OGC-2023](https://linear.app/onegovcloud/issue/OGC-2023) | [e873821c01](https://github.com/onegov/onegov-cloud/commit/e873821c01cd2bd68572bbfaad7cb65e88f22888)

### Town6

##### Slider

Fix bug where sizing of slider only worked after resizing the header.

`Bugfix` | [OGC-2056](https://linear.app/onegovcloud/issue/OGC-2056) | [d1c071cdd2](https://github.com/onegov/onegov-cloud/commit/d1c071cdd2f13de7f629bdd069c6d2253b83da3f)

##### Add missing translation

`Bugfix` | [OGC-2064](https://linear.app/onegovcloud/issue/OGC-2064) | [ebdff10ca3](https://github.com/onegov/onegov-cloud/commit/ebdff10ca304caf485c4b81ae7a219c9118828f0)

##### Fixes sidebar contact.

Go this error:
JSONDecodeError: Expecting value: line 1 column 1 (char 0)

`Bugfix` | [OGC-2089](https://linear.app/onegovcloud/issue/OGC-2089) | [cc8c03ba1a](https://github.com/onegov/onegov-cloud/commit/cc8c03ba1aea0a05b4cfec1fc13658104426f787)

### User

##### Fixes isolation bug between multiple SAML2 providers

`Bugfix` | [e11229b408](https://github.com/onegov/onegov-cloud/commit/e11229b408fe31ab2672f12027f0a9080d698ebf)

## 2025.7

`2025-02-17` | [4297221960...2458cd0a05](https://github.com/OneGov/onegov-cloud/compare/4297221960^...2458cd0a05)

### Agency

##### Staka LU No hierarchical numbering in pdf

`Feature` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [4297221960](https://github.com/onegov/onegov-cloud/commit/4297221960bd639331463f584ea63829e4dd9aa0)

##### Staka LU Add logo to pdf

`Feature` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [f60df0f84e](https://github.com/onegov/onegov-cloud/commit/f60df0f84e4ddf5eb2674398d3d6279b5f603be9)

##### Staka LU Support alliance names in import

`Feature` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [4c79c0cf51](https://github.com/onegov/onegov-cloud/commit/4c79c0cf516473c7b00db7e264eaa2bde7485fcf)

##### Staka LU Use alternative dienststelle name over dienstelle

`Feature` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [37d46a2e26](https://github.com/onegov/onegov-cloud/commit/37d46a2e26d743e4002c9d067dcb1ca5662dabdf)

##### Staka LU pdf shows now organisation information

`Feature` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [e0ee4b0c7f](https://github.com/onegov/onegov-cloud/commit/e0ee4b0c7f39105e5aa30f4a640bb0ea91d70fbe)

### Pas

##### Adds provisional import script.

`Feature` | [OGC-1878](https://linear.app/onegovcloud/issue/OGC-1878) | [9bafe68736](https://github.com/onegov/onegov-cloud/commit/9bafe687361c7160c869fd0269b656b9d82d2e16)

## 2025.6

`2025-02-13` | [4a8ed94cb1...952fb7d12f](https://github.com/OneGov/onegov-cloud/compare/4a8ed94cb1^...952fb7d12f)

### Agency

##### Clean up previous implementation.

Uses a meta field for the external_user_id (So we don't have a specific column
    in org for a specific feature of agency)
    Make sure the api uses it's own mutation form such that it's seperated form
    public facing mutations.
    Make sure hidden_people_fields is honoured everywhere

`Bugfix` | [OGC-2061](https://linear.app/onegovcloud/issue/OGC-2061) | [4a8ed94cb1](https://github.com/onegov/onegov-cloud/commit/4a8ed94cb12db893dc3de0fb73fb4b3c7d1db309)

## 2025.5

`2025-02-13` | [e8c813d38e...2046905863](https://github.com/OneGov/onegov-cloud/compare/e8c813d38e^...2046905863)

### Agency

##### Staka LU Skip personal email addresses

`Feature` | [OGC-1952](https://linear.app/onegovcloud/issue/OGC-1952) | [59d5e5c77a](https://github.com/onegov/onegov-cloud/commit/59d5e5c77a26313d8d6eb41a830cf99e6b37d3c8)

##### Staka LU Adds function and academic title fields to pdf export

`Feature` | [OGC-2071](https://linear.app/onegovcloud/issue/OGC-2071) | [02332a8ba7](https://github.com/onegov/onegov-cloud/commit/02332a8ba73b8d5de77c5134cebe7917e46f8502)

### Api

##### Add external_id for Person. Used in agency.

Also had to refactor the Api such that request is in scope.

`Feature` | [OGC-2061](https://linear.app/onegovcloud/issue/OGC-2061) | [73d7b015ae](https://github.com/onegov/onegov-cloud/commit/73d7b015aecbf8e89702d0ac6a95bbf04fe18784)

### Directory

##### Ensure all Directory Entry Subscribers are listed

`Bugfix` | [OGC-2063](https://linear.app/onegovcloud/issue/OGC-2063) | [956bda24aa](https://github.com/onegov/onegov-cloud/commit/956bda24aab6f9d8d3f57da20aab1e5a968d278e)

### Org

##### Moves contact inherit functionality to base `ContactExtension`

This means resources, forms and directories can now inherit their
contact information from a topic as well.

`Feature` | [OGC-2049](https://linear.app/onegovcloud/issue/OGC-2049) | [7e9659342c](https://github.com/onegov/onegov-cloud/commit/7e9659342ce8243668811990f88dcbd8fccf4855)

##### Api Access

`Bugfix` | [OGC-2075](https://linear.app/onegovcloud/issue/OGC-2075) | [21bff15e86](https://github.com/onegov/onegov-cloud/commit/21bff15e86b2151544c89ad4783e1da76f12d6fb)

### Pay

##### Adds Worldline Saferpay payment provider

`Feature` | [OGC-2068](https://linear.app/onegovcloud/issue/OGC-2068) | [f841f76e6c](https://github.com/onegov/onegov-cloud/commit/f841f76e6c11155c6e62699387a2d1c910705f38)

### Town6

##### Adds a topics API endpoint

Also includes a small extension to the existing news/events endpoint

`Feature` | [OGC-2058](https://linear.app/onegovcloud/issue/OGC-2058) | [6f5f3b9b64](https://github.com/onegov/onegov-cloud/commit/6f5f3b9b6400ff7b3cde9b3f8ac9cbd2eedd4088)

##### Adds an additional contact link.

`Feature` | [OGC-1940](https://linear.app/onegovcloud/issue/OGC-1940) | [8b138e5965](https://github.com/onegov/onegov-cloud/commit/8b138e596506df91d8bd15fb2539b6e73848b46d)

### User

##### Makes `at_hash` optional in OpenID Connect provider

`Bugfix` | [OGC-1767](https://linear.app/onegovcloud/issue/OGC-1767) | [5189b63bf7](https://github.com/onegov/onegov-cloud/commit/5189b63bf79c2d8569ae91aade8070f709f8911e)

## 2025.4

`2025-01-31` | [c0942af43d...0c5beb8230](https://github.com/OneGov/onegov-cloud/compare/c0942af43d^...0c5beb8230)

### Api

##### Add documentation

`Feature` | [OGC-2036](https://linear.app/onegovcloud/issue/OGC-2036) | [42524e6d9a](https://github.com/onegov/onegov-cloud/commit/42524e6d9a5f091e0c0bdeb0b8ccf5e55a36916f)

### Directories

##### Only send delayed email notifications for 'public' and 'mtan' access levels.

`Bugfix` | [OGC-2044](https://linear.app/onegovcloud/issue/OGC-2044) | [41b2f79431](https://github.com/onegov/onegov-cloud/commit/41b2f79431f89896b6c3d3baea0b34a0cc1a04ca)

### Feriennet

##### Google Tag Manager

Replace script

`Feature` | [OGC-1353](https://linear.app/onegovcloud/issue/OGC-1353) | [40481da20c](https://github.com/onegov/onegov-cloud/commit/40481da20ca8e140655dbc7cb694ad5562089080)

### Form

##### Add formcode definitions

Add more possible definitions in the form editor to choose from.

`Feature` | [OGC-1942](https://linear.app/onegovcloud/issue/OGC-1942) | [382bcc60b5](https://github.com/onegov/onegov-cloud/commit/382bcc60b5f945b067a2920bb8eacd9b71f0cf87)

### Gis

##### Prevents accidentally changing the zoom on the map.

`Feature` | [OGC-1944](https://linear.app/onegovcloud/issue/OGC-1944) | [a91c91e17b](https://github.com/onegov/onegov-cloud/commit/a91c91e17b51db7b96bd6f959c4db653bfb6b0d4)

### Newsletter

##### Adds option to notify admins if a user unsubscribes from the newsletter subscription list

`Feature` | [OGC-2037](https://linear.app/onegovcloud/issue/OGC-2037) | [08e795f772](https://github.com/onegov/onegov-cloud/commit/08e795f772d3bb0c322fb7e1693bb412c0fcbe88)

### Org

##### Collect inactive email addresses daily and indicate delivery failures for newsletter recipients

`Feature` | [OGC-1896](https://linear.app/onegovcloud/issue/OGC-1896) | [821ff43296](https://github.com/onegov/onegov-cloud/commit/821ff43296c1ab9ce88297a1e17cac3b647252e9)

### Pay

##### Adds Datatrans payment provider

`Feature` | [OGC-2007](https://linear.app/onegovcloud/issue/OGC-2007) | [cdf4acbdd8](https://github.com/onegov/onegov-cloud/commit/cdf4acbdd8fe3a3b15f10929342189be13a743e7)

### Town6

##### Show creation date in imagesets.

`Feature` | [OGC-1901](https://linear.app/onegovcloud/issue/OGC-1901) | [4507af6c4c](https://github.com/onegov/onegov-cloud/commit/4507af6c4ccf8f32fda65be79792e3f9ed369e30)

##### Add text_link in homepage widget markdown file

`Feature` | [cf0b91c727](https://github.com/onegov/onegov-cloud/commit/cf0b91c727bb962297278d089552ecee796002d0)

##### Add option for label text

`Feature` | [OGC-2040](https://linear.app/onegovcloud/issue/OGC-2040) | [e59d03389d](https://github.com/onegov/onegov-cloud/commit/e59d03389dc422d3d91abed86e9e4ee9dbd540aa)

##### Make deleting a link more accessible.

`Bugfix` | [OGC-739](https://linear.app/onegovcloud/issue/OGC-739) | [4d318fc9bf](https://github.com/onegov/onegov-cloud/commit/4d318fc9bf898c38fa34f747fee7698f2bb14a08)

## 2025.3

`2025-01-23` | [9eabea3e30...f3e1dbff9c](https://github.com/OneGov/onegov-cloud/compare/9eabea3e30^...f3e1dbff9c)

### Electionday

##### Allows defining the publisher URI via `open_data` metadata.

This also ensures that the default URI is a URN, rather than a URL
since we can't compute a URL that will always be valid.

We now also include the publisher's email directly and not only via the
contactPoint.

`Bugfix` | [OGC-2002](https://linear.app/onegovcloud/issue/OGC-2002) | [81edbfa4fa](https://github.com/onegov/onegov-cloud/commit/81edbfa4fa009e6983adfd66b6eaafd97c26a556)

### Form

##### Fixes incorrect field dependencies for labels that use parentheses

`Bugfix` | [OGC-2041](https://linear.app/onegovcloud/issue/OGC-2041) | [2eff06c5f6](https://github.com/onegov/onegov-cloud/commit/2eff06c5f653f2a4b0ed2233f9f8aa14145dccd6)

### Landsgemeinde

##### Adds redirect from /film to /topics/film

`Feature` | [OGC-2039](https://linear.app/onegovcloud/issue/OGC-2039) | [832ada552a](https://github.com/onegov/onegov-cloud/commit/832ada552a6664a5a34c3154a7703f5239363739)

### Org

##### Document forms

Upload a PDF to be displayed in the forms view.

`Feature` | [OGC-2003](https://linear.app/onegovcloud/issue/OGC-2003) | [1a3e11618b](https://github.com/onegov/onegov-cloud/commit/1a3e11618bb305d72e2f52872fe602d38dd05b7d)

##### Avoid emitting an exception for invalid years

`Bugfix` | [SEA-1666](https://linear.app/seantis/issue/SEA-1666) | [79c1ac840c](https://github.com/onegov/onegov-cloud/commit/79c1ac840cd22392f7c69d85bfa5266fd88a2ecc)

### Town 6

##### Homepage video Link

Add option for text-link

`Feature` | [OGC-2040](https://linear.app/onegovcloud/issue/OGC-2040) | [7136ecb857](https://github.com/onegov/onegov-cloud/commit/7136ecb857db1c56dd9ff8539c8e95e78d8ff634)

### Town6

##### Sidebar-toggler bottom

Restyle the sidebar-toggler so it is fixed to the bottom and more visible.

`Feature` | [OGC-1985](https://linear.app/onegovcloud/issue/OGC-1985) | [d2c4c7dedd](https://github.com/onegov/onegov-cloud/commit/d2c4c7deddd82e65881fb003345bc1bcb99fff9c)

## 2025.2

`2025-01-17` | [2e9311bc89...0f10de8479](https://github.com/OneGov/onegov-cloud/compare/2e9311bc89^...0f10de8479)

### Directory

##### Delay sending update notifications to subscribers if publication starts in future

`Feature` | [OGC-1825](https://linear.app/onegovcloud/issue/OGC-1825) | [991f2c5c76](https://github.com/onegov/onegov-cloud/commit/991f2c5c761b72ea158a54180267b276b3049e14)

### Feriennet

##### Fix save button

`Bugfix` | [OGC-1348](https://linear.app/onegovcloud/issue/OGC-1348) | [2e9311bc89](https://github.com/onegov/onegov-cloud/commit/2e9311bc89639ab1d83014430fa5971fa52a4687)

### Org

##### Sort side panel links alphabetically

`Feature` | [OGC-2008](https://linear.app/onegovcloud/issue/OGC-2008) | [10c9a81c86](https://github.com/onegov/onegov-cloud/commit/10c9a81c86187f7aa59ead9aa567481cdfbf8805)

### Town6

##### API For News and Events

`Feature` | [OGC-1950](https://linear.app/onegovcloud/issue/OGC-1950) | [e9e35cb967](https://github.com/onegov/onegov-cloud/commit/e9e35cb967ebcde1369507192ec1d56db9451a6a)

## 2025.1

`2025-01-09` | [4cbd81a1fe...fa75011145](https://github.com/OneGov/onegov-cloud/compare/4cbd81a1fe^...fa75011145)

### Core

##### Update stamp price

`Feature` | [NONE](#NONE) | [e9bcdd74bc](https://github.com/onegov/onegov-cloud/commit/e9bcdd74bc4da984f533bde08d17e607f454d626)

### Election Day

##### Adds missing static entities for unit tests

`Bugfix` | [NONE](#NONE) | [4cbd81a1fe](https://github.com/onegov/onegov-cloud/commit/4cbd81a1fecce0cf72a85082979017256f9fae88)

### Electionday

##### Adds municipality and map data for 2025

`Feature` | [OGC-1953](https://linear.app/onegovcloud/issue/OGC-1953) | [db7d0c9304](https://github.com/onegov/onegov-cloud/commit/db7d0c93044bbc02b257555a1dc8fd044af78e8c)

### Org

##### Adds optional ordering by filename or caption to image sets

`Feature` | [OGC-2000](https://linear.app/onegovcloud/issue/OGC-2000) | [f67e97d4ed](https://github.com/onegov/onegov-cloud/commit/f67e97d4ed357dccaee3008bc58544504b22b02d)

## test

No changes since last release

## test

`2025-01-08` | [9c3aee5da3...bcfbf712a8](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...bcfbf712a8)

### Core

##### Add descriptions in formcode docs

`Feature` | [OGC-1942](https://linear.app/onegovcloud/issue/OGC-1942) | [6908b4cf33](https://github.com/onegov/onegov-cloud/commit/6908b4cf33cdf05552da1056b87d03f645b688b8)

### Landsgemeinde

##### Remove "Auskunft" from Footer

`Feature` | [OGC-1991](https://linear.app/onegovcloud/issue/OGC-1991) | [675267da50](https://github.com/onegov/onegov-cloud/commit/675267da50dc7ee3968a96c8feb7fa76abf519ab)

##### Rename Archive

`Feature` | [OGC-1990](https://linear.app/onegovcloud/issue/OGC-1990) | [ee62c7a0c9](https://github.com/onegov/onegov-cloud/commit/ee62c7a0c915845d604adcc8ab0e539ca26cdd50)

##### Prevent crash on file replacement

`Bugfix` | [OGC-1999](https://linear.app/onegovcloud/issue/OGC-1999) | [eb0b55a269](https://github.com/onegov/onegov-cloud/commit/eb0b55a269f1cd0967615027dfd1a7cbf2f70f36)

##### File Upload View

`Bugfix` | [OGC-1998](https://linear.app/onegovcloud/issue/OGC-1998) | [95e4fb151e](https://github.com/onegov/onegov-cloud/commit/95e4fb151e53671ac667940d31a9dd019d97ef9e)

### Settings

##### Displays the web statistics url

`Feature` | [OGC-1639](https://linear.app/onegovcloud/issue/OGC-1639) | [13baf032fd](https://github.com/onegov/onegov-cloud/commit/13baf032fd10932908cc089f192b2cb12c0c6fe0)

### Town 6

##### Search View

`Feature` | [OGC-1966](https://linear.app/onegovcloud/issue/OGC-1966) | [c080567c8e](https://github.com/onegov/onegov-cloud/commit/c080567c8ed2d2e13e277e2689db56e5fb6ef974)

### User

##### Fixes various issues in OIDC authentication provider

`Bugfix` | [OGC-1767](https://linear.app/onegovcloud/issue/OGC-1767) | [bef47625f0](https://github.com/onegov/onegov-cloud/commit/bef47625f02b602e040449cdd2534619bf595ddb)

## 2024.60

`2024-12-19` | [5925b224b9...7bff3ede2e](https://github.com/OneGov/onegov-cloud/compare/5925b224b9^...7bff3ede2e)

**Upgrade hints**
- On the off-chance that we have some duplicate `Payment` associations this upgrade task will fail, in which case we would need to write another migration to remove duplicates for all links on `Payment`.
### Agency

##### Import Staka LU: Skip label 'Telefon' but keep 'Telefonist'

`Feature` | [OGC-1954](https://linear.app/onegovcloud/issue/OGC-1954) | [5925b224b9](https://github.com/onegov/onegov-cloud/commit/5925b224b9354ea45f2ab9fc7bd384e4bf624449)

##### Allows ticket notifications to target parent organisations

`Feature` | [OGC-1658](https://linear.app/onegovcloud/issue/OGC-1658) | [0250a72e1e](https://github.com/onegov/onegov-cloud/commit/0250a72e1eeedf91ab2fbb1e2a99f558226d776c)

##### Prevent cutting content in person card

`Bugfix` | [OGC-1963](https://linear.app/onegovcloud/issue/OGC-1963) | [d296c64877](https://github.com/onegov/onegov-cloud/commit/d296c64877697d606fa4653e749164e5a5ea4a8f)

### Api

##### Return a 403 for missing authorization when requesting a JWT token

`Bugfix` | [7d33b93711](https://github.com/onegov/onegov-cloud/commit/7d33b93711a3804f9fc9941dd790598dfd7df7bf)

##### Makes sure invisible endpoint items are inaccessible

`Bugfix` | [OGC-1992](https://linear.app/onegovcloud/issue/OGC-1992) | [9e317877f1](https://github.com/onegov/onegov-cloud/commit/9e317877f1d21f11c2658415fde14c4c187fe65d)

### Core

##### Adds unique constraint to association tables

`Bugfix` | [OGC-1969](https://linear.app/onegovcloud/issue/OGC-1969) | [4adcb66f82](https://github.com/onegov/onegov-cloud/commit/4adcb66f825d3be0a67c27ef4cda190d18f9711d)

### Election Day

##### Election results shown as pending as long as election not completed/final

Note: No model or api adaption done

`Feature|` | [OGC-1939](https://linear.app/onegovcloud/issue/OGC-1939) | [7663a133d9](https://github.com/onegov/onegov-cloud/commit/7663a133d90f35221e3b3fce660babdbd64872a8)

### Electionday

##### Adds additional date metadata to subscribers

`Feature` | [OGC-1882](https://linear.app/onegovcloud/issue/OGC-1882) | [1770d45927](https://github.com/onegov/onegov-cloud/commit/1770d45927b012e16ff7e99b6a56a6e869bd2158)

##### Include specific URLs for sub-results in SMS when possible

`Feature` | [OGC-1881](https://linear.app/onegovcloud/issue/OGC-1881) | [01eb7d8b03](https://github.com/onegov/onegov-cloud/commit/01eb7d8b034861d80a24166838f95974db679776)

### Feriennet

##### Make it possible to change attendee info without active period

`Bugfix` | [PRO-1341](https://linear.app/projuventute/issue/PRO-1341) | [8693110cd8](https://github.com/onegov/onegov-cloud/commit/8693110cd8edf4d4d93b58efadf790f82f3e9de5)

### File

##### Apply EXIF orientation to image when stripping EXIF metadata

`Bugfix` | [OGC-1993](https://linear.app/onegovcloud/issue/OGC-1993) | [5859fb2455](https://github.com/onegov/onegov-cloud/commit/5859fb2455bd1c3b6c68c0248b1ee2be526ee945)

### Files

##### Sort sidebar documents alphabetically (org and town6)

`Feature` | [OGC-1797](https://linear.app/onegovcloud/issue/OGC-1797) | [0e99c5e925](https://github.com/onegov/onegov-cloud/commit/0e99c5e92511685250f051c15dcdf952d182c2c9)

### Org

##### Avoid generating redundant file links for linked general files

This also updates WebTest to the newest version, since we need it in
order to test multi-file uploads.

`Bugfix` | [OGC-1967](https://linear.app/onegovcloud/issue/OGC-1967) | [27c3e25ed5](https://github.com/onegov/onegov-cloud/commit/27c3e25ed579219df1454d5fcfa36dd6708b640d)

##### Re-add submit-button for directory entry suggestion button

`Bugfix` | [OGC-1986](https://linear.app/onegovcloud/issue/OGC-1986) | [7e4076face](https://github.com/onegov/onegov-cloud/commit/7e4076face9c972078d73bedd4b2cdef53bd511b)

##### Submits individual uploads in dropzone sequentially

Submitting them in parallel sometimes results in nginx producing 503
errors and there's no significant speed benefit to starting the uploads
in parallel, since we will still be limited by our bandwidth.

`Bugfix` | [OGC-1994](https://linear.app/onegovcloud/issue/OGC-1994) | [e12dd0bb88](https://github.com/onegov/onegov-cloud/commit/e12dd0bb884315e8a299549e219554254ac8f3c2)

### Pas

##### Generating various exports.

`Feature` | [OGC-1878](https://linear.app/onegovcloud/issue/OGC-1878) | [96f09cfc20](https://github.com/onegov/onegov-cloud/commit/96f09cfc200a20d153fa81ab5b4dccbaecba0f9b)

### Town6

##### Sidebar make person function as wide as document names and map

`Feature` | [NONE](#NONE) | [13d6a10ad3](https://github.com/onegov/onegov-cloud/commit/13d6a10ad3fbd27e9e26440acfdb47917ac6b467)

##### Icon Links

Correct margin and padding if there is no text

`Feature` | [OGC-1943](https://linear.app/onegovcloud/issue/OGC-1943) | [471d46565c](https://github.com/onegov/onegov-cloud/commit/471d46565c7158a752b41722125a600bdaffea13)

##### Make the context-specific-function multi line capable.

`Feature` | [OGC-1955](https://linear.app/onegovcloud/issue/OGC-1955) | [597a6cc034](https://github.com/onegov/onegov-cloud/commit/597a6cc034b87d7b3e727c9aa83e3cf38aafd4a4)

##### Lead is no longer a mandatory field in ExternalLinkForm

`Feature` | [OGC-1941](https://linear.app/onegovcloud/issue/OGC-1941) | [5523e08e31](https://github.com/onegov/onegov-cloud/commit/5523e08e31cc2b0e4ee865b3e3126f41aabe1cde)

##### Main image in news

Enable the option to hide main images on news

`Bugfix` | [OGC-1903](https://linear.app/onegovcloud/issue/OGC-1903) | [53135169e2](https://github.com/onegov/onegov-cloud/commit/53135169e2b654ca6782f448e19446ae2c989680)

### User

##### Adds scope setting to OIDC authentication provider

`Feature` | [OGC-1767](https://linear.app/onegovcloud/issue/OGC-1767) | [dc2ebc87dc](https://github.com/onegov/onegov-cloud/commit/dc2ebc87dcc8d8e699c59f2e21eb53492e899d87)

## test

`2024-12-17` | [9c3aee5da3...b6de332b06](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...b6de332b06)

## 2024.59

`2024-12-12` | [0e99c5e925...5ae8a276f3](https://github.com/OneGov/onegov-cloud/compare/0e99c5e925^...5ae8a276f3)

### Files

##### Sort sidebar documents alphabetically (org and town6)

`Feature` | [OGC-1797](https://linear.app/onegovcloud/issue/OGC-1797) | [0e99c5e925](https://github.com/onegov/onegov-cloud/commit/0e99c5e92511685250f051c15dcdf952d182c2c9)

## 2024.58

`2024-12-11` | [5925b224b9...cfd97aa9b7](https://github.com/OneGov/onegov-cloud/compare/5925b224b9^...cfd97aa9b7)

**Upgrade hints**
- On the off-chance that we have some duplicate `Payment` associations this upgrade task will fail, in which case we would need to write another migration to remove duplicates for all links on `Payment`.
### Agency

##### Import Staka LU: Skip label 'Telefon' but keep 'Telefonist'

`Feature` | [OGC-1954](https://linear.app/onegovcloud/issue/OGC-1954) | [5925b224b9](https://github.com/onegov/onegov-cloud/commit/5925b224b9354ea45f2ab9fc7bd384e4bf624449)

##### Allows ticket notifications to target parent organisations

`Feature` | [OGC-1658](https://linear.app/onegovcloud/issue/OGC-1658) | [0250a72e1e](https://github.com/onegov/onegov-cloud/commit/0250a72e1eeedf91ab2fbb1e2a99f558226d776c)

### Api

##### Return a 403 for missing authorization when requesting a JWT token

`Bugfix` | [7d33b93711](https://github.com/onegov/onegov-cloud/commit/7d33b93711a3804f9fc9941dd790598dfd7df7bf)

### Core

##### Adds unique constraint to association tables

`Bugfix` | [OGC-1969](https://linear.app/onegovcloud/issue/OGC-1969) | [4adcb66f82](https://github.com/onegov/onegov-cloud/commit/4adcb66f825d3be0a67c27ef4cda190d18f9711d)

### Electionday

##### Adds additional date metadata to subscribers

`Feature` | [OGC-1882](https://linear.app/onegovcloud/issue/OGC-1882) | [1770d45927](https://github.com/onegov/onegov-cloud/commit/1770d45927b012e16ff7e99b6a56a6e869bd2158)

##### Include specific URLs for sub-results in SMS when possible

`Feature` | [OGC-1881](https://linear.app/onegovcloud/issue/OGC-1881) | [01eb7d8b03](https://github.com/onegov/onegov-cloud/commit/01eb7d8b034861d80a24166838f95974db679776)

### Feriennet

##### Make it possible to change attendee info without active period

`Bugfix` | [PRO-1341](https://linear.app/projuventute/issue/PRO-1341) | [8693110cd8](https://github.com/onegov/onegov-cloud/commit/8693110cd8edf4d4d93b58efadf790f82f3e9de5)

### Org

##### Avoid generating redundant file links for linked general files

This also updates WebTest to the newest version, since we need it in
order to test multi-file uploads.

`Bugfix` | [OGC-1967](https://linear.app/onegovcloud/issue/OGC-1967) | [27c3e25ed5](https://github.com/onegov/onegov-cloud/commit/27c3e25ed579219df1454d5fcfa36dd6708b640d)

### Pas

##### Generating various exports.

`Feature` | [OGC-1878](https://linear.app/onegovcloud/issue/OGC-1878) | [96f09cfc20](https://github.com/onegov/onegov-cloud/commit/96f09cfc200a20d153fa81ab5b4dccbaecba0f9b)

### Town6

##### Sidebar make person function as wide as document names and map

`Feature` | [NONE](#NONE) | [13d6a10ad3](https://github.com/onegov/onegov-cloud/commit/13d6a10ad3fbd27e9e26440acfdb47917ac6b467)

##### Icon Links

Correct margin and padding if there is no text

`Feature` | [OGC-1943](https://linear.app/onegovcloud/issue/OGC-1943) | [471d46565c](https://github.com/onegov/onegov-cloud/commit/471d46565c7158a752b41722125a600bdaffea13)

##### Make the context-specific-function multi line capable.

`Feature` | [OGC-1955](https://linear.app/onegovcloud/issue/OGC-1955) | [597a6cc034](https://github.com/onegov/onegov-cloud/commit/597a6cc034b87d7b3e727c9aa83e3cf38aafd4a4)

##### Main image in news

Enable the option to hide main images on news

`Bugfix` | [OGC-1903](https://linear.app/onegovcloud/issue/OGC-1903) | [53135169e2](https://github.com/onegov/onegov-cloud/commit/53135169e2b654ca6782f448e19446ae2c989680)

## test

`2024-12-09` | [9c3aee5da3...9460a55000](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...9460a55000)

### Swissvotes

##### Adds translations for Basel poster collection, adjusts order of poster sources

`Feature` | [SWI-42](https://linear.app/swissvotes/issue/SWI-42) | [4b8e08ca2b](https://github.com/onegov/onegov-cloud/commit/4b8e08ca2bacb5486bb69e5df322d89f56a5febc)

## 2024.57

`2024-12-06` | [c11857afe9...4506c6d109](https://github.com/OneGov/onegov-cloud/compare/c11857afe9^...4506c6d109)

### Agency

##### Import Staka LU: Organisation mapping if only office assigned

`Feature` | [OGC-1927](https://linear.app/onegovcloud/issue/OGC-1927) | [c11857afe9](https://github.com/onegov/onegov-cloud/commit/c11857afe96a8d4c88f559ce2a48150dfafd47de)

##### Staka LU Do not import person's notes

`Feature` | [OGC-1919](https://linear.app/onegovcloud/issue/OGC-1919) | [7327673bdf](https://github.com/onegov/onegov-cloud/commit/7327673bdfd733d27abc9e38a3ee888d12e291a3)

##### Staka LU: Introduce agency ids for import

`Feature` | [OGC-1921](https://linear.app/onegovcloud/issue/OGC-1921) | [8d665ca8f8](https://github.com/onegov/onegov-cloud/commit/8d665ca8f8ba71dbe7cb19e1a6562da892dacb52)

##### Staka LU: Support importing multiple memberships

`Feature` | [OGC-1891, OGC-1915](https://linear.app/onegovcloud/issue/OGC-1891, OGC-1915) | [b3d933d91c](https://github.com/onegov/onegov-cloud/commit/b3d933d91cc6a5161209addcd72bb82dfaa29fc0)

##### Staka LU: parse agency phone and address

`Feature` | [OGC-1923](https://linear.app/onegovcloud/issue/OGC-1923) | [5a8d8a4371](https://github.com/onegov/onegov-cloud/commit/5a8d8a4371a5a4e7d16c992b1a086ec4fdc30866)

### Directory

##### Use human field ids and preserve order in accordion mode

`Bugfix` | [OGC-1928](https://linear.app/onegovcloud/issue/OGC-1928) | [afe504d1ac](https://github.com/onegov/onegov-cloud/commit/afe504d1ac6b950544b164d689fcca7ba069f24c)

### Feriennet

##### Rename the field for health information

`Feature` | [PRO-1336](https://linear.app/projuventute/issue/PRO-1336) | [60dd10bbb7](https://github.com/onegov/onegov-cloud/commit/60dd10bbb7fe466ef376adf275f6d3c154f7332f)

### Fsi

##### Course Subscribtions

Ensure selected course is at least 6 years in the future from the last course the attendee subscribed to

`Feature` | [OGC-1912](https://linear.app/onegovcloud/issue/OGC-1912) | [ddf9e27fd1](https://github.com/onegov/onegov-cloud/commit/ddf9e27fd15e35c5586b3a4ed9ea4d8bbc4d21f2)

### Org

##### Editmode Buttons

Hide send button if layout.editmode is true

`Bugfix` | [f47e8e14d2](https://github.com/onegov/onegov-cloud/commit/f47e8e14d2b3245a240037cc1eea8ff775eb88c0)

### Swissvotes

##### Adds Plakatsammlung Basel as new source for voting posters

`Feature` | [SWI-42](https://linear.app/swissvotes/issue/SWI-42) | [3d679f1d52](https://github.com/onegov/onegov-cloud/commit/3d679f1d52e88c3e07dcc2d1c5928ee30a308f49)

### Town6

##### Change order in sidebar to contact, persons, docs, links, others

`Feature` | [OGC-1945](https://linear.app/onegovcloud/issue/OGC-1945) | [41a834c119](https://github.com/onegov/onegov-cloud/commit/41a834c119e97fef1839765f357a109797c3a1a9)

##### Add Sub sub title (h4) to redactor formatting menu

`Feature` | [OGC-1946](https://linear.app/onegovcloud/issue/OGC-1946) | [9830beac82](https://github.com/onegov/onegov-cloud/commit/9830beac8238e1f58e5f8649ef8f2b46c8dee9fd)

##### Add direct phone or mobile number in people overview

`Feature` | [OGC-1938](https://linear.app/onegovcloud/issue/OGC-1938) | [38ad6f3612](https://github.com/onegov/onegov-cloud/commit/38ad6f36126356d06f21c6191500fefeb6f2bcef)

##### Make empty selection for inline photoalbum possible.

The `ChoosenSelectField`, which was used previously, does not seem to render an empty choice.

`Bugfix` | [OGC-1933](https://linear.app/onegovcloud/issue/OGC-1933) | [d3b6bb45d4](https://github.com/onegov/onegov-cloud/commit/d3b6bb45d4d8a9c3bc1f3af7e7e9f66669926861)

##### Fixes photoswipe not working if photo album inlined in page.

`Bugfix` | [OGC-1934](https://linear.app/onegovcloud/issue/OGC-1934) | [0df602b882](https://github.com/onegov/onegov-cloud/commit/0df602b88269522b4159e6e36259b8c079f6c505)

##### Submissions for new entries

Rearrange condition so enable_submissions gets checked

`Bugfix` | [OGC-1929](https://linear.app/onegovcloud/issue/OGC-1929) | [0a2015d385](https://github.com/onegov/onegov-cloud/commit/0a2015d38520cd2d4d3e21772135f94c6cb18b15)

##### Adjust condition for actions view

Create variable for enable_update_notifications and use it for the condition.

`Bugfix` | [OGC-1929](https://linear.app/onegovcloud/issue/OGC-1929) | [7048310823](https://github.com/onegov/onegov-cloud/commit/704831082315153634a7b38ca058db1aec7b88c3)

### User

##### Adds OpenID Connect login provider

`Feature` | [OGC-1767](https://linear.app/onegovcloud/issue/OGC-1767) | [3c2800b994](https://github.com/onegov/onegov-cloud/commit/3c2800b994519824aa64a02c2d704985005ecbf5)

##### Fixes SAML2 not always skipping SLO, despite being disabled

`Bugfix` | [b8931d311f](https://github.com/onegov/onegov-cloud/commit/b8931d311fd7aa1a80a6f0af363a288d27ac188b)

### Winterthur

##### Fix json and csv mission report views in case of no vehicle symbol

`Bugfix` | [OGC-1819, OGC-1931](https://linear.app/onegovcloud/issue/OGC-1819, OGC-1931) | [a58353cec6](https://github.com/onegov/onegov-cloud/commit/a58353cec6db95d549e93448577887e19d5fb271)

##### Firefigher mission exports: date in iso format

`Bugfix` | [OGC-1932](https://linear.app/onegovcloud/issue/OGC-1932) | [db721e4ad8](https://github.com/onegov/onegov-cloud/commit/db721e4ad8ba94db4f840970653395718a68504d)

## 2024.56

`2024-11-26` | [d8727155ea...7ce0e4569a](https://github.com/OneGov/onegov-cloud/compare/d8727155ea^...7ce0e4569a)

## 2024.55

`2024-11-26` | [75d4cff3cf...0121dbe21d](https://github.com/OneGov/onegov-cloud/compare/75d4cff3cf^...0121dbe21d)

## 2024.54

`2024-11-26` | [896b8619c2...d7b7a777f5](https://github.com/OneGov/onegov-cloud/compare/896b8619c2^...d7b7a777f5)

### Org

##### External link form editbar buttons

Make sure all relevant buttons are in the edit bar.

`Bugfix` | [OGC-1917](https://linear.app/onegovcloud/issue/OGC-1917) | [1531f9b8a5](https://github.com/onegov/onegov-cloud/commit/1531f9b8a5dce12e59b8ff6230f64b166521fa80)

### Town6

##### Add option for inline photo album

`Feature` | [OGC-1886](https://linear.app/onegovcloud/issue/OGC-1886) | [9f34f2ced5](https://github.com/onegov/onegov-cloud/commit/9f34f2ced52007fee7d7b70d3c43842cdb7633a4)

## 2024.53

`2024-11-22` | [400849c1c3...9ddca9d407](https://github.com/OneGov/onegov-cloud/compare/400849c1c3^...9ddca9d407)

### Agency

##### Adds import command for staka lu

`Feature` | [OGC-1891](https://linear.app/onegovcloud/issue/OGC-1891) | [1e8ddc14bb](https://github.com/onegov/onegov-cloud/commit/1e8ddc14bbd10cbe53a4e5dad2b9fec0d30dfbb6)

##### Import Staka Luzern: Filter email addresses, log errors while importing

`Feature` | [OGC-1891](https://linear.app/onegovcloud/issue/OGC-1891) | [b20dfa40b3](https://github.com/onegov/onegov-cloud/commit/b20dfa40b3aa999b346b5960fb00100bae6ccff4)

### File

##### Should Ghostscript go astray, our fallback saves the day.

`Bugfix` | [OGC-1911](https://linear.app/onegovcloud/issue/OGC-1911) | [6859effbbb](https://github.com/onegov/onegov-cloud/commit/6859effbbbe47dd9dce642644817311a915fadf8)

### Files

##### Fix ajax request removing to many elements for action delete

`Bugfix` | [OGC-1851](https://linear.app/onegovcloud/issue/OGC-1851) | [6b23b2e7a0](https://github.com/onegov/onegov-cloud/commit/6b23b2e7a03b4bcfe1158cf40f897788c29c4a9c)

### Fsi

##### Condition for mail reminders

`Bugfix` | [OGC-1898](https://linear.app/onegovcloud/issue/OGC-1898) | [feafd8879d](https://github.com/onegov/onegov-cloud/commit/feafd8879d0eede6178cce40bc50c78ed8f4850e)

### Landsgemeinde

##### Footer Text

`Feature` | [24b85f82ed](https://github.com/onegov/onegov-cloud/commit/24b85f82ed196099dab2ceca27c8786b2e6c3dd9)

### Winterthur

##### Adds json and csv view to mission reports

`/mission-reports/json` resp. `/mission-reports/csv`

`Feature` | [OGC-1907](https://linear.app/onegovcloud/issue/OGC-1907) | [c55eb564a8](https://github.com/onegov/onegov-cloud/commit/c55eb564a849acb40927f1f02a7d8ab961dcacfc)

##### Adds open data description for mission reports

`Feature` | [OGC-1908](https://linear.app/onegovcloud/issue/OGC-1908) | [04d072f339](https://github.com/onegov/onegov-cloud/commit/04d072f339a572ae4bda06c65bb47e7090802407)

## 1

`2024-11-21` | [9c3aee5da3...e14871c0ba](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...e14871c0ba)

### Agency

##### Ensure a failing pdf file access does not crash application

`Bugfix` | [OGC-1906](https://linear.app/onegovcloud/issue/OGC-1906) | [c85c47ea7e](https://github.com/onegov/onegov-cloud/commit/c85c47ea7ecda50b85c4a26cd24377a7f1c637bc)

## 2024.52

`2024-11-07` | [057ee170cf...b896c374ce](https://github.com/OneGov/onegov-cloud/compare/057ee170cf^...b896c374ce)

### Core

##### Reviews silenced bandit errors and increases robustness

`Bugfix` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [aac58babb9](https://github.com/onegov/onegov-cloud/commit/aac58babb93843cc99bebf245db3bb95764c487b)

### Directory

##### Ensure all values can be displayed in accordion layout

`Bugfix` | [OGC-1895](https://linear.app/onegovcloud/issue/OGC-1895) | [3d6aa4d218](https://github.com/onegov/onegov-cloud/commit/3d6aa4d218a53c3246ebf1c7a02847d969c083fe)

### Feriennet

##### Add piwik to the feriennet CSP

`Feature` | [PRO-1264](https://linear.app/projuventute/issue/PRO-1264) | [48163dd50a](https://github.com/onegov/onegov-cloud/commit/48163dd50aa321067717fc978f85c4d9d2b6391a)

### Fsi

##### Remove invalid state filter for survey export

`Bugfix` | [OGC-1889](https://linear.app/onegovcloud/issue/OGC-1889) | [5d8df83efb](https://github.com/onegov/onegov-cloud/commit/5d8df83efb88918c5743b6ded5f0f08910310729)

##### Make Survey Submission Public

The SurveySubmission is finished, but it can still be edited.

`Bugfix` | [OGC-1850](https://linear.app/onegovcloud/issue/OGC-1850) | [612b2af593](https://github.com/onegov/onegov-cloud/commit/612b2af5932f72bb28c8a8d3ec0de9e2c38e8111)

### Landsgemeinde

##### Update timestamp in iframe via js

We now update the timestamp in the iframe video via js, which enables us to turn on autoplay without muting in certrain browsers.

`Feature` | [OGC-1668](https://linear.app/onegovcloud/issue/OGC-1668) | [403b5285c4](https://github.com/onegov/onegov-cloud/commit/403b5285c4f0c8909ad5d4e170900ddd77cfa7c3)

### Org

##### Only managers can add newsletters and see subscribers

`Bugfix` | [OGC-1890](https://linear.app/onegovcloud/issue/OGC-1890) | [a117d6bcc6](https://github.com/onegov/onegov-cloud/commit/a117d6bcc626f02a5eb702967950a5940b52b23e)

### Town6

##### Remove equalizer from cards

`Feature` | [476538ed18](https://github.com/onegov/onegov-cloud/commit/476538ed1801bb4f5efdfdde827db17cfe220d2f)

##### Reduce Export title size for person

`Bugfix` | [OGC-1887](https://linear.app/onegovcloud/issue/OGC-1887) | [5cce1360de](https://github.com/onegov/onegov-cloud/commit/5cce1360de7af9f76c3848ec5ae4d06831d61b26)

### Translator

##### Remove nationality column after migrating to meta

`Feature` | [OGC-1805](https://linear.app/onegovcloud/issue/OGC-1805) | [057ee170cf](https://github.com/onegov/onegov-cloud/commit/057ee170cf44f0768eff6a864aee9e3b0773b081)

### Wtfs

##### Remove wtfs application from code base

`Feature` | [OGC-1792](https://linear.app/onegovcloud/issue/OGC-1792) | [1154c6c0e9](https://github.com/onegov/onegov-cloud/commit/1154c6c0e932e680829e582ae14df54e87474647)

## 2024.51

`2024-10-25` | [70697c790f...41a2fd0aad](https://github.com/OneGov/onegov-cloud/compare/70697c790f^...41a2fd0aad)

### Electionday

##### Fixes license portion of catalog.rdf for Open Data Swiss

This also fixes the same bug for Landsgemeinde

`Bugfix` | [OGC-1729](https://linear.app/onegovcloud/issue/OGC-1729) | [0d5f068dd1](https://github.com/onegov/onegov-cloud/commit/0d5f068dd19aebddbad08fc231f0ace19db81d84)

### Fsi

##### Fix link pointing to 404.

`Bugfix` | [OGC-1885](https://linear.app/onegovcloud/issue/OGC-1885) | [4ee63be294](https://github.com/onegov/onegov-cloud/commit/4ee63be2945871f8c4c5ccc382954110aeea21a4)

### Landsgemeinde

##### Remove Label "Antrag"

`Feature` | [OGC-1846](https://linear.app/onegovcloud/issue/OGC-1846) | [54af2cd666](https://github.com/onegov/onegov-cloud/commit/54af2cd66613bf3165ea7b7a3974a2420f47bf18)

##### Open Data Page

`Feature` | [OGC-1704](https://linear.app/onegovcloud/issue/OGC-1704) | [8b5e7a7c85](https://github.com/onegov/onegov-cloud/commit/8b5e7a7c850fa2e9905cf5525b2c648ce4070fcd)

### Org

##### Ticket Permissions for Directories

Ticket permissions can now be set for single directories.

`Feature` | [OGC-1775](https://linear.app/onegovcloud/issue/OGC-1775) | [6f9d132a3e](https://github.com/onegov/onegov-cloud/commit/6f9d132a3e772fdae4253529f53794df51038bca)

##### Fixes removing linked people from an unordered list

`Bugfix` | [OGC-1883](https://linear.app/onegovcloud/issue/OGC-1883) | [bdc57edeb2](https://github.com/onegov/onegov-cloud/commit/bdc57edeb23e20d6a09dbe0bd5f079648263872f)

##### Make newsletters subscribers import more robust.

`Bugfix` | [OGC-1829](https://linear.app/onegovcloud/issue/OGC-1829) | [6b8516b668](https://github.com/onegov/onegov-cloud/commit/6b8516b668608f87acc0a9f4c259c0d494d76c71)

### Town6

##### Unify the look of the side-panel actions

`Feature` | [OGC-1855](https://linear.app/onegovcloud/issue/OGC-1855) | [70697c790f](https://github.com/onegov/onegov-cloud/commit/70697c790f43597461a02657950728ab36b38020)

##### Redesign the find your spot option

`Feature` | [OGC-1831](https://linear.app/onegovcloud/issue/OGC-1831) | [ad4def92d1](https://github.com/onegov/onegov-cloud/commit/ad4def92d1958368d17811fe376b9f1dd659d501)

##### Add Upload Button to Dropzone

`Feature` | [OGC-1848](https://linear.app/onegovcloud/issue/OGC-1848) | [4dbbbbe6a2](https://github.com/onegov/onegov-cloud/commit/4dbbbbe6a2fd9f0a9adff5241d6378cd98c3d4a8)

##### Adds organisation logo to transactional emails if available

`Feature` | [OGC-1733](https://linear.app/onegovcloud/issue/OGC-1733) | [f0388158f2](https://github.com/onegov/onegov-cloud/commit/f0388158f2208af9f3bb7146aaa6bac05f661d4a)

### Translator

##### Add command to recreate languages

```
onegov-translator --select /translator_directory/schaffhausen create-languages --dry-run
onegov-translator --select /translator_directory/schaffhausen force-delete-languages --dry-run
```

`Feature` | [OGC-1873](https://linear.app/onegovcloud/issue/OGC-1873) | [b2870a79a1](https://github.com/onegov/onegov-cloud/commit/b2870a79a113533ec17cdd43a192c30d27759941)

## 2024.50

`2024-10-11` | [3f9655c562...6d17e690a8](https://github.com/OneGov/onegov-cloud/compare/3f9655c562^...6d17e690a8)

### Fsi

##### Survey improvements

-    Exports can be made for single or multiple submission windows
-    Submissions can now be deleted
-    Changes to the survey are now prevented if there are any submissions
-    Once the submission is made it is automatically confirmed, but can still be edited

`Feature` | [OGC-1821](https://linear.app/onegovcloud/issue/OGC-1821) | [eb0d0926ed](https://github.com/onegov/onegov-cloud/commit/eb0d0926edc51eb841747b8f31c16861628bc843)

### Newsletter

##### Move update subscription from edit bar to a link

`Feature` | [NONE](#NONE) | [7a76ef78e9](https://github.com/onegov/onegov-cloud/commit/7a76ef78e976d3aac3247179ab5cf16c152ac0ce)

### Org

##### Make editing rule for allocations possible.

`Feature` | [OGC-1397](https://linear.app/onegovcloud/issue/OGC-1397) | [3f9655c562](https://github.com/onegov/onegov-cloud/commit/3f9655c5627815d44a323795329c8c26114851b8)

##### Pins ancestor choices in contact inheritance select

`Feature` | [OGC-1853](https://linear.app/onegovcloud/issue/OGC-1853) | [5e97e3ee40](https://github.com/onegov/onegov-cloud/commit/5e97e3ee40cb61ecc22864cfc597262aa78c1d29)

##### Fixes regression in `login.pt` due to different providers shape

`Bugfix` | [5ab94875f5](https://github.com/onegov/onegov-cloud/commit/5ab94875f515ef8b36d62394c474f5863b3e8db6)

### Swissvotes

##### Update column name

`Bugfix` | [SWI-50](https://linear.app/swissvotes/issue/SWI-50) | [3b733fb1ad](https://github.com/onegov/onegov-cloud/commit/3b733fb1adfe54add16c829bd4951b859de3c292)

### Town6

##### Restyling of newsletter

Some style improvements of the newsletter and added images of events if there are any

`Feature` | [OGC-1788](https://linear.app/onegovcloud/issue/OGC-1788) | [981242fcfa](https://github.com/onegov/onegov-cloud/commit/981242fcfa871e767bdfaa068bb300edc4d49939)

### User

##### Actually allows multiple providers of the same type to coexist

`Bugfix` | [OGC-1750](https://linear.app/onegovcloud/issue/OGC-1750) | [59474454b8](https://github.com/onegov/onegov-cloud/commit/59474454b89a4ad3ac5cc7c1bc9c2c66a11d7285)

## 2024.49

`2024-10-07` | [4b2186bb38...1b5993f16a](https://github.com/OneGov/onegov-cloud/compare/4b2186bb38^...1b5993f16a)

### Feriennet

##### Fix definition of "overfull"

Attendees, who are blocked aren't counted for an occasion to be "overfull"

`Bugfix` | [OGC-1312](https://linear.app/onegovcloud/issue/OGC-1312) | [d17ab4d9a9](https://github.com/onegov/onegov-cloud/commit/d17ab4d9a907f5e892261302b9cf4ce26185f228)

### Form

##### Fixes `ExpectedExtensions` not working with `.mp3` file ending

`Bugfix` | [OGC-1795](https://linear.app/onegovcloud/issue/OGC-1795) | [223b0fbea2](https://github.com/onegov/onegov-cloud/commit/223b0fbea20717fa0d89f14f8918c2aedfeb2fb3)

### Org

##### Add `analytics` subdomain to child src content policy.

`Feature` | [OGC-1787](https://linear.app/onegovcloud/issue/OGC-1787) | [4c05f081ac](https://github.com/onegov/onegov-cloud/commit/4c05f081ac6c2a2ea89fcd343e6e8d53d75c2d6f)

##### Change message text newsletter.

`Bugfix` | [OGC-1828](https://linear.app/onegovcloud/issue/OGC-1828) | [943685c2d2](https://github.com/onegov/onegov-cloud/commit/943685c2d2012a9e9af1a07916deec0494f44694)

##### Render markup of survey text correctly

`Bugfix` | [OGC-1844](https://linear.app/onegovcloud/issue/OGC-1844) | [49113d3823](https://github.com/onegov/onegov-cloud/commit/49113d3823ef753e7928008b465d4fd34f5a1276)

### Town6

##### Don't linkify the leads in the form and survey overview

`Bugfix` | [OGC-1818](https://linear.app/onegovcloud/issue/OGC-1818) | [e455e2c0c8](https://github.com/onegov/onegov-cloud/commit/e455e2c0c89b26986215b051bd2473f9a57e86f2)

### User

##### Allows configuring more than one instance of the same provider

`Feature` | [OGC-1856](https://linear.app/onegovcloud/issue/OGC-1856) | [3004111e8b](https://github.com/onegov/onegov-cloud/commit/3004111e8bb57161c1476a7ae2529e80f29b4a72)

## 2024.48

`2024-09-19` | [5f073ef498...29b45cbaed](https://github.com/OneGov/onegov-cloud/compare/5f073ef498^...29b45cbaed)

### Core

##### Improves performance of `orm_cached` with an in-memory cache

This avoid deserialization overhead for potentially very large nested
structures, such as the pages tree. While still properly invalidating
the cache between multiple processes.

`Performance` | [OGC-1827](https://linear.app/onegovcloud/issue/OGC-1827) | [0a9647dad4](https://github.com/onegov/onegov-cloud/commit/0a9647dad4984131ece0332457e142109972f1d9)

### Org

##### Newsletter Text

Add "You no longer wish to receive the newsletter?" to the newsletter footer.

`Feature` | [OGC-1817](https://linear.app/onegovcloud/issue/OGC-1817) | [1358e35fcd](https://github.com/onegov/onegov-cloud/commit/1358e35fcdef1a693ec1b23d025cdd4723671003)

##### Avoids generating a giant list of fields in `PersonLinkExtension`

Instead use a dynamic `FieldList` like with `GeneralFileLinkExtension`

`Feature` | [OGC-1796](https://linear.app/onegovcloud/issue/OGC-1796) | [af229a696b](https://github.com/onegov/onegov-cloud/commit/af229a696bce71e4bb61498698259bf0efa30e05)

##### Make sure anchors in URLs are not viewed as hashtags

`Bugfix` | [OGC-1816](https://linear.app/onegovcloud/issue/OGC-1816) | [ece085a433](https://github.com/onegov/onegov-cloud/commit/ece085a433955db54faa921994c1684f5bfa03a5)

##### Fixes incorrect news link in navigation

`Bugfix` | [OGC-1843](https://linear.app/onegovcloud/issue/OGC-1843) | [95748406d2](https://github.com/onegov/onegov-cloud/commit/95748406d2d339acaabb8a1f44d0de3dd95de81d)

### Town6

##### Make file details closable

`Feature` | [OGC-1822](https://linear.app/onegovcloud/issue/OGC-1822) | [201cba10da](https://github.com/onegov/onegov-cloud/commit/201cba10dafe2554e43ae2a0f2dab244aef38baf)

##### Testimonial Slider Size

Fix size of testimonial slider

`Bugfix` | [OGC-1800](https://linear.app/onegovcloud/issue/OGC-1800) | [91aeb84c4f](https://github.com/onegov/onegov-cloud/commit/91aeb84c4f24f507f4e1822c193cd0eca2e3d16f)

## 2024.47

`2024-09-13` | [4830594bc9...10162c037d](https://github.com/OneGov/onegov-cloud/compare/4830594bc9^...10162c037d)

### Api

##### Only log unexpected exceptions in `ApiException`

`Bugfix` | [d64955e5c6](https://github.com/onegov/onegov-cloud/commit/d64955e5c68eec6fffefde7f9ce69f543e9be87c)

### Fsi

##### Hide OGC-Login in FSI in production

`Feature` | [8d38490cfe](https://github.com/onegov/onegov-cloud/commit/8d38490cfea440623a679d744fa34b8b363b0913)

##### Search Layout Error

`Bugfix` | [ee376cdd14](https://github.com/onegov/onegov-cloud/commit/ee376cdd141391e40c46ad8a2f41cee69177c471)

### Intranet

##### Hide search form

Hide search form if client isn't logged in

`Bugfix` | [OGC-1793](https://linear.app/onegovcloud/issue/OGC-1793) | [7f16b0dd21](https://github.com/onegov/onegov-cloud/commit/7f16b0dd21518440c97ce67d0d53b0a63045c86e)

### Landsgemeinde

##### Remove extra titles for assembly items

`Feature` | [OGC-1808](https://linear.app/onegovcloud/issue/OGC-1808) | [47768a5c28](https://github.com/onegov/onegov-cloud/commit/47768a5c28b629dabed535b962950c9b1ef244ea)

### Org

##### Avoids expensive query when no filters have been defined

`Bugfix` | [5cb2d88abb](https://github.com/onegov/onegov-cloud/commit/5cb2d88abb3321827c2d866dd9a1fffc71732d41)

##### Only sends directory entry notifications for public entries

`Bugfix` | [OGC-1806](https://linear.app/onegovcloud/issue/OGC-1806) | [fb931d37bc](https://github.com/onegov/onegov-cloud/commit/fb931d37bca57c5edb93c5dc03b0715d4e5d5dc7)

##### Also avoids sending a notification for unpublished entries

`Bugfix` | [OGC-1806](https://linear.app/onegovcloud/issue/OGC-1806) | [291df80027](https://github.com/onegov/onegov-cloud/commit/291df80027dbea6d7ed7a3518adc819cf2fb5bd1)

##### Avoids storing ORM objects in `orm_cached` properties

This should improve reliability and should introduce less flaky
behavior caused by incorrect merges of objects into the session.

`Bugfix` | [OGC-1813](https://linear.app/onegovcloud/issue/OGC-1813) | [f8645321a0](https://github.com/onegov/onegov-cloud/commit/f8645321a0cd0bad94aaff4a1879fc98e8cedf6c)

### People

##### Vcard export fails if no zip code was provided in fields `location_code_city` or `postal_code_city`

`Bugfix` | [OGC-1826](https://linear.app/onegovcloud/issue/OGC-1826) | [9254b4e9cf](https://github.com/onegov/onegov-cloud/commit/9254b4e9cf09442e2ea98a98609833f0910b1b9a)

### Swissvotes

##### Additional Column for LeeWas polls

`Feature` | [SWI-50](https://linear.app/swissvotes/issue/SWI-50) | [f96344313f](https://github.com/onegov/onegov-cloud/commit/f96344313fbabfc5cd7fbec14598911eb2692531)

### Ticket

##### Directory Entry Handler allows to withdraw ticket rejection

`Feature` | [OGC-1765](https://linear.app/onegovcloud/issue/OGC-1765) | [048124170c](https://github.com/onegov/onegov-cloud/commit/048124170cca270ced2a2f6fcde6ef78765ea9c1)

### Town6

##### Adds footer settings for linkedin and tiktok

`Feature` | [OGC-1791](https://linear.app/onegovcloud/issue/OGC-1791) | [93f6678e46](https://github.com/onegov/onegov-cloud/commit/93f6678e465a911b327e24330886eebf37a68cad)

##### Improve /files layout style

`Feature` | [NONE](#NONE) | [7e7cd8987e](https://github.com/onegov/onegov-cloud/commit/7e7cd8987e111691fd24d5e19fc7fee8f38aa343)

##### Field Display

Remove field if there are no TicketPermissions

`Bugfix` | [OGC-1766](https://linear.app/onegovcloud/issue/OGC-1766) | [4d97fe7ab3](https://github.com/onegov/onegov-cloud/commit/4d97fe7ab352fd3de906e5a4e72376fa976e98cc)

##### Survey Export Town6

`Bugfix` | [OGC-1821](https://linear.app/onegovcloud/issue/OGC-1821) | [541b6ae8b5](https://github.com/onegov/onegov-cloud/commit/541b6ae8b55583ca236d32b50673ccf3752f7874)

### Translator

##### Adjust template variable name for multiple nationalities

`Bugfix` | [OGC-1805](https://linear.app/onegovcloud/issue/OGC-1805) | [19e3929e07](https://github.com/onegov/onegov-cloud/commit/19e3929e07ef2f7116c91d1ada934eeed2f4f52b)

##### Fix missing translation in AKK ticket

`Bugfix` | [OGC-1820](https://linear.app/onegovcloud/issue/OGC-1820) | [dc97c20907](https://github.com/onegov/onegov-cloud/commit/dc97c209071e320c310d10e8b3007f36c6b9ca33)

### User

##### Makes SLO with SAML2 optional

`Feature` | [OGC-1751](https://linear.app/onegovcloud/issue/OGC-1751) | [60107a76d3](https://github.com/onegov/onegov-cloud/commit/60107a76d3343340a73a1ad574bfe4465fae7d2c)

### Winterthur

##### Roadwork show title

`Bugfix` | [OGC-1706](https://linear.app/onegovcloud/issue/OGC-1706) | [7eca0726c1](https://github.com/onegov/onegov-cloud/commit/7eca0726c1f28b6a55fa38055601873fdf2b811c)

## 2024.46

`2024-08-30` | [9346ca33c7...bdcf6b6ed8](https://github.com/OneGov/onegov-cloud/compare/9346ca33c7^...bdcf6b6ed8)

## 2024.45

`2024-08-30` | [213290a149...1e25012897](https://github.com/OneGov/onegov-cloud/compare/213290a149^...1e25012897)

### Directory

##### Fixing typos in translations

`Bugfix` | [NONE](#NONE) | [8b267dc2c0](https://github.com/onegov/onegov-cloud/commit/8b267dc2c0d117f60b5b1c88231612e2fd268ac9)

### Event

##### Re-add lost view handle_edit_event_filters

`Bugfix` | [OGC-1784](https://linear.app/onegovcloud/issue/OGC-1784) | [2728f89567](https://github.com/onegov/onegov-cloud/commit/2728f89567a2d479ce45074e2d755c8a050ee82e)

### Newsletter

##### Support for newsletter category definition and subscription

An organization can define newsletter categories. Subscribing users can select their categories of interest and will only receive newsletters that report on at least one of their subscribed categories.

`Feature` | [OGC-1725](https://linear.app/onegovcloud/issue/OGC-1725) | [ae836fb2ac](https://github.com/onegov/onegov-cloud/commit/ae836fb2ac282303dfe63fb74ab2ab8b2dbd951e)

### Org

##### Allow operlapping submission windows

Allow overlapping of submission windows as long as they have a title.

`Feature` | [OGC-1785](https://linear.app/onegovcloud/issue/OGC-1785) | [77de18765e](https://github.com/onegov/onegov-cloud/commit/77de18765e343dcd08f592bed3e16a010bcbba2b)

##### Allows pages to inherit contact info from another topic

`Feature` | [OGC-1798](https://linear.app/onegovcloud/issue/OGC-1798) | [38afa09864](https://github.com/onegov/onegov-cloud/commit/38afa09864c3118d0a30d08f424107243b78700d)

### Town6

##### Homepage structure

Update homepage structure so the slider doesn't have an unnecessary white space below.

`Bugfix` | [b9a34863d9](https://github.com/onegov/onegov-cloud/commit/b9a34863d9293649b77ca1e25d4bd5f5c87a5f5b)

##### Fixes contact block rendering in surveys list

`Bugfix` | [8649a30fe9](https://github.com/onegov/onegov-cloud/commit/8649a30fe90b3b72c59d21d9fc71adffca4c7615)

##### Fixes style for link groups in edit bar

The link group does not appear on the same level as the single links

`Bugfix` | [OGC-1799](https://linear.app/onegovcloud/issue/OGC-1799) | [fae03060c6](https://github.com/onegov/onegov-cloud/commit/fae03060c6912328681f20bd718cd873baafab1a)

### Translator

##### Explicitly list translators last and first name in order to prevent confusion

Translator's last name always in uppercase.

`Feature` | [OGC-1814](https://linear.app/onegovcloud/issue/OGC-1814) | [6251d1b894](https://github.com/onegov/onegov-cloud/commit/6251d1b8943fe454dba2c8978b22d57df2f3807f)

##### Fill nationality of translators in letter template

`Bugfix` | [OGC-1805](https://linear.app/onegovcloud/issue/OGC-1805) | [011c922505](https://github.com/onegov/onegov-cloud/commit/011c922505df4f709970942751c0b341df2636a3)

### Winterthur

##### Force landscape mode for shift schedule image

`Bugfix` | [OGC-1809](https://linear.app/onegovcloud/issue/OGC-1809) | [97abd794e3](https://github.com/onegov/onegov-cloud/commit/97abd794e30cb1907d55b77e7dad4d76f7a4d856)

## 2024.44

`2024-08-19` | [cc5f3c0f1b...dc35c81ad8](https://github.com/OneGov/onegov-cloud/compare/cc5f3c0f1b^...dc35c81ad8)

### Fsi

##### UI Update to Foundation 6

`Feature` | [OGC-1748](https://linear.app/onegovcloud/issue/OGC-1748) | [245af37067](https://github.com/onegov/onegov-cloud/commit/245af3706789980a8e499c5f8519430fe40a49b6)

### People

##### Cleanup/Remove cli cmd and data migration script for agency address parsed from portrait field

`Feature` | [OGC-1053](https://linear.app/onegovcloud/issue/OGC-1053) | [e5c3c3f9db](https://github.com/onegov/onegov-cloud/commit/e5c3c3f9dbb049f38398f3e2aaa4096d59e261f7)

## 2024.43

`2024-08-13` | [9a317394e2...5e0d0a928e](https://github.com/OneGov/onegov-cloud/compare/9a317394e2^...5e0d0a928e)

### Agency

##### Allows person mutations to be supplied via the API

`Feature` | [OGC-1773](https://linear.app/onegovcloud/issue/OGC-1773) | [9cd4cfd16c](https://github.com/onegov/onegov-cloud/commit/9cd4cfd16c9e2e9edf7343b92d02b70ce810b046)

### Electionday

##### Adds Auth view for TOTP second factor

`Feature` | [SEA-1413](https://linear.app/seantis/issue/SEA-1413) | [9adbe66e6c](https://github.com/onegov/onegov-cloud/commit/9adbe66e6c9ecd578b84fefbc210fd03d54c34d6)

### Fsi

##### Fix result display of radio buttons

`Bugfix` | [OGC-1612](https://linear.app/onegovcloud/issue/OGC-1612) | [3ddc62c936](https://github.com/onegov/onegov-cloud/commit/3ddc62c936bd72e6f04be68b614aa323c9487a5f)

### Gazette

##### Adds Auth view for TOTP second factor

`Feature` | [SEA-1413](https://linear.app/seantis/issue/SEA-1413) | [ce13e5bad3](https://github.com/onegov/onegov-cloud/commit/ce13e5bad38edeee01825ad6188f95c009a27436)

### Intranet

##### UI Update to foundation 6

`Feature` | [OGC-1772](https://linear.app/onegovcloud/issue/OGC-1772) | [ffbae8ab6a](https://github.com/onegov/onegov-cloud/commit/ffbae8ab6a6d07ff9dba861dbca0cfe78bca1771)

### Landsgemeinde

##### Add missing closing tag

`Bugfix` | [OGC-1680](https://linear.app/onegovcloud/issue/OGC-1680) | [c1da31fb1f](https://github.com/onegov/onegov-cloud/commit/c1da31fb1fb69d863c2e4c02f4aa83507d62e959)

### Org

##### Move and change description of field "delete_when_expired"

`Feature` | [OGC-1764](https://linear.app/onegovcloud/issue/OGC-1764) | [7a6413699e](https://github.com/onegov/onegov-cloud/commit/7a6413699e6a34818de6b3bc94eb6684aa7801b5)

### Swissvotes

##### Adds Auth view for TOTP second factor

`Feature` | [SEA-1413](https://linear.app/seantis/issue/SEA-1413) | [e0db0be0fe](https://github.com/onegov/onegov-cloud/commit/e0db0be0fe670015150cb7f48a9036457428291e)

### Ticket

##### Timeline misses state changes 'archived', 'recovered from archive' and 'assigned'

`Bugfix` | [OGC-1779](https://linear.app/onegovcloud/issue/OGC-1779) | [73360ebc41](https://github.com/onegov/onegov-cloud/commit/73360ebc41206ae451f1946d129df52af5cf1215)

### Town6

##### Display people images in sidebar

`Feature` | [OGC-1600](https://linear.app/onegovcloud/issue/OGC-1600) | [10970daa0a](https://github.com/onegov/onegov-cloud/commit/10970daa0af8e50e81ce1100dc8b53f353996e89)

### Translator

##### Align mandatory fields for internal and external form (social security number, email, mobile)

`Feature` | [OGC-1754](https://linear.app/onegovcloud/issue/OGC-1754) | [5eafa8273d](https://github.com/onegov/onegov-cloud/commit/5eafa8273def0c63029d2fad84a7ea6544eab922)

##### Translator details in three columns

`Feature` | [OGC-1758](https://linear.app/onegovcloud/issue/OGC-1758) | [119ba36b7b](https://github.com/onegov/onegov-cloud/commit/119ba36b7b384126fff0d97bdbe0fe4cd54ec655)

##### Request translator to check data after a year

`Feature` | [OGC-1756](https://linear.app/onegovcloud/issue/OGC-1756) | [6565b298d8](https://github.com/onegov/onegov-cloud/commit/6565b298d8444df8fd65159ee6cf7e45ea83e1a4)

### Wtfs

##### Adds Auth view for TOTP second factor

`Feature` | [OGC-1413](https://linear.app/onegovcloud/issue/OGC-1413) | [91a94ceca0](https://github.com/onegov/onegov-cloud/commit/91a94ceca07fc8c181203c7f8939ef1e66506650)

## 2024.42

`2024-08-01` | [ef924060e7...b77c4e79b4](https://github.com/OneGov/onegov-cloud/compare/ef924060e7^...b77c4e79b4)

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

