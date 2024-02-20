# Changes

## 2024.8

`2024-02-16` | [61d0b56270...1a2194e801](https://github.com/OneGov/onegov-cloud/compare/61d0b56270^...1a2194e801)

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

`Feature` | [ogc-1454](#ogc-1454) | [e641db1512](https://github.com/onegov/onegov-cloud/commit/e641db15128b3e337e1fa28b296a902a7a80b252)

##### Reservation note is always shown and adjusted to inform user multiple selections are possible

`Feature` | [ogc-1450](#ogc-1450) | [f2dfceab9e](https://github.com/onegov/onegov-cloud/commit/f2dfceab9e63ab3be2811bc327c3095a8fd1f7da)

##### Adds support for videos in directory entries

`Feature` | [ogc-1408](#ogc-1408) | [6ddc85ec7a](https://github.com/onegov/onegov-cloud/commit/6ddc85ec7ab67882a7a58f21dff2bcfb4de1c8e2)

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

`Feature` | [ogc-1454](#ogc-1454) | [a97af2900a](https://github.com/onegov/onegov-cloud/commit/a97af2900a49c8d45498985873d58dec7ca941f3)

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

`Feature` | [ogc-1334](#ogc-1334) | [88c7597c18](https://github.com/onegov/onegov-cloud/commit/88c7597c18589c360f310d2df4ae411674d10c5b)

##### Adds reservation details to initial reservation email

`Feature` | [ogc-1334](#ogc-1334) | [374f35cfc2](https://github.com/onegov/onegov-cloud/commit/374f35cfc2d5a058ebfc7a511dd26f7b17780b5a)

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

`Feature` | [Ogc-1415](#Ogc-1415) | [22973c83fe](https://github.com/onegov/onegov-cloud/commit/22973c83fea7f3fc3da4a34fa001a3477cc76c93)

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

`Bugfix` | [ogc-1282](#ogc-1282) | [67940f955e](https://github.com/onegov/onegov-cloud/commit/67940f955e98c2c2290ea9bdebe8d536f42fe644)

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

`Bugfix` | [ogc-1383](#ogc-1383) | [d67dbc756f](https://github.com/onegov/onegov-cloud/commit/d67dbc756f14d0756ca52c4af453191c64b8ce54)

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

`Feature` | [ogc-1383](#ogc-1383) | [3b3b08f5ce](https://github.com/onegov/onegov-cloud/commit/3b3b08f5ced9d8e142ef18174f32376a69dfc2f0)

### Town

##### Submissions are now ordered by name

`Feature` | [ogc-1345](#ogc-1345) | [d6b4438fe0](https://github.com/onegov/onegov-cloud/commit/d6b4438fe038d16a980bee7973c7c566e67cf14e)

## 2023.62

`2023-12-12` | [a6bf5cf964...a780435e85](https://github.com/OneGov/onegov-cloud/compare/a6bf5cf964^...a780435e85)

### Directories

##### Fix typo in translation in directory export view

`Bugfix` | [ogc-1348](#ogc-1348) | [1fb939568d](https://github.com/onegov/onegov-cloud/commit/1fb939568d35c6a4fd2619b4de9e123c5319c1e8)

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

`Bugfix` | [ogc-1349](#ogc-1349) | [bc717a18be](https://github.com/onegov/onegov-cloud/commit/bc717a18becbd6d537b2d8c203a8279d25d61bf5)

### Reservations

##### Show pending approval tool tip only if reservation pending

`Bugfix` | [ogc-1338](#ogc-1338) | [a6bf5cf964](https://github.com/onegov/onegov-cloud/commit/a6bf5cf964e03046d845306219506e3884a112c3)

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

`Bugfix` | [ogc-1331](#ogc-1331) | [fa0d2b9393](https://github.com/onegov/onegov-cloud/commit/fa0d2b9393a4ee822b0faac11fe8c0087e407485)

### Tickets

##### Condense ticket status message when closed

`Feature` | [ogc-1330](#ogc-1330) | [971ba389e7](https://github.com/onegov/onegov-cloud/commit/971ba389e7fc561db09c07ff4591e3c6541ef0ff)

### Town6

##### Add Test Version of Chat-Function

Town6: Add Test Version of Chat-Function

`Feature` | [16c237773f](https://github.com/onegov/onegov-cloud/commit/16c237773f211243a82f6382ffdb17b8a71a962f)

## 2023.59

`2023-11-13` | [3f2cc6c3b1...90927b7ecb](https://github.com/OneGov/onegov-cloud/compare/3f2cc6c3b1^...90927b7ecb)

### Test

##### Mark occasionally failing web test as 'flaky' and fix splinter api change

`Bugfix` | [None](#None) | [3f2cc6c3b1](https://github.com/onegov/onegov-cloud/commit/3f2cc6c3b142264de1ec60e9d695f95a0bed9fce)

## 2023.58

`2023-11-10` | [e42602c1ec...cedb02aae2](https://github.com/OneGov/onegov-cloud/compare/e42602c1ec^...cedb02aae2)

## 2023.57

`2023-11-10` | [7602e5eefc...97404f538b](https://github.com/OneGov/onegov-cloud/compare/7602e5eefc^...97404f538b)

**Upgrade hints**
- Change map settings of all instances from Zug
### Events

##### Anthrazit xml export: Fix missing event if series started in the past

`Bugfix` | [ogc-1320](#ogc-1320) | [6cb0177c17](https://github.com/onegov/onegov-cloud/commit/6cb0177c177eb2b4936ed5ab6800a8bffe39aeb0)

##### Anthrazit xml export: Replace CR, LF with html br tag

`Bugfix` | [ogc-1320](#ogc-1320) | [30992412df](https://github.com/onegov/onegov-cloud/commit/30992412df8e955a2556535eb748de9091fbde71)

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

`Feature` | [ogc-1320](#ogc-1320) | [30efa28176](https://github.com/onegov/onegov-cloud/commit/30efa28176945afa6400c490c4005c775ba38ba6)

##### Add assets for event form independent of tag usage

`Bugfix` | [ogc-1318](#ogc-1318) | [edc89417b7](https://github.com/onegov/onegov-cloud/commit/edc89417b74d1490c03164f98cb09fcb9086b949)

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

## 2023.55

`2023-10-27` | [ca67f7b542...110e196f6e](https://github.com/OneGov/onegov-cloud/compare/ca67f7b542^...110e196f6e)

### Org

##### Adds an mTAN access level to resources

Protected resources can only be viewed by the public after inputting a
mTAN that was sent to their mobile device. The number of requests may
optionally be limited as well as the duration of a mTAN session.

`Feature` | [OGC-917](https://linear.app/onegovcloud/issue/OGC-917) | [ba4e930e42](https://github.com/onegov/onegov-cloud/commit/ba4e930e428665bd28d26e77297b130b2ec76c59)

##### Automatic archiving and deletion of tickets.

`Feature` | [OGC-58](https://linear.app/onegovcloud/issue/OGC-58) | [f7ecae3b9e](https://github.com/onegov/onegov-cloud/commit/f7ecae3b9e2b63354aefb4f7de5ab89509da0eed)

##### Fixes deletion of pages with linked files

`Bugfix` | [ca67f7b542](https://github.com/onegov/onegov-cloud/commit/ca67f7b54271f4e2eabefceee270fc37ad632ccd)

## 2023.54

`2023-10-24` | [0e85c77c26...4398f3fd12](https://github.com/OneGov/onegov-cloud/compare/0e85c77c26^...4398f3fd12)

### Feriennet

##### Add Rega logo

`Feature` | [PRO-1217](https://linear.app/projuventute/issue/PRO-1217) | [3e5adeeb82](https://github.com/onegov/onegov-cloud/commit/3e5adeeb82950c20d2b2137a9866b4c7a3c1884b)

### Org

##### Displays filters in event form regardless of user privileges

`Bugfix` | [OGC-1308](https://linear.app/onegovcloud/issue/OGC-1308) | [0e85c77c26](https://github.com/onegov/onegov-cloud/commit/0e85c77c2620382158dc18d86219c5d529fabcd9)

## 2023.53

`2023-10-23` | [b83715b9b1...4d3218f204](https://github.com/OneGov/onegov-cloud/compare/b83715b9b1^...4d3218f204)

### Feriennet

##### Update content security policy

`Bugfix` | [3733cb188b](https://github.com/onegov/onegov-cloud/commit/3733cb188b93b8f50c5b368350fb113e56c616b7)

### Landsgemeinde

##### Minor Adjusment

`Feature` | [OGC-1286](https://linear.app/onegovcloud/issue/OGC-1286) | [b83715b9b1](https://github.com/onegov/onegov-cloud/commit/b83715b9b103e448ab409b6e228086e892ca9c66)

### Winterthur

##### Enable resizer for Single Events

`Bugfix` | [OGC-1047](https://linear.app/onegovcloud/issue/OGC-1047) | [92984a8279](https://github.com/onegov/onegov-cloud/commit/92984a8279b4ca7f8256bdd06e679887539b2300)

## 2023.52

`2023-10-23` | [d8d88e831a...f1d513bda8](https://github.com/OneGov/onegov-cloud/compare/d8d88e831a^...f1d513bda8)

### Ballot

##### Fixes various hybrid properties.

`Bugfix` | [OGC-533](https://linear.app/onegovcloud/issue/OGC-533) | [d8d88e831a](https://github.com/onegov/onegov-cloud/commit/d8d88e831adecb0a4a604711aa1c4a4e6df279c4)

### Core

##### Adds compatibility with arrow 1.3.

`Feature` | [OGC-122](https://linear.app/onegovcloud/issue/OGC-122) | [eb573a8efc](https://github.com/onegov/onegov-cloud/commit/eb573a8efc03205eb6321ded262b55bcae1e86fb)

### Election Day

##### Fixes election-candidates-table widget.

`Bugfix` | [9133404a16](https://github.com/onegov/onegov-cloud/commit/9133404a160f8e7d4bfce01afe926e31ee0ebcb2)

##### Fixes screen deletion message.

`Bugfix` | [5811a56f85](https://github.com/onegov/onegov-cloud/commit/5811a56f851b9af06b467fd46b3ae93425873271)

##### Fixes column classes.

`Bugfix` | [20b0ec15a9](https://github.com/onegov/onegov-cloud/commit/20b0ec15a90da0b76f9b45e19e2356f15738ba87)

##### Fixes missing expats in counted-entities widget.

`Bugfix` | [OGC-1302](https://linear.app/onegovcloud/issue/OGC-1302) | [da715fb62f](https://github.com/onegov/onegov-cloud/commit/da715fb62ffcb7a3fb239372673885093d4fba05)

##### Try to bypass browser cache when reloading screens.

`Bugfix` | [4a516b8bba](https://github.com/onegov/onegov-cloud/commit/4a516b8bbaf1d0b59a3aa09724cd1ccc893c64cf)

##### Relax vote sanity checks for uncounted results.

`Bugfix` | [c37c98c379](https://github.com/onegov/onegov-cloud/commit/c37c98c379660ebabbfe867d8dd66ced9128562d)

##### Fixes vote statistics sorting.

`Bugfix` | [427a528340](https://github.com/onegov/onegov-cloud/commit/427a5283407005de457e805b91b883a5905752f4)

### Org

##### Fixes the directory import for edge case.

`Bugfix` | [OGC-338](https://linear.app/onegovcloud/issue/OGC-338) | [c62f9fcaa2](https://github.com/onegov/onegov-cloud/commit/c62f9fcaa297d5883c8e8d16c6d409441160ba31)

## 2023.51

`2023-10-16` | [99ad14d5ba...7ad07bd03e](https://github.com/OneGov/onegov-cloud/compare/99ad14d5ba^...7ad07bd03e)

### Stubs

##### Fixes linting error.

`Bugfix` | [99ad14d5ba](https://github.com/onegov/onegov-cloud/commit/99ad14d5ba8aa9b28e87b922474dedfbcab9787b)

## 2023.50

`2023-10-16` | [cd3f1d4a2a...110d72fade](https://github.com/OneGov/onegov-cloud/compare/cd3f1d4a2a^...110d72fade)

### Core

##### Adds a SMS delivery queue and spooler

Similar to email the delivery can be triggered using a CLI command, but
we also add a spooler which continually monitors the queue for additions
and delivers them more or less immediately.

    onegov-core sendsms
    onegov-core sms-spooler

This replaces the old delivery queue in ElectionDay

`Feature` | [OGC-1285](https://linear.app/onegovcloud/issue/OGC-1285) | [ce7a7558d4](https://github.com/onegov/onegov-cloud/commit/ce7a7558d4ec8c94764b45bdc599d12a812dae67)

### Election Day

##### Improve some queries.

`Bugfix` | [10706b13a1](https://github.com/onegov/onegov-cloud/commit/10706b13a11769f5674ea04a02a29b1fb5d15d0c)

##### Remove untested and failing view.

`Bugfix` | [851159db58](https://github.com/onegov/onegov-cloud/commit/851159db58bbf01e2c72a538ac654397caec7b7a)

### Events

##### Fix link for 'past events' in case of no events found.

`Bugfix` | [ogc-1281](#ogc-1281) | [cd3f1d4a2a](https://github.com/onegov/onegov-cloud/commit/cd3f1d4a2a10a3bf4f340e60a0c2235a8d823292)

### Feriennet

##### Add URLs for Analytics

`Feature` | [OGC-1155](https://linear.app/onegovcloud/issue/OGC-1155) | [f13521ab60](https://github.com/onegov/onegov-cloud/commit/f13521ab6086f22ec5f4d0fb16de8451b3011787)

### Org

##### Make the PDF part of the ticket file download and fixes errors.

`Feature` | [OGC-1271](https://linear.app/onegovcloud/issue/OGC-1271) | [23389d7630](https://github.com/onegov/onegov-cloud/commit/23389d76308564e46398e17f6173171bfc2b765a)

### Town6

##### Center Slider Images

`Feature` | [c859421a6c](https://github.com/onegov/onegov-cloud/commit/c859421a6cbec3a42dfd032af515162af0692358)

##### New sidebar

The sidebar content now stays in sight even with scrolling. On mobile it is moved into an offCanvas-panel.

`Feature` | [a6f8fb29a9](https://github.com/onegov/onegov-cloud/commit/a6f8fb29a9ca54625e8147eb399e6ec0e707809c)

##### Fix Current Page Highlighting

`Bugfix` | [b9792ace8f](https://github.com/onegov/onegov-cloud/commit/b9792ace8f8789ff7f3ceb51cc55aa572482f29d)

##### Input Button Styling

`Other` | [ORG-682](#ORG-682) | [5b796e54f3](https://github.com/onegov/onegov-cloud/commit/5b796e54f3945e775e135eb3e34733a244ef5d86)

##### Only apply image changes to homepage-image-slider

`Bugfix` | [da9fb6be22](https://github.com/onegov/onegov-cloud/commit/da9fb6be2207c537d46bc8c3d48331a423064d66)

## 2023.49

`2023-09-29` | [095da96732...095da96732](https://github.com/OneGov/onegov-cloud/compare/095da96732^...095da96732)

## 2023.48

`2023-09-29` | [cc4d60fbac...006cfbbb9f](https://github.com/OneGov/onegov-cloud/compare/cc4d60fbac^...006cfbbb9f)

### Events

##### Winterthur anthrazit xml will now support 'rubrik' nested under 'hauptrubrik' as well as 'keyword'

`Feature` | [ogc-1048](#ogc-1048) | [1b59e1d108](https://github.com/onegov/onegov-cloud/commit/1b59e1d10800e1388aef3795ed39806a1c3e5758)

## 2023.47

`2023-09-28` | [07a1f518d9...8c0abf7431](https://github.com/OneGov/onegov-cloud/compare/07a1f518d9^...8c0abf7431)

**Upgrade hints**
- onegov-people --select /onegov_town6/* onegov-migrate-people-address-field
### Core

##### Fixes delta filestorage transfer.

- Also adds verbose output so we can see which files are copied
- ``--include='*/'`` was necessary for recursive directory traversal
- Note that ``--include`` needs to come before ``--exclude``

`Bugfix` | [15b779ba9d](https://github.com/onegov/onegov-cloud/commit/15b779ba9dc022966e73d9e82ff32365716c3623)

### Election

##### Add a maximum screen number limit.

`Bugfix` | [503bb3a1b7](https://github.com/onegov/onegov-cloud/commit/503bb3a1b743825ee0fc1d6dd2653dd91f3ea670)

### Election Day

##### Replaces CVP with Die Mitte in color suggestions.

`Feature` | [2d733ae2c9](https://github.com/onegov/onegov-cloud/commit/2d733ae2c9718f954d168de17bfde043010b4345)

##### Improve naming of tie breaker view.

`Feature` | [OGC-1273](https://linear.app/onegovcloud/issue/OGC-1273) | [f63012b9f2](https://github.com/onegov/onegov-cloud/commit/f63012b9f228a07deaeba17bb854c539f76ec6cf)

##### Add temporary static data for 2024.

`Feature` | [OGC-1280](https://linear.app/onegovcloud/issue/OGC-1280) | [c12ea961fc](https://github.com/onegov/onegov-cloud/commit/c12ea961fcb27c7a6a4349d92e6a8c19e9958925)

##### Fixes error field focus for errors with no inputs.

`Bugfix` | [578170b7de](https://github.com/onegov/onegov-cloud/commit/578170b7de05ab9134e31c166a816487c39bfe33)

##### Don't add expats to entity filters.

`Bugfix` | [a7a9e705f0](https://github.com/onegov/onegov-cloud/commit/a7a9e705f053d7b95f61c360c80ad98be81a48fc)

##### Hide proporz specific options for majorz elections.

`Bugfix` | [46252309ae](https://github.com/onegov/onegov-cloud/commit/46252309aea4b98df6c73ed3cf71c08458d9b7d6)

### Events

##### Preserve filter order (alphabetically by default)

`Feature` | [ogc-1219](#ogc-1219) | [b3ccf8c690](https://github.com/onegov/onegov-cloud/commit/b3ccf8c69073cf230fc23e111376255522fb77c6)

##### Winterthur style adjustments

`Feature` | [ogc-1219](#ogc-1219) | [7ff72d9e25](https://github.com/onegov/onegov-cloud/commit/7ff72d9e259ce7b0395977caf8bddb252196ff31)

##### Validate event filter definition does not use names used in EventForm

`Feature` | [ogc-1219](#ogc-1219) | [2bb596ec26](https://github.com/onegov/onegov-cloud/commit/2bb596ec268ee8ee01aba952ff06a92966442622)

##### Fix how filters are displayed in ticket summary

`Bugfix` | [ogc-1219](#ogc-1219) | [0871e46907](https://github.com/onegov/onegov-cloud/commit/0871e469078bb1f6bb53d130be9a51b01a63a973)

##### Fix how filters are displayed in ticket summary [part 2]

`Bugfix` | [ogc-1219](#ogc-1219) | [561d1954ef](https://github.com/onegov/onegov-cloud/commit/561d1954ef5c15003cee717a40feb7645f663be3)

### Org

##### Download files from ticket.

`Feature` | [OGC-1271](https://linear.app/onegovcloud/issue/OGC-1271) | [537466709a](https://github.com/onegov/onegov-cloud/commit/537466709a5177d05a3c3258f077bd61e324ab25)

##### Fixes regression in `OrgApp.root_pages`

`Bugfix` | [OGC-1276](https://linear.app/onegovcloud/issue/OGC-1276) | [d3215e78e4](https://github.com/onegov/onegov-cloud/commit/d3215e78e4811217b56229bddc913ddb6a54e90b)

### People

##### Replaces the address field for people for org and town6

`Feature` | [ogc-1243](#ogc-1243) | [b28680bbff](https://github.com/onegov/onegov-cloud/commit/b28680bbff4fa1d43042cbb6f61fd988b1dd68b0)

### Swissvotes

##### Add missing script-src.

`Bugfix` | [092a24511b](https://github.com/onegov/onegov-cloud/commit/092a24511bae07af75931016cedf7a841f70e58f)

### Town6

##### Mark current navigation element

`Feature` | [OGC-1259](https://linear.app/onegovcloud/issue/OGC-1259) | [7177ef2b76](https://github.com/onegov/onegov-cloud/commit/7177ef2b769ccceab3343bc0a6906addfaf3aeb8)

##### Video height fullscreen by default

`Feature` | [OGC-1202](https://linear.app/onegovcloud/issue/OGC-1202) | [881c2dcedf](https://github.com/onegov/onegov-cloud/commit/881c2dcedf0b987f445ffaa2a119e478c13a4c56)

##### Small fix for person directory.

`Bugfix` | [OGC-1257](https://linear.app/onegovcloud/issue/OGC-1257) | [07a1f518d9](https://github.com/onegov/onegov-cloud/commit/07a1f518d9e19d6f042de6c3ed6f4788321f04b8)

## 2023.46

`2023-09-22` | [db9db375c6...f47ebd23ee](https://github.com/OneGov/onegov-cloud/compare/db9db375c6^...f47ebd23ee)

### Core

##### Speed up file transfer.

`Feature` | [OGC-1267](https://linear.app/onegovcloud/issue/OGC-1267) | [b5ffff15b5](https://github.com/onegov/onegov-cloud/commit/b5ffff15b5daa3dffe38908aab36c182e03b0e55)

### Events

##### Makes inline search work with event json data

`Bugfix` | [ogc-1219](#ogc-1219) | [9528480cbb](https://github.com/onegov/onegov-cloud/commit/9528480cbb3c654cd06ce57efa64e532bad9eb07)

##### Winterthur fix anthrazit export - missing 'rubrik' elements in case of filter

`Bugfix` | [ogc-1048](#ogc-1048) | [43a2e8f579](https://github.com/onegov/onegov-cloud/commit/43a2e8f579b895c55a52ef12be78df3697ea6e13)

##### Filter keywords are not pupulated when editing event

`Bugfix` | [ogc-1219](#ogc-1219) | [3488df52f6](https://github.com/onegov/onegov-cloud/commit/3488df52f6801b0d49bfd7ff4d2e9881d7502365)

##### Prevent to show filter keywords if value is not set

`Bugfix` | [ogc-1219](#ogc-1219) | [cca9a365d9](https://github.com/onegov/onegov-cloud/commit/cca9a365d9c84879ea8621819dd276a3db1999c2)

##### Every filter element goes into its own field to prevent layout issues in case when many filter elements are selected

`Bugfix` | [ogc-1219](#ogc-1219) | [956abfe01c](https://github.com/onegov/onegov-cloud/commit/956abfe01c628709711d4bb183057cffd60b3417)

### Landsgemeinde

##### Add suggestions to votum form.

`Feature` | [OGC-1244](https://linear.app/onegovcloud/issue/OGC-1244) | [7d50a65042](https://github.com/onegov/onegov-cloud/commit/7d50a65042a5677fab042263f41526d6001260e1)

### Org

##### Adds linked files to topics/news that are displayed in the sidebar

`Feature` | [OGC-1203](https://linear.app/onegovcloud/issue/OGC-1203) | [9217accb97](https://github.com/onegov/onegov-cloud/commit/9217accb977f30ce402f3cb33e964bc9dde6228e)

### Town6

##### Sort by pages in person card.

`Bugfix` | [OGC-1257](https://linear.app/onegovcloud/issue/OGC-1257) | [354203cb42](https://github.com/onegov/onegov-cloud/commit/354203cb4284c33f4c2b4475a5701ef1e83c7564)

### Winterthur

##### DWS Event import set default fitler keywords instead of default categories

`Feature` | [ogc-1225](#ogc-1225) | [ac6f81533d](https://github.com/onegov/onegov-cloud/commit/ac6f81533d6400967e357069af6ce61c95b31ce0)

## 2023.45

`2023-09-17` | [bdc3f8199a...ecfe2c1868](https://github.com/OneGov/onegov-cloud/compare/bdc3f8199a^...ecfe2c1868)

### Core

##### Tighten CSP.

`Feature` | [OGC-1156](https://linear.app/onegovcloud/issue/OGC-1156) | [ddd93a96c4](https://github.com/onegov/onegov-cloud/commit/ddd93a96c4db85333c8b737d08fb0228099b0387)

### Landsgemeinde

##### Redesign and improvements.

`Feature` | [OGC-638](https://linear.app/onegovcloud/issue/OGC-638) | [0b55e2df61](https://github.com/onegov/onegov-cloud/commit/0b55e2df61ace6de047a513bdb900a816eb43718)

### Multiple

##### Add URL validators to URLFields.

`Bugfix` | [OGC-1130](https://linear.app/onegovcloud/issue/OGC-1130) | [e869c97c09](https://github.com/onegov/onegov-cloud/commit/e869c97c095b25734c160296870b1f6b3d13e364)

##### Update jQuery.

`Bugfix` | [OGC-1130](https://linear.app/onegovcloud/issue/OGC-1130) | [db639425d2](https://github.com/onegov/onegov-cloud/commit/db639425d2dbdf5e3c553ef13be52facfd3b1bd9)

### Org

##### Lax CSP.

`Bugfix` | [OGC-1156](https://linear.app/onegovcloud/issue/OGC-1156) | [fe41d22058](https://github.com/onegov/onegov-cloud/commit/fe41d220587932dee3cb263e63e57d80dba2c9fa)

### Swissvotes

##### Update translations.

`Feature` | [bdc3f8199a](https://github.com/onegov/onegov-cloud/commit/bdc3f8199a5e704df6650821033022c8327e7209)

##### Include mastodon assets only when used.

`Bugfix` | [d83aa8daed](https://github.com/onegov/onegov-cloud/commit/d83aa8daed1db7095156a03ac801a66da1ec0472)

## 2023.44

`2023-09-15` | [aa4f78c218...ba8bc7d4ec](https://github.com/OneGov/onegov-cloud/compare/aa4f78c218^...ba8bc7d4ec)

**Upgrade hints**
- onegov-core --select /onegov_org/* upgrade or `onegov-core upgrade
### Api

##### Type annotations for api module. (#957)

Co-authored-by: David Salvisberg <david.salvisberg@seantis.ch>

`Other` | [f80729f9db](https://github.com/onegov/onegov-cloud/commit/f80729f9db3feaf38455a10dd9a2e43c337ee93c)

### Events

##### Configurable event filters (analog to directories)

`Feature` | [ogc-1219](#ogc-1219) | [9af704438c](https://github.com/onegov/onegov-cloud/commit/9af704438ccae09b3a416704b4fcc02d99c19d23)

##### Fix tag counting in case of extra date

`Bugfix` | [ogc-1248](#ogc-1248) | [49174bbdaf](https://github.com/onegov/onegov-cloud/commit/49174bbdaf83c6e5dd8ca73da634ef84ab0e6d50)

### Landsgemeinde

##### Show scheduled vota only for logged in users.

`Feature` | [OGC-1239](https://linear.app/onegovcloud/issue/OGC-1239) | [aa4f78c218](https://github.com/onegov/onegov-cloud/commit/aa4f78c2189e2b91806a37d1ff648c8afc9b8126)

##### Add last modified to agenda items.

`Feature` | [OGC-1239](https://linear.app/onegovcloud/issue/OGC-1239) | [115b63960e](https://github.com/onegov/onegov-cloud/commit/115b63960e2ce4128d1aa5e8124224c7b3211431)

##### Adds suggestion models.

`Feature` | [OGC-1244](https://linear.app/onegovcloud/issue/OGC-1244) | [81a2f22e38](https://github.com/onegov/onegov-cloud/commit/81a2f22e385f5721433fc731e4020a66e4ed0c5d)

##### Fixes rendering of timestamp.

`Bugfix` | [09d130863a](https://github.com/onegov/onegov-cloud/commit/09d130863afb5f2ad6fd22c41999d946e917c99d)

### Org

##### Optimizes page navigation by avoiding recursive database queries

`Bugfix` | [OGC-1228](https://linear.app/onegovcloud/issue/OGC-1228) | [e15e323a47](https://github.com/onegov/onegov-cloud/commit/e15e323a4718994dbd68f3a9801393c1db8c8294)

### Swissvotes

##### Update translations.

`Feature` | [68f519e067](https://github.com/onegov/onegov-cloud/commit/68f519e067094f65b80a2608229862945c75636f)

##### Enable French attachments for parliamentary initatives.

`Feature` | [df77d244b0](https://github.com/onegov/onegov-cloud/commit/df77d244b0cf7dfde975bb379d7831772b40723b)

### Town6

##### Always show function in person card.

`Feature` | [OGC-1242](https://linear.app/onegovcloud/issue/OGC-1242) | [6b1a3d140a](https://github.com/onegov/onegov-cloud/commit/6b1a3d140ab25a94950dce5380f11d7e3faff2e6)

##### Header changes

`Feature` | [6e15e6cff4](https://github.com/onegov/onegov-cloud/commit/6e15e6cff42b336bd8dd3c495f7fe6befa7c93f2)

##### Adds job widget based on RSS feed.

`Feature` | [OGC-1255](https://linear.app/onegovcloud/issue/OGC-1255) | [fdbb1c7ffe](https://github.com/onegov/onegov-cloud/commit/fdbb1c7ffe4bba07b93849b1d0b42d0503b88412)

##### Fix overlapping elements.

`Bugfix` | [OGC-1252](https://linear.app/onegovcloud/issue/OGC-1252) | [e941180f0d](https://github.com/onegov/onegov-cloud/commit/e941180f0db33ea0f0f5de67c8bba6c968616a3f)

## 2023.43

`2023-09-04` | [bbca2e85e1...ad057529c1](https://github.com/OneGov/onegov-cloud/compare/bbca2e85e1^...ad057529c1)

### Landsgemeinde

##### Remove start time from agenda items and vota.

`Feature` | [OGC-638](https://linear.app/onegovcloud/issue/OGC-638) | [b1ff00ae9c](https://github.com/onegov/onegov-cloud/commit/b1ff00ae9c79b7008506db4148a290d7ed3e25a5)

##### Update archive title.

`Feature` | [OGC-1239](https://linear.app/onegovcloud/issue/OGC-1239) | [ccab5dce85](https://github.com/onegov/onegov-cloud/commit/ccab5dce85f5b0e035a2a64416816e55f3045948)

### Landsgmeinde

##### Improve tracking of ticker changes and add a hint for completed assemblies.

`Feature` | [OGC-1238](https://linear.app/onegovcloud/issue/OGC-1238) | [4c878bf697](https://github.com/onegov/onegov-cloud/commit/4c878bf697f5f8eb7c70633e44270a0b9ff2cdf5)

### Swissvotes

##### Update translations.

`Feature` | [SWI](#SWI) | [ce76cd136b](https://github.com/onegov/onegov-cloud/commit/ce76cd136bb67eb795cb5bfc076252a773a24f8c)

## 2023.42

`2023-09-01` | [d9cfe17091...c52430d8d5](https://github.com/OneGov/onegov-cloud/compare/d9cfe17091^...c52430d8d5)

### Election Day

##### Refactor import and export formats.

`Feature` | [d9cfe17091](https://github.com/onegov/onegov-cloud/commit/d9cfe17091399e6c88a0563d1c30efde1caa7106)

### Org

##### Increase robustness of functions that depend on submission.

This prevents possible `AttributeError` if `self.submission` is None

`Bugfix` | [OGC-1236](https://linear.app/onegovcloud/issue/OGC-1236) | [4866a931a8](https://github.com/onegov/onegov-cloud/commit/4866a931a85e2715d7774ecffeee708077469351)

### Swissvotes

##### Update translations.

`Feature` | [SWI-35](https://linear.app/swissvotes/issue/SWI-35) | [5caa8c7ac3](https://github.com/onegov/onegov-cloud/commit/5caa8c7ac3546422087a839345339c4c7450d84a)

##### Add hints to parliamentary initative attachments.

`Feature` | [SWI-32](https://linear.app/swissvotes/issue/SWI-32) | [dbc78829e1](https://github.com/onegov/onegov-cloud/commit/dbc78829e136c3bd9488a611453b91c925dc7417)

##### Restyle mastodon timeline.

`Feature` | [SWI-37](https://linear.app/swissvotes/issue/SWI-37) | [fb780c2120](https://github.com/onegov/onegov-cloud/commit/fb780c21206c179e35d20aebe0fc64cc60816bb9)

### Town6

##### Translations and pre-commit hook so this won't happen again.

`Bugfix` | [OGC-1237](https://linear.app/onegovcloud/issue/OGC-1237) | [ed0f12ed53](https://github.com/onegov/onegov-cloud/commit/ed0f12ed531872b1d1af80a3764d820ecaee6cfe)

### Winterthur

##### Inline search lower search text

`Bugfix` | [ogc-1201](#ogc-1201) | [85c6ff67aa](https://github.com/onegov/onegov-cloud/commit/85c6ff67aa1d578df800d331d6ed2f623cedbad0)

## 2023.41

`2023-08-29` | [bd6cdfa7bf...bd6cdfa7bf](https://github.com/OneGov/onegov-cloud/compare/bd6cdfa7bf^...bd6cdfa7bf)

## 2023.40

`2023-08-29` | [bdbad28762...5d1b492881](https://github.com/OneGov/onegov-cloud/compare/bdbad28762^...5d1b492881)

### Landsgemeinde

##### More adjustments

`Feature` | [8feeabf916](https://github.com/onegov/onegov-cloud/commit/8feeabf9166987ddab0f21c4e0e9c41a05209398)

## 2023.39

`2023-08-29` | [3df972f740...30d9caebb6](https://github.com/OneGov/onegov-cloud/compare/3df972f740^...30d9caebb6)

### Core

##### Fixes `request.application_url`/`request.path_url`

Also fixes incorrect url in sentry events

`Bugfix` | [8b0cc00129](https://github.com/onegov/onegov-cloud/commit/8b0cc00129d1d79333d36a584e86eb6a8bd9a8d1)

### Events

##### Organizer phone number not always shown and translated

`Bugfix` | [ogc-1222](#ogc-1222) | [879cab78f0](https://github.com/onegov/onegov-cloud/commit/879cab78f0331ab79f14a4f2e1c00519159811b8)

### Landsgemeinde

##### Styling and Sidebar

`Feature` | [OGC-1116](https://linear.app/onegovcloud/issue/OGC-1116) | [2e6ea7db51](https://github.com/onegov/onegov-cloud/commit/2e6ea7db512234d4776a1146311def3b9531be52)

### Org

##### Make linkify parser more robust.

`Bugfix` | [OGC-1233](https://linear.app/onegovcloud/issue/OGC-1233) | [5063677158](https://github.com/onegov/onegov-cloud/commit/506367715872eed269153a4717ca4adcc1a7750e)

### Swissvotes

##### Style mastodon timeline.

`Bugfix` | [SWI-37](https://linear.app/swissvotes/issue/SWI-37) | [b95a54050c](https://github.com/onegov/onegov-cloud/commit/b95a54050c521e06dfe1d3905d4d7253512df3d8)

## 2023.38

`2023-08-22` | [7ae984d376...1a47ed40da](https://github.com/OneGov/onegov-cloud/compare/7ae984d376^...1a47ed40da)

### Core

##### Add compatibility with mistletoe 1.2.

`Bugfix` | [e61fb068a7](https://github.com/onegov/onegov-cloud/commit/e61fb068a7093be3e5048a86b387ea9227c676a8)

### Events

##### Winterthur adding xml view for anthrazit format

`Feature` | [ogc-1048](#ogc-1048) | [7ae984d376](https://github.com/onegov/onegov-cloud/commit/7ae984d37638afcccf0b53d4badd3aad37c128a6)

### Swissvotes

##### Change collection duration info.

`Feature` | [SWI-38](https://linear.app/swissvotes/issue/SWI-38) | [4826eccffe](https://github.com/onegov/onegov-cloud/commit/4826eccffe2d6c633877a7f21a10a4684a5fb571)

##### Add English short title.

`Feature` | [SWI-38](https://linear.app/swissvotes/issue/SWI-38) | [a487782052](https://github.com/onegov/onegov-cloud/commit/a4877820523f872e726d9c2dc745796a3b4b88dd)

##### Add parliamentary initiatives.

`Feature` | [SWI-32](https://linear.app/swissvotes/issue/SWI-32) | [52c3314581](https://github.com/onegov/onegov-cloud/commit/52c33145813b0c8f7277b0ff785dfe329cadee2e)

##### Add mastodon timeline.

`Feature` | [SWI-37](https://linear.app/swissvotes/issue/SWI-37) | [4dea33f44e](https://github.com/onegov/onegov-cloud/commit/4dea33f44ecde483555adcea06186daf56d3c560)

##### Add a voting result line to general.

`Feature` | [SWI-35](https://linear.app/swissvotes/issue/SWI-35) | [aa40de9fb7](https://github.com/onegov/onegov-cloud/commit/aa40de9fb7476e7552b0f617faf03ea391abb10b)

## 2023.37

`2023-08-21` | [161ee64bb5...cce9f9d188](https://github.com/OneGov/onegov-cloud/compare/161ee64bb5^...cce9f9d188)

### Core

##### Fixes authentication in LDAPKerberosProvider (#941)

`Bugfix` | [OGC-1209](https://linear.app/onegovcloud/issue/OGC-1209) | [a7db20dea7](https://github.com/onegov/onegov-cloud/commit/a7db20dea722844fe4faabc831fbb94b987427b9)

##### Pin validators

`Bugfix` | [OGC-1224](https://linear.app/onegovcloud/issue/OGC-1224) | [fe6cdd2af0](https://github.com/onegov/onegov-cloud/commit/fe6cdd2af0fa68cc9f55f8ac25dcbbbf1c0fb7af)

### Event

##### Adds optional field for organizer's phone number

`Feature` | [ogc-1222](#ogc-1222) | [e2162f780a](https://github.com/onegov/onegov-cloud/commit/e2162f780a8a1a3476d3f867c1a1cf36400ee01a)

##### Show number of occurrences per tag

`Feature` | [ogc-1220](#ogc-1220) | [ea6d77a2a1](https://github.com/onegov/onegov-cloud/commit/ea6d77a2a1bc416dba1aaeba26d09620ceed5257)

##### Allow to set default event category when importing from ical if non is given

For Winterthur importing the DWS calendar from ical. Usually no categories are set so we can set a default if non is given for daily imports.

`Feature` | [ogc-1225](#ogc-1225) | [fec26f2ebd](https://github.com/onegov/onegov-cloud/commit/fec26f2ebd8f68f4baaaabd0243f4ff5e3192b74)

### Form

##### Gets rid of `colour` dependency

Instead uses actively maintained `webcolors` to validate `ColorField`

`Feature` | [OGC-1229](https://linear.app/onegovcloud/issue/OGC-1229) | [a291a9b82f](https://github.com/onegov/onegov-cloud/commit/a291a9b82f22cfb6b30e9e889471e8114db6d181)

##### Remove wtforms-components dependency

`Bugfix` | [OGC-1226](https://linear.app/onegovcloud/issue/OGC-1226) | [b813409480](https://github.com/onegov/onegov-cloud/commit/b813409480e69efa38b388b3f95ee6d059d9c57d)

### Swissvotes

##### Move position of the federal council to voting campaign.

`Feature` | [SWI-40](https://linear.app/swissvotes/issue/SWI-40) | [278800c9fe](https://github.com/onegov/onegov-cloud/commit/278800c9feff00ff98e4dc3fb46e5422c57549e4)

##### Add English translations of actors and update some other translations.

`Feature` | [SWI-41](https://linear.app/swissvotes/issue/SWI-41) | [abf1307af1](https://github.com/onegov/onegov-cloud/commit/abf1307af14b333eeab1810e1ab94bcbed28e39c)

##### Add easyvote video links.

`Feature` | [SWI-34](https://linear.app/swissvotes/issue/SWI-34) | [2f515e2034](https://github.com/onegov/onegov-cloud/commit/2f515e2034e4e82ba974848bfaa5c1e8e9dd6122)

##### Add easyvote booklet.

`Feature` | [SWI-34](https://linear.app/swissvotes/issue/SWI-34) | [ded8fa6a5f](https://github.com/onegov/onegov-cloud/commit/ded8fa6a5fc65f88fb24782a003de51172c498dc)

##### Add doctype website.

`Feature` | [SWI-39](https://linear.app/swissvotes/issue/SWI-39) | [f48cad690c](https://github.com/onegov/onegov-cloud/commit/f48cad690c0848cadd76297e6900dd23cf0ee279)

##### Enable french brief descriptions and result files.

`Feature` | [SWI-33](https://linear.app/swissvotes/issue/SWI-33) | [73eb4611f9](https://github.com/onegov/onegov-cloud/commit/73eb4611f9ecb1463b81a5107025e23a265411e3)

##### Fixes national council share indicator.

`Bugfix` | [SWI-36](https://linear.app/swissvotes/issue/SWI-36) | [2fb9d9b44e](https://github.com/onegov/onegov-cloud/commit/2fb9d9b44e430be118fdfb8040e8ecd075d2b9e7)

### Town6

##### Adds misssing wrapper for view that is used by org.

`Bugfix` | [2985f67ff8](https://github.com/onegov/onegov-cloud/commit/2985f67ff8bffdc364b3e271b9f51e8b42b6e940)

### Winterthur

##### Adds inline text search for events

`Feature` | [ogc-1201](#ogc-1201) | [3b5f385b72](https://github.com/onegov/onegov-cloud/commit/3b5f385b7236b6d2633c1a023f15ff014d96047c)

##### Daycare calculation correction

`Bugfix` | [OGC-1207](https://linear.app/onegovcloud/issue/OGC-1207) | [493691e9fd](https://github.com/onegov/onegov-cloud/commit/493691e9fd3dace9365e18162ba6afc90c2894dc)

## 2023.36

`2023-08-04` | [c1bddcd2d7...8e1eb9630c](https://github.com/OneGov/onegov-cloud/compare/c1bddcd2d7^...8e1eb9630c)

### Api

##### Authentication to bypass rate limits.

`Feature` | [OGC-1102](https://linear.app/onegovcloud/issue/OGC-1102) | [88823ad8c3](https://github.com/onegov/onegov-cloud/commit/88823ad8c3ee90532ad6bc9e306df3ff4621e4ba)

### Core

##### Makes `dict_property` behave like a `hybrid_property`

`Feature` | [6869e8d8ff](https://github.com/onegov/onegov-cloud/commit/6869e8d8ffebfa22afb7eb11f10ead75ed6988ea)

##### Fixes error in FileDataManager

`Bugfix` | [c1bddcd2d7](https://github.com/onegov/onegov-cloud/commit/c1bddcd2d7f0bf8aab42779a2ba54a9ff3fe94da)

### Event

##### Event price is now multi line capable

`Bugfix` | [ogc-1217](#ogc-1217) | [8d2ea574d0](https://github.com/onegov/onegov-cloud/commit/8d2ea574d024334c96d88c9cd6407653f4501daf)

### File

##### Makes image uploads slightly more robust against corrupt files

`Bugfix` | [e60f9c5e68](https://github.com/onegov/onegov-cloud/commit/e60f9c5e682b7d1b96651dbf88bd400816b76fd0)

### Form

##### Notify if registration can not be confirmed because the maximum number of participants has been reached

`Bugfix` | [ogc-1211](#ogc-1211) | [0db6f1cf9a](https://github.com/onegov/onegov-cloud/commit/0db6f1cf9a4363a738c9d0a473f1914cb3b774ba)

### Org

##### Send mail for internal notes on reservations.

`Feature` | [OGC-1068](https://linear.app/onegovcloud/issue/OGC-1068) | [527a9a531c](https://github.com/onegov/onegov-cloud/commit/527a9a531cf0e644882b44f0c520ec2ec58b4675)

##### Send mail for rejected reservations.

`Feature` | [OGC-946](https://linear.app/onegovcloud/issue/OGC-946) | [e07158b8f1](https://github.com/onegov/onegov-cloud/commit/e07158b8f1e593b76cfe91c5eadab23943cc2ea7)

##### Fixes validator on publication form extension

`Bugfix` | [bb3310c410](https://github.com/onegov/onegov-cloud/commit/bb3310c410ba38eaa0be3cde917e8ac870a81b87)

##### Fix linking in contact side panel.

`Bugfix` | [OGC-1215](https://linear.app/onegovcloud/issue/OGC-1215) | [8f6f8f94f7](https://github.com/onegov/onegov-cloud/commit/8f6f8f94f7cd9b56a3caf76a55a1a7c51f63e5fa)

### Town6

##### Add option to optionally hide context-specific functions.

`Feature` | [OGC-1129](https://linear.app/onegovcloud/issue/OGC-1129) | [29d00157c7](https://github.com/onegov/onegov-cloud/commit/29d00157c7aac0b673ab8f1e2da11d67a9e220e6)

## 2023.35

`2023-07-21` | [25d7d0e843...1c0a54e230](https://github.com/OneGov/onegov-cloud/compare/25d7d0e843^...1c0a54e230)

### Feriennet

##### Pre-fill `attendee_id` on `InvoiceItem` based on `group`

`Bugfix` | [PRO-1092](https://linear.app/projuventute/issue/PRO-1092) | [5ded180aed](https://github.com/onegov/onegov-cloud/commit/5ded180aedad3992faeea01b987c0ef238d9566f)

### File

##### Optimizes thumbnail generation and potentially fixes issue

`Bugfix` | [OGC-1190](https://linear.app/onegovcloud/issue/OGC-1190) | [b92b1a676f](https://github.com/onegov/onegov-cloud/commit/b92b1a676f30bd5ebdcecbd0a1f8b5a490900b62)

## 2023.34

`2023-07-18` | [a15b7df028...729bf01546](https://github.com/OneGov/onegov-cloud/compare/a15b7df028^...729bf01546)

### Feriennet

##### Fix upgrade step

`Bugfix` | [eeb027e135](https://github.com/onegov/onegov-cloud/commit/eeb027e135809c0b342a84c114f02ee72d880bc8)

## 2023.33

`2023-07-18` | [05cfebe0e2...d6e27abb40](https://github.com/OneGov/onegov-cloud/compare/05cfebe0e2^...d6e27abb40)

### Feriennet

##### Fix invoice item bug on attendee name change

Check for attendee id instead of name in the invoice items after a new booking. Also rename the invoice item group in the current period if the attendee name changes.

`Bugfix` | [PRO-1092](https://linear.app/projuventute/issue/PRO-1092) | [79ac2bf63f](https://github.com/onegov/onegov-cloud/commit/79ac2bf63fcbb1c1b7d3d69e596b393f89869d31)

## 2023.32

`2023-07-11` | [fa001f406a...d6a24a0433](https://github.com/OneGov/onegov-cloud/compare/fa001f406a^...d6a24a0433)

### Feriennet

##### Replace Banners

`Feature` | [PRO-1224](https://linear.app/projuventute/issue/PRO-1224) | [fa001f406a](https://github.com/onegov/onegov-cloud/commit/fa001f406aa4d3a1b8446f9796c52e8191bafe38)

##### Bugfix invoice item export

`Bugfix` | [PRO-1201](https://linear.app/projuventute/issue/PRO-1201) | [63b78a0756](https://github.com/onegov/onegov-cloud/commit/63b78a0756282ddcc67d4c58e0f86560e036ccac)

### File

##### Strips EXIF data from uploaded images

Improves robustness of image processing in `ProcessedUploadedFile`

`Feature` | [OGC-1190](https://linear.app/onegovcloud/issue/OGC-1190) | [355c39e74a](https://github.com/onegov/onegov-cloud/commit/355c39e74aeecfd36df17e9749b40c8a11974aa8)

## 2023.31

`2023-07-10` | [7faae3b590...7faae3b590](https://github.com/OneGov/onegov-cloud/compare/7faae3b590^...7faae3b590)

## 2023.30

`2023-07-10` | [21ac88f973...ead6346d0e](https://github.com/OneGov/onegov-cloud/compare/21ac88f973^...ead6346d0e)

### Core

##### Adds a proper Sentry Integration

Starts using `SentryWsgiMiddleware`, since this performs
all the necessary book keeping for traces and profiles

`Feature` | [OGC-1178](https://linear.app/onegovcloud/issue/OGC-1178) | [bf06050587](https://github.com/onegov/onegov-cloud/commit/bf060505870b25cbd6e9c7d2c767d144b32d3a8c)

### Election Day

##### Fixes deleting archived results from alternative sites.

`Bugfix` | [OGC-1186](https://linear.app/onegovcloud/issue/OGC-1186) | [21ac88f973](https://github.com/onegov/onegov-cloud/commit/21ac88f97399f6632167e51a1e4b7644da1519d9)

### Feriennet

##### Fix Invoice Item Export

`Bugfix` | [PRO-1201](https://linear.app/projuventute/issue/PRO-1201) | [78d50f5027](https://github.com/onegov/onegov-cloud/commit/78d50f50278fb7273eec910f9e165286c6468964)

##### Prevent crash in case of invalid period id

`Bugfix` | [PRO-1206](https://linear.app/projuventute/issue/PRO-1206) | [933eb26434](https://github.com/onegov/onegov-cloud/commit/933eb264341d2837a0afcfabba6fab3707da3355)

### Fsi

##### Hide login text on FSI page

`Bugfix` | [b003a1c3ed](https://github.com/onegov/onegov-cloud/commit/b003a1c3ed6b2f5bd782aac6bb6b86261e5b3938)

### Org

##### Replace onegov footer links with admin.digital

`Feature` | [ee6b956371](https://github.com/onegov/onegov-cloud/commit/ee6b9563713a324c9e6362afe786088c20d3f7e3)

##### Fix side panel

`Bugfix` | [9342f64527](https://github.com/onegov/onegov-cloud/commit/9342f645274ee4a28733e42ddd278c82919eb7c7)

##### Make import more robust if the zip contains a directory.

`Bugfix` | [OGC-1142](https://linear.app/onegovcloud/issue/OGC-1142) | [9b279f532d](https://github.com/onegov/onegov-cloud/commit/9b279f532d650e1703b411b48ecfdbf60bc44999)

## 2023.29

`2023-06-29` | [509e80e963...c4febf3e82](https://github.com/OneGov/onegov-cloud/compare/509e80e963^...c4febf3e82)

### Core

##### Remove filestorage recursively when deleting an instance.

`Bugfix` | [0fb1381c32](https://github.com/onegov/onegov-cloud/commit/0fb1381c325648f066df14630f4758fd87d7bd24)

### Election Day

##### Add experimental eCH-0252 import for votes.

`Feature` | [OGC-1152](https://linear.app/onegovcloud/issue/OGC-1152) | [c4292828b8](https://github.com/onegov/onegov-cloud/commit/c4292828b80b0a950be98f3fabd6c2e8480b1dcb)

##### Add support for intermediate eCH-0252 results.

`Feature` | [OGC-1152](https://linear.app/onegovcloud/issue/OGC-1152) | [0e761ae784](https://github.com/onegov/onegov-cloud/commit/0e761ae784c85f6eea542b589f8fb64dd37ab90e)

##### Allows instances to be served by multiple sites/hosts.

`Feature` | [OGC-1186](https://linear.app/onegovcloud/issue/OGC-1186) | [48fae4c34a](https://github.com/onegov/onegov-cloud/commit/48fae4c34ac06c023951b45012adcf0c277aeb92)

##### Allows to specify an official host to be used for the archived results when being served by multiple sites.

`Feature` | [OGC-1186](https://linear.app/onegovcloud/issue/OGC-1186) | [27882bc78c](https://github.com/onegov/onegov-cloud/commit/27882bc78c7d0a217533df01efef92a0d75a44a6)

##### Remove cache busting by cache control header.

`Other` | [OGC-1167](https://linear.app/onegovcloud/issue/OGC-1167) | [f9e0d27888](https://github.com/onegov/onegov-cloud/commit/f9e0d2788843584ebaffe7ae7bc7b9d4a40fcc89)

##### Add host to pages cache keys.

`Feture` | [OGC-1186](https://linear.app/onegovcloud/issue/OGC-1186) | [bfb05a2ef3](https://github.com/onegov/onegov-cloud/commit/bfb05a2ef3fcf376f0475d5a7df656946f761be6)

### Landsgemeinde

##### Add cache for ticker.

`Feature` | [509e80e963](https://github.com/onegov/onegov-cloud/commit/509e80e963cd9167b34ed2883015755cfed4505f)

##### Add video timestamps.

`Feature` | [8badd5e907](https://github.com/onegov/onegov-cloud/commit/8badd5e907e4c915e3a5a0787f52d4906d4a7738)

##### Add link to ticker.

`Feature` | [93781524e2](https://github.com/onegov/onegov-cloud/commit/93781524e25d4b20d1b99659a17cc240580d3c0a)

##### Improve ticker code.

Adds fallback to ticker in case of websocket server shutdown and add 
timestamp to HEAD request to avoid being browser-cached.

`Bugfix` | [093fdf43af](https://github.com/onegov/onegov-cloud/commit/093fdf43af92fb4ecc2de84f815db5a48a08f13a)

### Org

##### Adds infomaniak to child src content policy.

`Feature` | [c851291070](https://github.com/onegov/onegov-cloud/commit/c851291070425b6b4452fe74fe593590ff1a6cc4)

## 2023.28

`2023-06-23` | [f880391f0d...179dd8f9c5](https://github.com/OneGov/onegov-cloud/compare/f880391f0d^...179dd8f9c5)

### Election Day

##### Enable communal votes for cantons.

`Feature` | [OGC-1148](https://linear.app/onegovcloud/issue/OGC-1148) | [8b2a81fdd7](https://github.com/onegov/onegov-cloud/commit/8b2a81fdd743862731cb779230142d3325f7e302)

##### Add external IDs to ballots.

`Feature` | [OGC-1155](https://linear.app/onegovcloud/issue/OGC-1155) | [0ce42d2915](https://github.com/onegov/onegov-cloud/commit/0ce42d291559c35f87eb93aac803220bf044d72e)

##### Add experimental eCH-0252 export for votes.

`Feature` | [OGC-1151](https://linear.app/onegovcloud/issue/OGC-1151) | [790dc24b53](https://github.com/onegov/onegov-cloud/commit/790dc24b53a411d166954c8c9937661cc8fa440e)

##### Cache HEAD requests.

`Feature` | [OGC-1165](https://linear.app/onegovcloud/issue/OGC-1165) | [ad1efa217e](https://github.com/onegov/onegov-cloud/commit/ad1efa217e66813a2c035b9d8a076c19d1d68905)

##### Avoid sending single quotation marks to the d3-renderer.

`Bugfix` | [OGC-1096](https://linear.app/onegovcloud/issue/OGC-1096) | [f880391f0d](https://github.com/onegov/onegov-cloud/commit/f880391f0d86c6edc7d71630352f22079110188b)

### Fsi

##### Hide OGC login form

`Feature` | [ogc-1111](#ogc-1111) | [c94cafdb8a](https://github.com/onegov/onegov-cloud/commit/c94cafdb8ac7ff7fce0077c09e3eed698c8f9835)

### Gazette

##### Fix flaky test

`Bugfix` | [91d7d7fef4](https://github.com/onegov/onegov-cloud/commit/91d7d7fef4ec198740576e8181ab710b2522aae2)

### Org

##### Adds an optional user definable notice when a directory is empty

Empty in this context means no visible entries

`Feature` | [OGC-1005](https://linear.app/onegovcloud/issue/OGC-1005) | [530dbafc70](https://github.com/onegov/onegov-cloud/commit/530dbafc7084bb7a984c8d2322e0c9a17a8892f6)

### Swissvotes

##### Drops obsolete column.

`Bugfix` | [21137ac4cf](https://github.com/onegov/onegov-cloud/commit/21137ac4cf003b23fdc83ab8840c449bba819618)

## 2023.27

`2023-06-14` | [cb66882702...0fd09b9803](https://github.com/OneGov/onegov-cloud/compare/cb66882702^...0fd09b9803)

### Election Day

##### Add official BFS numbers of cantons.

`Feature` | [63d26bdf15](https://github.com/onegov/onegov-cloud/commit/63d26bdf1584e4acb8fbb6eaea8f099d26fd00da)

##### Add external IDs.

External IDs may be used as an alternative to the (internal) ID when uploading using the REST interface.

`Feature` | [OGC-1155](https://linear.app/onegovcloud/issue/OGC-1155) | [a110ebda45](https://github.com/onegov/onegov-cloud/commit/a110ebda4563504dea80c4681bab77d20ff9718b)

##### Show the current election day on the frontpage instead of the latest.

`Bugfix` | [OGC-1147](https://linear.app/onegovcloud/issue/OGC-1147) | [961a8ece7b](https://github.com/onegov/onegov-cloud/commit/961a8ece7b18b24184c1c25888d558e865923c0c)

### Feriennet

##### Add organizer on invoices

`Feature` | [PRO-1183](https://linear.app/projuventute/issue/PRO-1183) | [830fce75de](https://github.com/onegov/onegov-cloud/commit/830fce75de75f060e1e672bba09899a172758499)

##### Show all occasion dates in info-mails

`Bugfix` | [PRO-1183](https://linear.app/projuventute/issue/PRO-1183) | [9c4408990c](https://github.com/onegov/onegov-cloud/commit/9c4408990c5a4cc21a248643b50ccdf916465d12)

### Fsi

##### Add option for reminder mails

`Feature` | [OGC-1037](https://linear.app/onegovcloud/issue/OGC-1037) | [1a131d3905](https://github.com/onegov/onegov-cloud/commit/1a131d3905ece0cb91fb9dff31e03db05152d833)

### Gazette

##### Move preview code to assets and tighten CSP.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [7f32e52f82](https://github.com/onegov/onegov-cloud/commit/7f32e52f823f3ff7a3bb00ce3c7b634c361aee3f)

### Quill

##### Move initalization to assets.

Also removes unused placeholders.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [98196cf031](https://github.com/onegov/onegov-cloud/commit/98196cf031fa1e9f981ada8190d07591279bec4c)

### Swissvotes

##### Tighten CSP.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [d194169fd6](https://github.com/onegov/onegov-cloud/commit/d194169fd66de5bb744b1663ed26a85321d8eb33)

### Tests

##### Resolve selenium deprecations.

`Bugfix` | [OGC-1143](https://linear.app/onegovcloud/issue/OGC-1143) | [cb66882702](https://github.com/onegov/onegov-cloud/commit/cb66882702f5c03f9e77f8cab3be2e8dc644f59b)

### Wtfs

##### Move print code to assets.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [7bb0f6682b](https://github.com/onegov/onegov-cloud/commit/7bb0f6682b9ebe6529442d4f473d56e74addbd5f)

## 2023.26

`2023-06-09` | [a3d68e34f2...a3d68e34f2](https://github.com/OneGov/onegov-cloud/compare/a3d68e34f2^...a3d68e34f2)

## 2023.25

`2023-06-09` | [bd22e80eb6...6ba5a3a188](https://github.com/OneGov/onegov-cloud/compare/bd22e80eb6^...6ba5a3a188)

### Core

##### Unpin reportlab.

`Other` | [OGC-1088](https://linear.app/onegovcloud/issue/OGC-1088) | [fe0ce2cb6d](https://github.com/onegov/onegov-cloud/commit/fe0ce2cb6deea4955ee4340011fe0b9a17c32bee)

### Election Day

##### Use an asset for screens.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [31e3504fd2](https://github.com/onegov/onegov-cloud/commit/31e3504fd2dbd738fcfb3583f8efad1c69dae6b1)

##### Move redirect filter code to common JS asset.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [967f1f1914](https://github.com/onegov/onegov-cloud/commit/967f1f1914de97b576b1e172f405d81f6fa7836d)

##### Tighten CSP.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [e930182df5](https://github.com/onegov/onegov-cloud/commit/e930182df59b02c64b4dc1af7726a9f8f479b440)

### Feriennet

##### Add terms and conditions to footer

`Feature` | [PRO-1190](https://linear.app/projuventute/issue/PRO-1190) | [c38bf05716](https://github.com/onegov/onegov-cloud/commit/c38bf057168e6a08d0621d3d781f9c359a79b8d6)

##### Only send mails if booking start date is in the past or today

`Bugfix` | [PRO-1188](https://linear.app/projuventute/issue/PRO-1188) | [3a71fad3ea](https://github.com/onegov/onegov-cloud/commit/3a71fad3ea79b2352d01f4d20a4f555d83fd4d8f)

##### Text fix

`Bugfix` | [PRO-1181](https://linear.app/projuventute/issue/PRO-1181) | [20ae8952b2](https://github.com/onegov/onegov-cloud/commit/20ae8952b295cd3913e1ba30de0a449bb2ed82c8)

##### Children bugfix

`Bugfix` | [PRO-1159](https://linear.app/projuventute/issue/PRO-1159) | [5e37efc0c3](https://github.com/onegov/onegov-cloud/commit/5e37efc0c31f958cccb69dfde07d4db218b85f7f)

### Gazette

##### Make test less flaky.

`Bugfix` | [eb7304f746](https://github.com/onegov/onegov-cloud/commit/eb7304f74656925e28a0a24c0608aecc141eda87)

### Org

##### Make import/export of newsletter subscribers more robust.

As created in 2b39d886b89d6486eb65423f702fabd34145f3dc

`Bugfix` | [OGC-1085](https://linear.app/onegovcloud/issue/OGC-1085) | [8045a7ecbc](https://github.com/onegov/onegov-cloud/commit/8045a7ecbcd944627c6bb05f02f91887835969c6)

### Sentry

##### Move initialization to asset files.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [df751b5cda](https://github.com/onegov/onegov-cloud/commit/df751b5cda9bfd80af67fb1053dbf37f09051e21)

### Swissvotes

##### Move the stat code to an asset.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [b384cbe51d](https://github.com/onegov/onegov-cloud/commit/b384cbe51d173bdc574221c5f423d9477c5b1062)

### Tablesaw

##### Use assets instead of inline scripts for translations.

Also removes tablesaw and references to it from projects not using it.

`Feature` | [OGC-867](https://linear.app/onegovcloud/issue/OGC-867) | [d4db78b4a7](https://github.com/onegov/onegov-cloud/commit/d4db78b4a779451616cac249bf9abc2ddff911df)

## 2023.24

`2023-05-31` | [6a926c125d...663bbe94ae](https://github.com/OneGov/onegov-cloud/compare/6a926c125d^...663bbe94ae)

### Agency

##### Adds upgrade step to replace `address.person` in export fields

`Bugfix` | [OGC-1139](https://linear.app/onegovcloud/issue/OGC-1139) | [88cae24c4d](https://github.com/onegov/onegov-cloud/commit/88cae24c4d472fe49285d576937e429165c273b5)

### Fsi

##### Change column in audit pdf

`Feature` | [OGC-1036](https://linear.app/onegovcloud/issue/OGC-1036) | [d2414931ff](https://github.com/onegov/onegov-cloud/commit/d2414931ffed7083b039f2ef02086bb973d6352d)

##### Change appearance and position of additional information

`Feature` | [OGC-1138](https://linear.app/onegovcloud/issue/OGC-1138) | [a6ec911d47](https://github.com/onegov/onegov-cloud/commit/a6ec911d47b0a34a1e0ab1ab15eebc7005aa04c2)

### Landsgemeinde

##### Add ticker.

`Feature` | [OGC-638](https://linear.app/onegovcloud/issue/OGC-638) | [6a926c125d](https://github.com/onegov/onegov-cloud/commit/6a926c125d543b9c986491aaa73719d61707a42e)

##### Improve state management.

`Feature` | [OGC-638](https://linear.app/onegovcloud/issue/OGC-638) | [62486e72f3](https://github.com/onegov/onegov-cloud/commit/62486e72f32be6ebd6f78672c830a89684d74973)

##### Add reveal to vota.

`Feature` | [OGC-638](https://linear.app/onegovcloud/issue/OGC-638) | [d7d9f0f3e8](https://github.com/onegov/onegov-cloud/commit/d7d9f0f3e8459ce1e236fe68bdb69ae16a23fc21)

## 2023.23

`2023-05-26` | [29781ded8d...d261febba9](https://github.com/OneGov/onegov-cloud/compare/29781ded8d^...d261febba9)

### Core

##### Remove readline from shell, add commit.

`Bugfix` | [29781ded8d](https://github.com/onegov/onegov-cloud/commit/29781ded8de29b7905f2a5b278f908953adc3232)

### Election Day

##### Adds compatibility with abraxas voting wabstic format.

`Feature` | [3888b6b118](https://github.com/onegov/onegov-cloud/commit/3888b6b118bbb46d90d29ef1e686be968a88e405)

##### Adds further compatibility with abraxas voting wabstic format.

`Feature` | [44fa86617a](https://github.com/onegov/onegov-cloud/commit/44fa86617a19047a5a49620fcb7bf7941c0ab8de)

### Feriennet

##### Translation Fix

`Bugfix` | [PRO-1184](https://linear.app/projuventute/issue/PRO-1184) | [f11a7d8d0c](https://github.com/onegov/onegov-cloud/commit/f11a7d8d0c3ccbc185d65ae8ea9e9b96821e12f9)

### Org

##### Adds import/export for newsletter subscribers.

`Feature` | [OGC-1085](https://linear.app/onegovcloud/issue/OGC-1085) | [2b39d886b8](https://github.com/onegov/onegov-cloud/commit/2b39d886b89d6486eb65423f702fabd34145f3dc)

##### Set the .zip extension for directory export.

`Bugfix` | [OGC-1087](https://linear.app/onegovcloud/issue/OGC-1087) | [c7b7d438bb](https://github.com/onegov/onegov-cloud/commit/c7b7d438bb33e65b47d40ed2859cc31c8ef966d7)

##### Improve presentation of context-specific function.

`Bugfix` | [OGC-1129](https://linear.app/onegovcloud/issue/OGC-1129) | [7c06b111f3](https://github.com/onegov/onegov-cloud/commit/7c06b111f30e73e8ed075bcb151ca7cb8b86b584)

### Pdf

##### Use Source Sans 3 instead of Helvetica.

`Bugfix` | [OGC-1036](https://linear.app/onegovcloud/issue/OGC-1036) | [de98dc0da1](https://github.com/onegov/onegov-cloud/commit/de98dc0da1a3b39689882352f566bbf1df22de8e)

## 2023.22

`2023-05-19` | [29f672dfc6...70148a383f](https://github.com/OneGov/onegov-cloud/compare/29f672dfc6^...70148a383f)

### Feriennet

##### Add political municipality fields to wishlist bookings export

`Feature` | [PRO-1181](https://linear.app/projuventute/issue/PRO-1181) | [c86a3836a7](https://github.com/onegov/onegov-cloud/commit/c86a3836a76ff54448e549d40612965d33d458c8)

### Fsi

##### Add Organisation name to choice field

`Feature` | [OGC-1035](https://linear.app/onegovcloud/issue/OGC-1035) | [29f672dfc6](https://github.com/onegov/onegov-cloud/commit/29f672dfc6e59800909f2520a9fd4237d43d684f)

### Landsgemeinde

##### Add vota.

Also make content searchable, simplify UI and add some basic styling.

`Feature` | [OGC-638](https://linear.app/onegovcloud/issue/OGC-638) | [842e9ef5b3](https://github.com/onegov/onegov-cloud/commit/842e9ef5b3d9f055b41e12b1dbee7d45412056bd)

### Mypy

##### Adds static type checking to CI/pre-commit (#828)

mypy: Enables static type checking

This is a very lax base config and does not add any annotations beyond
the bare minimum to make mypy happy. But this allows us to get started
on adding type annotations to our code and gradually make the config
more strict for the parts of the code that is annotated.

`Other` | [f12698bf96](https://github.com/onegov/onegov-cloud/commit/f12698bf9641e8c9c3753879189d221fb8c12a06)

### Org

##### Fix exception in hidden directory entries for logged out users

This fixes ONEGOV-CLOUD-48W

`Bugfix` | [OGC-1124](https://linear.app/onegovcloud/issue/OGC-1124) | [5cbf551856](https://github.com/onegov/onegov-cloud/commit/5cbf551856cb1d4b62a71216cfb697e256b5d69e)

