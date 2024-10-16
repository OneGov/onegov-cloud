# Changes

## 2024.50

`2024-10-11` | [3f9655c562...eb0d0926ed](https://github.com/OneGov/onegov-cloud/compare/3f9655c562^...eb0d0926ed)

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

