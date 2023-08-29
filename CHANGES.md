# Changes

## 2023.40

`2023-08-29` | [bdbad28762...469592aecc](https://github.com/OneGov/onegov-cloud/compare/bdbad28762^...469592aecc)

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

## 2023.21

`2023-05-12` | [5a75b7c0ec...274e92ba87](https://github.com/OneGov/onegov-cloud/compare/5a75b7c0ec^...274e92ba87)

### Election Day

##### Add conditional widgets for majority types.

`Feature` | [OGC-1097](https://linear.app/onegovcloud/issue/OGC-1097) | [5a75b7c0ec](https://github.com/onegov/onegov-cloud/commit/5a75b7c0ec6beb2d7b7c949783ac373f0b8c639e)

### Feriennet

##### Invoice item dates bug

Fixed bug where the initial selection never got overwritten

`Bugfix` | [PRO-1167](https://linear.app/projuventute/issue/PRO-1167) | [7dbbf98ba3](https://github.com/onegov/onegov-cloud/commit/7dbbf98ba3af8317a3f2b850929f99ec27108544)

##### Fix number of unlucky atteendees on dashboard

`Bugfix` | [PRO-1118](https://linear.app/projuventute/issue/PRO-1118) | [96a8fd4efc](https://github.com/onegov/onegov-cloud/commit/96a8fd4efca780170b8f4558123d4033c616202c)

### Landsgemeinde

##### Add landsgemeinde app.

`Feature` | [OGC-639](https://linear.app/onegovcloud/issue/OGC-639) | [1fde757608](https://github.com/onegov/onegov-cloud/commit/1fde7576084713bdc9c531c7b73bf31f17d17d58)

### Translator Direcory

##### Use distinct adresses in mailto link.

`Bugfix` | [OGC-1015](https://linear.app/onegovcloud/issue/OGC-1015) | [9fab08c131](https://github.com/onegov/onegov-cloud/commit/9fab08c1314fea2b4a021b0212b4d5016783ccc9)

### Winterthur

##### Include events in iframe resizing

`Feature` | [OGC-1047](https://linear.app/onegovcloud/issue/OGC-1047) | [30e3a0ec17](https://github.com/onegov/onegov-cloud/commit/30e3a0ec1772c980e21ec528576bc89b95973546)

## 2023.20

`2023-05-08` | [611c884776...4de63d80f1](https://github.com/OneGov/onegov-cloud/compare/611c884776^...4de63d80f1)

### Core

##### Indicate hash useage.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [9fbe826fae](https://github.com/onegov/onegov-cloud/commit/9fbe826faecf92036adb11f06d2c2fbd72dbf766)

##### Validate URL used in PostThread.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [f35ecef9c3](https://github.com/onegov/onegov-cloud/commit/f35ecef9c3b23f429b0ae67a5d064dfb00b90137)

##### Add requests timeouts.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [bdbd70c2de](https://github.com/onegov/onegov-cloud/commit/bdbd70c2de5391526b5edf1169d43963c438fbd8)

##### Log execeptions instead of silenty ignoring them.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [36f512b925](https://github.com/onegov/onegov-cloud/commit/36f512b92538d92f4aeb69c80c216acc63f5f8e8)

##### Use either secrets for random or indicate non-cryptographic usage.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [cafe3f3f03](https://github.com/onegov/onegov-cloud/commit/cafe3f3f03d4e12d1d56363592e2910fa4c136db)

##### Indicate safe hardcoded password values.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [c4fea59798](https://github.com/onegov/onegov-cloud/commit/c4fea5979891877c983ecadf83ca407e2fa4f10f)

##### Harden SQL code.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [919d41a0a9](https://github.com/onegov/onegov-cloud/commit/919d41a0a9f7e4aa7071222b89c7c8d67fc4d493)

##### Enable bandit.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [0fa7509577](https://github.com/onegov/onegov-cloud/commit/0fa750957734b94bbaee0c204d603a915649e1b1)

##### Pin reportlab.

`Other` | [OGC-1088](https://linear.app/onegovcloud/issue/OGC-1088) | [1e1996752e](https://github.com/onegov/onegov-cloud/commit/1e1996752e3d3a6a32d80699f0dc9ebfbcf38b85)

### Feriennet

##### Edit email text

`Feature` | [PRO-1126](https://linear.app/projuventute/issue/PRO-1126) | [34a97c1c2c](https://github.com/onegov/onegov-cloud/commit/34a97c1c2c2b76f2f4ca690bfd4b752431cfdfd1)

### Form

##### Add security hint for yaml loading.

`Feature` | [SEA-1010](https://linear.app/seantis/issue/SEA-1010) | [05d69feec0](https://github.com/onegov/onegov-cloud/commit/05d69feec09974ccabe995e250a133e4c145a639)

### Org

##### Small Adjustments

Slightly larger page text
Version number in footer
Hover effect on Navigation

`Feature` | [611c884776](https://github.com/onegov/onegov-cloud/commit/611c884776d048ff7d5f104ccf7c7e40c092e471)

##### Minor code improvement

`Improvement` | [OGC-1076](https://linear.app/onegovcloud/issue/OGC-1076) | [7278d680a8](https://github.com/onegov/onegov-cloud/commit/7278d680a871b4f03cf3d8afd66aa0f5eca32714)

##### Indent check only activated for new and edit forms but not for displaying.

Activate indent check while parsing form code only if originating from core validators which means there is either a new or an edited form code to be parsed.

`Bugfix` | [ogc-1027](#ogc-1027) | [dedde69fef](https://github.com/onegov/onegov-cloud/commit/dedde69fef1a6f306aaaeb26c5526bfa435d0666)

### Swissvotes

##### Fixes button text for adding pages.

`Bugfix` | [32c5a26dcf](https://github.com/onegov/onegov-cloud/commit/32c5a26dcf4c9537edd1b3d20348f1c761410d29)

### Town6

##### Add option for a testimonial slider

`Feature` | [OGC-761](https://linear.app/onegovcloud/issue/OGC-761) | [623e0a4a83](https://github.com/onegov/onegov-cloud/commit/623e0a4a8339a790da19f92989d6c07a50ecf0e2)

##### Display previous and next entries

`Feature` | [OGC-740](https://linear.app/onegovcloud/issue/OGC-740) | [d2ef277915](https://github.com/onegov/onegov-cloud/commit/d2ef277915d43bcaec08c5a89651a4ac39ded6c9)

##### Fixes E-mail template

Removes reference to deleted 'sender' mail macro from mail template.

`Bugfix` | [OGC-1090](https://linear.app/onegovcloud/issue/OGC-1090) | [c10d67a954](https://github.com/onegov/onegov-cloud/commit/c10d67a95465091bb23ea3c4fdd3b48b51498535)

## 2023.19

`2023-04-30` | [2c4fdd7c74...c49813dfd5](https://github.com/OneGov/onegov-cloud/compare/2c4fdd7c74^...c49813dfd5)

### Ballot

##### Fixes file constraints.

`Bugfix` | [OGC-1073](https://linear.app/onegovcloud/issue/OGC-1073) | [2c4fdd7c74](https://github.com/onegov/onegov-cloud/commit/2c4fdd7c743ae3279edf8c973e3fcc750442c0b6)

## 2023.18

`2023-04-25` | [d1acf02b0b...e5efb9ca24](https://github.com/OneGov/onegov-cloud/compare/d1acf02b0b^...e5efb9ca24)

### Feriennet

##### Make form more robust if field is missing

`Bugfix` | [pro-1116](#pro-1116) | [64139c70db](https://github.com/onegov/onegov-cloud/commit/64139c70dbe1f82c1a8351f61ff247a02acbe327)

### Town6

##### Make image preview visible

`Feature` | [d1acf02b0b](https://github.com/onegov/onegov-cloud/commit/d1acf02b0b64579b6789bd8b29dc5259ffbf6aa4)

## 2023.17

`2023-04-24` | [dc42c72bf3...0d924d70fc](https://github.com/OneGov/onegov-cloud/compare/dc42c72bf3^...0d924d70fc)

### Feriennet

##### Edit email text

`Feature` | [PRO-1126](https://linear.app/projuventute/issue/PRO-1126) | [00a56fcdf7](https://github.com/onegov/onegov-cloud/commit/00a56fcdf779d548ba7fd1ad803679d63a951fbd)

### Town6

##### Remove "Onegov Cloud Team" in mail-footer

`Feature` | [OGC-1167](https://linear.app/onegovcloud/issue/OGC-1167) | [5f9dce3952](https://github.com/onegov/onegov-cloud/commit/5f9dce3952b4096e48ef3d1946686843ca73ce12)

##### Fixes news not being displayed if it's the first item.

Fix root-level page interpretation bug for news, 
which was mistakenly being treated as falsy (index 0).

`Bugfix` | [OGC-863](https://linear.app/onegovcloud/issue/OGC-863) | [dc42c72bf3](https://github.com/onegov/onegov-cloud/commit/dc42c72bf3229270ff262b2c38a58d61cb41cfcb)

## 2023.16

`2023-04-19` | [5a8e9c14f8...53985572c5](https://github.com/OneGov/onegov-cloud/compare/5a8e9c14f8^...53985572c5)

### Feriennet

##### New banners and logo

`Feature` | [PRO-1173](https://linear.app/projuventute/issue/PRO-1173) | [fac9d2d77a](https://github.com/onegov/onegov-cloud/commit/fac9d2d77a6a8f518bce8a0767b603ef966f5653)

##### E-mail notifications on registration for activity

The attendee receives a notification on registration or cancellation of their participation.

`Feature` | [PRO-1126](https://linear.app/projuventute/issue/PRO-1126) | [c8e1e47d58](https://github.com/onegov/onegov-cloud/commit/c8e1e47d58efd0f2d1f45249865bc58bd1dabc70)

##### Invoice Items payment with dates

`Feature` | [PRO-1167](https://linear.app/projuventute/issue/PRO-1167) | [3081f7bdc1](https://github.com/onegov/onegov-cloud/commit/3081f7bdc1c4d4ad442b0c65ba50d775df03a92a)

### Org

##### Add more options to "further information" on directories

`Feature` | [OGC-928](https://linear.app/onegovcloud/issue/OGC-928) | [b34fabd9bb](https://github.com/onegov/onegov-cloud/commit/b34fabd9bb5189b3ba359963a6486c0bc9cb3b86)

### Town6

##### Make color inversion on icon links possible

`Feature` | [OGC-764](https://linear.app/onegovcloud/issue/OGC-764) | [9d77ea9d20](https://github.com/onegov/onegov-cloud/commit/9d77ea9d20c3514c65811a3a3be8dcd6a6e9726f)

##### External event url

`Feature` | [OGC-746](https://linear.app/onegovcloud/issue/OGC-746) | [a2f858c15e](https://github.com/onegov/onegov-cloud/commit/a2f858c15edd12c7002170724e44b1321c8dd883)

##### Small Fixes

`Bugfix` | [5a8e9c14f8](https://github.com/onegov/onegov-cloud/commit/5a8e9c14f87e838bbaf188ad5ed784db04312f07)

## 2023.15

`2023-04-14` | [d83694ed38...54d349b1ba](https://github.com/OneGov/onegov-cloud/compare/d83694ed38^...54d349b1ba)

### Core

##### Fix a lot bugbear warnings.

`Feature` | [ed22bb2831](https://github.com/onegov/onegov-cloud/commit/ed22bb2831c4358f8363bada4203ea83b5c11fae)

##### Enable flake8 bugbear.

Enables bugbear in pre-commit and CI linting, also introduces a garbage collector friendly LRU cache variant.

`Feature` | [OGC-1052](https://linear.app/onegovcloud/issue/OGC-1052) | [e0e6a99d35](https://github.com/onegov/onegov-cloud/commit/e0e6a99d35bf9558fb08d91e9a57d4a874f1ed90)

### Election Day

##### Make clear media callout more specific.

`Feature` | [d83694ed38](https://github.com/onegov/onegov-cloud/commit/d83694ed388b1dba07f22a71ff227d6e47115b6b)

##### Add browser notification hint.

`Feature` | [74e039b610](https://github.com/onegov/onegov-cloud/commit/74e039b610533af64760bbc7c89568345ca0686c)

##### Fixes missing translation.

`Bugfix` | [c64b7ab263](https://github.com/onegov/onegov-cloud/commit/c64b7ab263f880d5d8b984b80e4bd1981bae8484)

### Feriennet

##### Add option to add a differing address for an attendee

`Feature` | [PRO-1116](https://linear.app/projuventute/issue/PRO-1116) | [c5fd8149d3](https://github.com/onegov/onegov-cloud/commit/c5fd8149d3469c992662c493f3871aba5f93cfb5)

##### Update Banners

`Feature` | [PRO-1170](https://linear.app/projuventute/issue/PRO-1170) | [00485719b0](https://github.com/onegov/onegov-cloud/commit/00485719b04e43e5dfb723645f83ef747f16b790)

##### Display free spots until booking phase has ended

If "Allow bookings after the bills have been created." is checked in the phase settings the booking phase will only end once the actual end date of the booking phase is reached.

`Feature` | [PRO-909](https://linear.app/projuventute/issue/PRO-909) | [c582039985](https://github.com/onegov/onegov-cloud/commit/c582039985bcbb4b875fcf831e17d480806b727b)

##### Invoice Link access denied

Displays "access denied" instead of "page not found" if Invoice exists.

`Bugfix` | [PRO-1149](https://linear.app/projuventute/issue/PRO-1149) | [bbb5393d3f](https://github.com/onegov/onegov-cloud/commit/bbb5393d3f2040da22252bd38e855010a98a0efa)

##### Only show attendees with booking for occasion

`Bugfix` | [PRO-1159](https://linear.app/projuventute/issue/PRO-1159) | [623fffecf7](https://github.com/onegov/onegov-cloud/commit/623fffecf70fc84102bcd03e1fee2080ecd8ab90)

### Org

##### Prioritize Events in search, and sort chronologically.

`Feature` | [OGC-908](https://linear.app/onegovcloud/issue/OGC-908) | [d65229c4e6](https://github.com/onegov/onegov-cloud/commit/d65229c4e671fe249d20acad9931d8907141029a)

### Search

##### Make model loading more robust to corrupt search indexes.

`Bugfix` | [f799ac39fa](https://github.com/onegov/onegov-cloud/commit/f799ac39fad2a22c5b780dd7d316742d7082cdd8)

### Town6

##### Improve mail text for ticket.

`Bugfix` | [OGC-1028](https://linear.app/onegovcloud/issue/OGC-1028) | [39b56314db](https://github.com/onegov/onegov-cloud/commit/39b56314db219ada9f70b22398e2288e7416af65)

## 2023.14

`2023-03-31` | [29986838ad...a5d780608d](https://github.com/OneGov/onegov-cloud/compare/29986838ad^...a5d780608d)

### Ballot

##### Speed up import of proporz elections.

`Bugfix` | [9feda8c6ca](https://github.com/onegov/onegov-cloud/commit/9feda8c6ca62d9d8d17c111c1fe6700b6cef5b4e)

### Core

##### Use latest pytest-localserver.

`Other` | [OGC-444](https://linear.app/onegovcloud/issue/OGC-444) | [9c3ba6a301](https://github.com/onegov/onegov-cloud/commit/9c3ba6a3011b402d90c694e0a8cc5516281d3ab4)

##### Don't use deferral on timestamp columns.

Timestamps don't add a lot of data to queries but accessing them will 
lead to a lot of additional queries. Also, nobody expects these 
timestamps to be deferred in the first place.

`Bugfix` | [6288609773](https://github.com/onegov/onegov-cloud/commit/6288609773ffc7cc447db2dd267e7dd433c00ff1)

### Election Day

##### Show timestamp of when the last archive was generated.

`Feature` | [OGC-885](https://linear.app/onegovcloud/issue/OGC-885) | [60a155a619](https://github.com/onegov/onegov-cloud/commit/60a155a61997a522bd48788d4937badb1f0bc3db)

##### Add fixture for candidate panachage results.

`Feature` | [33bf6b6be9](https://github.com/onegov/onegov-cloud/commit/33bf6b6be9b5a10acc7dbd243eac5716dbf31c90)

##### Add websocket notification fallback.

Falls back to short polling using a cached endpoint, in case the websocket server is unreachable or out of workers.

`Feature` | [OGC-991](https://linear.app/onegovcloud/issue/OGC-991) | [ca68ec36ce](https://github.com/onegov/onegov-cloud/commit/ca68ec36cef0612c2a62e3fcfb38c089cc3687b0)

##### Fix entity filter sorting.

`Bugfix` | [1e2b8b65e6](https://github.com/onegov/onegov-cloud/commit/1e2b8b65e68a412d15d8ff00cebab1bba3d8a9ce)

### Ferienet

##### Update banners

`Feature` | [PRO-1163](https://linear.app/projuventute/issue/PRO-1163) | [a367bc346c](https://github.com/onegov/onegov-cloud/commit/a367bc346c0bea35bfb0105135aee4eb13bff397)

### Feriennet

##### Make sure importing transaction files works again.

`Bugfix` | [PRO-1156](https://linear.app/projuventute/issue/PRO-1156) | [93c4d96653](https://github.com/onegov/onegov-cloud/commit/93c4d96653219c706549e9aef97d9fcac05664f0)

##### Dashboard Occasions

Only counts occasions of accepted activities

`Bugfix` | [PRO-1161](https://linear.app/projuventute/issue/PRO-1161) | [58a2a4f497](https://github.com/onegov/onegov-cloud/commit/58a2a4f4971afc51d2257672a4ce6edcc0df767f)

### Org

##### Extends allocation cleanup view with a weekday filter

`Feature` | [OGC-1032](https://linear.app/onegovcloud/issue/OGC-1032) | [b0ad130ed7](https://github.com/onegov/onegov-cloud/commit/b0ad130ed701f51b2c414b0249e43144022c9b98)

### Town6

##### Map view

Reposition map on directory overview.

`Feature` | [OGC-996](https://linear.app/onegovcloud/issue/OGC-996) | [8ea9293963](https://github.com/onegov/onegov-cloud/commit/8ea9293963cfd88001b4c8c694ee0b013caad46d)

## 2023.13

`2023-03-17` | [0edf69e38c...d788d97796](https://github.com/OneGov/onegov-cloud/compare/0edf69e38c^...d788d97796)

### Ballot

##### Remove old panachage model.

`Feature` | [OGC-769](https://linear.app/onegovcloud/issue/OGC-769) | [73573b2e0f](https://github.com/onegov/onegov-cloud/commit/73573b2e0fbeab7647ffbb96902d4397f4bb9421)

### Election Day

##### Improve accessability.

`Feature` | [OGC-1022](https://linear.app/onegovcloud/issue/OGC-1022) | [0edf69e38c](https://github.com/onegov/onegov-cloud/commit/0edf69e38cecc8ace8609c2bd2060bba98e8fad3)

##### Allow embedded elements to be localized independently of the locale stored in the cookie.

`Feature` | [dc5ea09a3e](https://github.com/onegov/onegov-cloud/commit/dc5ea09a3e71f85dc4498540843f5504a07e2c32)

##### Fixes javascript boolean conversion.

`Bugfix` | [6d075c66e5](https://github.com/onegov/onegov-cloud/commit/6d075c66e57633c7e228e849aa8ac623833f99f7)

### Feriennet

##### Add new banner

`Feature` | [PRO-1163](https://linear.app/projuventute/issue/PRO-1163) | [8e238305cc](https://github.com/onegov/onegov-cloud/commit/8e238305ccd9647b1ff8f0cddbe4958c7923377d)

##### Add option to mark invoice as paid with specific date

`Feature` | [PRO-1115](https://linear.app/projuventute/issue/PRO-1115) | [b456bb5030](https://github.com/onegov/onegov-cloud/commit/b456bb50306c9c6905eeb984207a68fd89c722cc)

##### Make test independent of DST.

`Bugfix` | [4ecaa95118](https://github.com/onegov/onegov-cloud/commit/4ecaa95118d0018813d696575d06db65a1072e1e)

##### Make another test independent of DST.

`Bugfix` | [a0e00d9e75](https://github.com/onegov/onegov-cloud/commit/a0e00d9e75144395b70049ec262064b3523d4e20)

### Org

##### Catch exception to prevent unresponsive 'link insert' overlay.

Even if the call selectNodeContents fails – it still works.

`Bugfix` | [OGC-1013](https://linear.app/onegovcloud/issue/OGC-1013) | [4bcd6e25ff](https://github.com/onegov/onegov-cloud/commit/4bcd6e25ff301ac9370efa5fc914177f963dd3de)

### Topics

##### Now any admin can add topics (pages) on the top (root) level.

`Feature` | [ogc-263](#ogc-263) | [ee79665d54](https://github.com/onegov/onegov-cloud/commit/ee79665d5470916ab735cc70db43eaa52aaced95)

### Town6

##### Only show "submit changes" if activated

`Bugfix` | [OGC-955](https://linear.app/onegovcloud/issue/OGC-955) | [bb85a255b0](https://github.com/onegov/onegov-cloud/commit/bb85a255b054e62ed9a8b7a75a2739f44a61f197)

## 2023.12

`2023-03-14` | [7685f751c6...e44f392c03](https://github.com/OneGov/onegov-cloud/compare/7685f751c6^...e44f392c03)

### Ballot

##### Split panachage result models.

`Feature` | [OGC-769](https://linear.app/onegovcloud/issue/OGC-769) | [4bc20e77a2](https://github.com/onegov/onegov-cloud/commit/4bc20e77a22c57aba2c01db981f2f32d0044b835)

### Core

##### Adds compatibility with latest chameleon release.

`Feature` | [9e2581836d](https://github.com/onegov/onegov-cloud/commit/9e2581836d38e1e8b7d0f02032c8a7a69d726338)

### Election Day

##### Add candidate panachage model, import and export.

`Feature` | [OGC-927](https://linear.app/onegovcloud/issue/OGC-927) | [cda513c9e7](https://github.com/onegov/onegov-cloud/commit/cda513c9e713d36d894037a76cb667ea35dd0025)

##### Avoid adding intermediate results of uncounted entities to proporz election.

`Bugfix` | [OGC-904](https://linear.app/onegovcloud/issue/OGC-904) | [d9d7ba371a](https://github.com/onegov/onegov-cloud/commit/d9d7ba371aff8fd90071d939786a6984539e62a1)

### Form

##### Increase default file upload limit to 15MB

`Feature` | [OGC-1012](https://linear.app/onegovcloud/issue/OGC-1012) | [f5e04760a0](https://github.com/onegov/onegov-cloud/commit/f5e04760a0c3de4c80421956fb5a05fa048dbdf3)

##### Accepts submissions of 0-values in required numeric fields

Previously due to 0-values not being truthy, they would get rejected by
the DataRequired validator on required fields in user-defined forms.

`Bugfix` | [OGC-1014](https://linear.app/onegovcloud/issue/OGC-1014) | [80cca6ed11](https://github.com/onegov/onegov-cloud/commit/80cca6ed114ce8baa84f81c7cbb7efac5169c3e4)

### Onboarding

##### Styling adjustments.

Also Removes the CSS :has selector which is not supported by all
major browsers at this point.

`Bugfix` | [8e943b5b14](https://github.com/onegov/onegov-cloud/commit/8e943b5b14b999d2e18c44fa2f30d1533e91cff8)

### Org

##### Allows external authentication providers to be marked as primary (#733)

Org: Allows external authentication providers to be marked as primary

The first primary provider for any given application will be pinned to
the top of the login page.

`Feature` | [OGC-1007](https://linear.app/onegovcloud/issue/OGC-1007) | [6d684c73c6](https://github.com/onegov/onegov-cloud/commit/6d684c73c673d0611f9d2ad6457af1bb884b855f)

##### Add default function for editor.

`Feature` | [OGC-985](https://linear.app/onegovcloud/issue/OGC-985) | [d79e1ccd65](https://github.com/onegov/onegov-cloud/commit/d79e1ccd65169e93054f9b4106a8d6fe1b1f724b)

### Server

##### Add compatibility with latest watchdog release.

`Feature` | [7685f751c6](https://github.com/onegov/onegov-cloud/commit/7685f751c63e4d020676711c9bdb9c417f8a2019)

##### Fixes test.

`Bugfix` | [c984fe482b](https://github.com/onegov/onegov-cloud/commit/c984fe482bf529f20afbe561088485293c5ac0ae)

### Websockets

##### Fix flaky test.

`Bugfix` | [1d51e921c5](https://github.com/onegov/onegov-cloud/commit/1d51e921c59c8eb9215b33b0f80d2a41d0d7c866)

## 2023.11

`2023-03-06` | [db16f8cb70...395e461899](https://github.com/OneGov/onegov-cloud/compare/db16f8cb70^...395e461899)

### Core

##### Pin Chameleon and resolve build container issues

`Bugfix` | [db16f8cb70](https://github.com/onegov/onegov-cloud/commit/db16f8cb70be1db510202780570d21cc4b763577)

## 2023.10

`2023-03-06` | [b7781dac32...f086f478b9](https://github.com/OneGov/onegov-cloud/compare/b7781dac32^...f086f478b9)

### Core

##### Pin Watchdog

`Bugfix` | [b7781dac32](https://github.com/onegov/onegov-cloud/commit/b7781dac326d39822a0dd3675f9992795e90e129)

### Feriennet

##### New Google Analytics Code

`Feature` | [PRO-1155](https://linear.app/projuventute/issue/PRO-1155) | [89a5fd502f](https://github.com/onegov/onegov-cloud/commit/89a5fd502faf30e2cce46db7e39fdb0f0959ac5c)

### Town6

##### Update widget in initial homepage structure.

`Feature` | [OGC-600](https://linear.app/onegovcloud/issue/OGC-600) | [8981201d9d](https://github.com/onegov/onegov-cloud/commit/8981201d9d0abaa07bd4c2f04e5b5157a47cbde2)

## 2023.9

`2023-03-06` | [aaba33b401...978ee79f4d](https://github.com/OneGov/onegov-cloud/compare/aaba33b401^...978ee79f4d)

### Election Day

##### Avoid opening unneccessary websockets.

`Bugfix` | [OGC-991](https://linear.app/onegovcloud/issue/OGC-991) | [aaba33b401](https://github.com/onegov/onegov-cloud/commit/aaba33b401bcbcbc0f36729a0180a3ceb578a892)

##### Always enable notifications menu.

`Bugfix` | [OGC-991](https://linear.app/onegovcloud/issue/OGC-991) | [22be9e47d4](https://github.com/onegov/onegov-cloud/commit/22be9e47d4f23fb1297530eb8b4fa8f93c2cad72)

### Feriennet

##### Dashboard improvements

`Feature` | [OGC-1119](https://linear.app/onegovcloud/issue/OGC-1119) | [748eb4d007](https://github.com/onegov/onegov-cloud/commit/748eb4d007775713623237e4543c47d4290745da)

##### Volunteer export add translations

`Bugfix` | [PRO-1015](https://linear.app/projuventute/issue/PRO-1015) | [b134fc4018](https://github.com/onegov/onegov-cloud/commit/b134fc4018153049c8e58ae78393962e724407ac)

##### Removes non-breaking whitespaces from QR bill debtor names.

`Bugfix` | [PRO-1145](https://linear.app/projuventute/issue/PRO-1145) | [d41b35c474](https://github.com/onegov/onegov-cloud/commit/d41b35c47478307be37f1d70d68218cf9dbf7b4c)

##### Send mail to user if not in recipient list

`Bugfix` | [PRO-1021](https://linear.app/projuventute/issue/PRO-1021) | [c92779861f](https://github.com/onegov/onegov-cloud/commit/c92779861f9b1f42dee9a25abf398b1e1f5be8af)

### Form

##### Catches MixedTypeError in ValidFormDefinition

This fixes a crash when entering a form with mixed radio/checkboxes

`Bugfix` | [26b4badaa3](https://github.com/onegov/onegov-cloud/commit/26b4badaa3eb095e87b1959ac97f6f5f88dc8b81)

### Gis

##### Fixes flaky behavior when selecting an address from search results

Specifically sometimes the marker would not move or the map would not
complete its animation to center on the newly selected address.

`Bugfix` | [OGC-995](https://linear.app/onegovcloud/issue/OGC-995) | [e4e9bc5b69](https://github.com/onegov/onegov-cloud/commit/e4e9bc5b69c0e096c06ef8d0f9ff65df322311e8)

### Onboarding

##### Extend form with more fields.

`Feature` | [OGC-601](https://linear.app/onegovcloud/issue/OGC-601) | [e6ed967cbc](https://github.com/onegov/onegov-cloud/commit/e6ed967cbcd04626b9c8d116eb8f868db56b8789)

### Org

##### Fixes occupancy link in reservation calendar

Depending on the start time and timezone of the allocation it sometimes

`Bugfix` | [OGC-1004](https://linear.app/onegovcloud/issue/OGC-1004) | [1316739c26](https://github.com/onegov/onegov-cloud/commit/1316739c266e1599cec33448771751ac36fe0121)

##### Fixes translations.

`Bugfix` | [80decde7cc](https://github.com/onegov/onegov-cloud/commit/80decde7cc85691f66f999432d6bf832bf4803b8)

##### Replaces the entry count in the DirectoriesWidget with the lead

The entry count was misleading because it did not take the entry's
visibility into account. Counting properly would be too slow for a
widget, so we show the lead instead.

`Bugfix` | [OGC-1006](https://linear.app/onegovcloud/issue/OGC-1006) | [5e2a9f44c5](https://github.com/onegov/onegov-cloud/commit/5e2a9f44c55840706145fcc59590283e840f0780)

##### Probibit inactive user to reset password

`Bugfix` | [PRO-1141](https://linear.app/projuventute/issue/PRO-1141) | [ae5e9dc806](https://github.com/onegov/onegov-cloud/commit/ae5e9dc80682c0ca924648129891bcd697a5ef51)

##### Fix Forms without group not being displayed.

`Bugfix` | [OGC-857](https://linear.app/onegovcloud/issue/OGC-857) | [4d998b90be](https://github.com/onegov/onegov-cloud/commit/4d998b90be087a7b5e4b29a282a6072d8490a5d0)

### Town6

##### Reduce events to 3 columns

Reduce to 3 columns to prevent ugly word wrapping.

`Feature` | [OGC-989](https://linear.app/onegovcloud/issue/OGC-989) | [94192987e9](https://github.com/onegov/onegov-cloud/commit/94192987e996f3c655b23ab1625e9e4f356a503c)

##### Fix styling problem in town6

`Bugfix` | [OGC-1001](https://linear.app/onegovcloud/issue/OGC-1001) | [899ea2347b](https://github.com/onegov/onegov-cloud/commit/899ea2347b5f57f86bce8220ad248ec0c5caf303)

##### Make suggestion panel solely dependant on enable_submissions

`Bugfix` | [OGC-955](https://linear.app/onegovcloud/issue/OGC-955) | [14193e75a9](https://github.com/onegov/onegov-cloud/commit/14193e75a9688ff12417ee20c2c48544ffb59532)

##### Fixes translations.

`Bugfix` | [4c9ac18f60](https://github.com/onegov/onegov-cloud/commit/4c9ac18f601f935e1888c5b945d8d8ce7d217c71)

##### Hide Gever Upload in navbar if it is not set in settings

`Bugfix` | [OGC-922](https://linear.app/onegovcloud/issue/OGC-922) | [cfe5a77f8d](https://github.com/onegov/onegov-cloud/commit/cfe5a77f8dd3ad5a7c27299b618f73becda3be7b)

##### Improvements to list of context-specific functions.

`Bugfix` | [OGC-731](https://linear.app/onegovcloud/issue/OGC-731) | [fc88d48d97](https://github.com/onegov/onegov-cloud/commit/fc88d48d972ec62f779bb2891a071c50e1b4a524)

### User

##### Adds missing translations.

`Bugfix.` | [153cbe7645](https://github.com/onegov/onegov-cloud/commit/153cbe764558e3ecdf326b65ad2fa70060e62174)

## 2023.8

`2023-02-22` | [1e0511b88a...ec2b45a0d6](https://github.com/OneGov/onegov-cloud/compare/1e0511b88a^...ec2b45a0d6)

### Core

##### Pin pglast.

`Other` | [OGC-992](https://linear.app/onegovcloud/issue/OGC-992) | [ce99e18448](https://github.com/onegov/onegov-cloud/commit/ce99e18448ec49ead487991cda17d91f3e8a1ac8)

##### Add compatibility with pglast 5.

`Bugfix` | [OGC-992](https://linear.app/onegovcloud/issue/OGC-992) | [39d6b449bf](https://github.com/onegov/onegov-cloud/commit/39d6b449bfbd52dcd926d866968a1dce302c54bf)

### Directory

##### Adds UploadMultipleField support to directories

Also fixes some rendering issues in the field display macro.

`Feature` | [OGC-911](https://linear.app/onegovcloud/issue/OGC-911) | [184afffab9](https://github.com/onegov/onegov-cloud/commit/184afffab9da347dc6555aea3a536aa3a3776f59)

### Election Day

##### Add websocket notifications.

Enables notifications to be sent to browsers connected via websockets. When the browsers are on the detail page for which the notification was triggered, a page refresh banner is displayed.

`Feature` | [OGC-991](https://linear.app/onegovcloud/issue/OGC-991) | [072c059848](https://github.com/onegov/onegov-cloud/commit/072c0598484466a8eb96e49c633b13bdeb9e18c1)

### Events

##### Events from the past can be shown. (#708)

In the case of 'No events found' we will display two link buttons. One will
point to 'all events' where as the other will show 'past events'. In addition
a new time range filter 'past events' was added to achieve the same from
filters.

`Feature` | [OGC-947](https://linear.app/onegovcloud/issue/OGC-947) | [2905f9d7f6](https://github.com/onegov/onegov-cloud/commit/2905f9d7f6a0593135175c98e2b4b896bd07cc01)

### Feriennet

##### Use main sponsor exclusively for bookings and invoices

`Feature` | [PRO-1143](https://linear.app/projuventute/issue/PRO-1143) | [1e0511b88a](https://github.com/onegov/onegov-cloud/commit/1e0511b88a5344ba60d71d46562c0694321e63ba)

##### Add new categories

`Feature` | [PRO-1150](https://linear.app/projuventute/issue/PRO-1150) | [9fa2f0b23e](https://github.com/onegov/onegov-cloud/commit/9fa2f0b23e679ce8949c7b398394d2e4af267f35)

##### Sponsor banners in mail

`Feature` | [PRO-1002](https://linear.app/projuventute/issue/PRO-1002) | [d2ccec14e1](https://github.com/onegov/onegov-cloud/commit/d2ccec14e1979a647a864594cd29a08a45c17f86)

##### New Google Analytics Code

`Feature` | [PRO-1071](https://linear.app/projuventute/issue/PRO-1071) | [581f8fab60](https://github.com/onegov/onegov-cloud/commit/581f8fab605a23618ee073b135f96f339495505a)

##### Show names of other children in bookings

`Feature` | [PRO-1090](https://linear.app/projuventute/issue/PRO-1090) | [69ecf5aa4d](https://github.com/onegov/onegov-cloud/commit/69ecf5aa4da49636165660b652fa4bd8744f879e)

##### Export for volunteers

`Feature` | [PRO-1015](https://linear.app/projuventute/issue/PRO-1015) | [b3bc1e8f33](https://github.com/onegov/onegov-cloud/commit/b3bc1e8f335de407d49409c0de44a043639e591d)

##### Text Adjustments

`Bugfix` | [PRO-1046](https://linear.app/projuventute/issue/PRO-1046) | [a89a11b46c](https://github.com/onegov/onegov-cloud/commit/a89a11b46c9118a60bac5c01ded7aae6e9dcf084)

##### Fixes page error in layout due to wrong sponsor collection handling

`Bugfix` | [OCG-988](#OCG-988) | [4fae792261](https://github.com/onegov/onegov-cloud/commit/4fae79226152a037031de024da50d5fdc79d69d2)

### File

##### Set X-Robots-Tag to noindex if the file's access is `secret`. (#714)

By default attachments to directory entries and form submissions are
set to `secret` now. They will still be listed in the rendered form.

`Feature` | [OGC-916](https://linear.app/onegovcloud/issue/OGC-916) | [9ac2231d58](https://github.com/onegov/onegov-cloud/commit/9ac2231d5882b59d6d0ad3b263b46d0224abaf90)

### Form

##### Adds optional valid date ranges to date/datetime fields.

Date ranges can either be specified using absolute dates or relative to
today. Relative dates are a signed integer followed by one of `days`,
`weeks`, `months`, `years` or the special value `today`. Examples:
```
    I'm a future date field = YYYY.MM.DD (+1 days..)
    I'm on today or in the future = YYYY.MM.DD (today..)
    I'm at least two weeks ago = YYYY.MM.DD (..-2 weeks)
    I'm between 2010 and 2020 = YYYY.MM.DD (2010.01.01..2020.12.31)
```

`Feature` | [OGC-744](https://linear.app/onegovcloud/issue/OGC-744) | [5081413c45](https://github.com/onegov/onegov-cloud/commit/5081413c456e2ba72716a9aa6c4b7275cc7ef7af)

##### Adds `UploadMultipleField` to forms and a modifier to form code

This is especially useful for custom forms defined using form code since
sometimes you want people to be able to submit multiple files without
having to create a bunch of single file fields. Example:

```
Documents = *.pdf (multiple)
```

`Feature` | [OGC-915](https://linear.app/onegovcloud/issue/OGC-915) | [7d620146a2](https://github.com/onegov/onegov-cloud/commit/7d620146a2fc88b4c0c826982f6275fae84ec49a)

##### Fixes dependency.

`Bugfix` | [5b789d1277](https://github.com/onegov/onegov-cloud/commit/5b789d1277fd66225d969a41c5844dc2fc0be988)

### Gis

##### Remove debug statements.

`Bugfix` | [0e9f51368f](https://github.com/onegov/onegov-cloud/commit/0e9f51368f13758649d88d0db925f893bbfc8a6f)

### Org

##### Side panel with title

`Bugfix` | [PRO-1142](https://linear.app/projuventute/issue/PRO-1142) | [23be87dc51](https://github.com/onegov/onegov-cloud/commit/23be87dc51c186b9934c79c461dbc4bb7f540fc9)

### Town6

##### Rename Side Panel

`Bugfix` | [0b8e71b54d](https://github.com/onegov/onegov-cloud/commit/0b8e71b54d76581609d7dd48708edf3aa65b2efc)

##### Make events navbar consistent design with button.

`Bugfix` | [OGC-745](https://linear.app/onegovcloud/issue/OGC-745) | [0a58567cbf](https://github.com/onegov/onegov-cloud/commit/0a58567cbfe64e279fc1a1d81112010d98687a1c)

### Websockets

##### Add channels.

`Feature` | [OGC-935](https://linear.app/onegovcloud/issue/OGC-935) | [6dd9dfef87](https://github.com/onegov/onegov-cloud/commit/6dd9dfef870facc4c1bb32687836cc7e91328fd2)

##### Add content security policy tween.

Allows to optionally add a websocket endpoint to the connect-src content 
security policy.

`Feature` | [OGC-935](https://linear.app/onegovcloud/issue/OGC-935) | [9b2a006baf](https://github.com/onegov/onegov-cloud/commit/9b2a006baf374b7514a871bae18ddabf66326c8e)

### Winterthur

##### Form validation on positive Integers.

`Bugfix` | [OGC-954](https://linear.app/onegovcloud/issue/OGC-954) | [4ba577d491](https://github.com/onegov/onegov-cloud/commit/4ba577d49145e87d6e78e8c0224bf16ea6f05e78)

## 2023.7

`2023-02-13` | [0504bce18a...a738192829](https://github.com/OneGov/onegov-cloud/compare/0504bce18a^...a738192829)

### Election Day

##### Allow alphanumeric list and party IDs.

`Feature` | [OGC-936](https://linear.app/onegovcloud/issue/OGC-936) | [99aca42cb5](https://github.com/onegov/onegov-cloud/commit/99aca42cb59868bdff1790a0c52c6448f1147538)

##### Avoid displaying bar charts with only inactive bars.

Show bar chart bars as active as long as no mandate has been allocated.

`Feature` | [OGC-934](https://linear.app/onegovcloud/issue/OGC-934) | [fcf926e009](https://github.com/onegov/onegov-cloud/commit/fcf926e009668fa279ef7ec54f76401b79d94e21)

##### Add historical colors for party results.

`Feature` | [OGC-931](https://linear.app/onegovcloud/issue/OGC-931) | [792624b1ae](https://github.com/onegov/onegov-cloud/commit/792624b1ae489b9be502cd22ed1eafb11463979f)

##### Add QR-code widget.

`Feature` | [OGC-884](https://linear.app/onegovcloud/issue/OGC-884) | [5bd0e8e784](https://github.com/onegov/onegov-cloud/commit/5bd0e8e784b26d128d84e87a89dd7bade150b60b)

##### Add total rows to election compound and election compound part statistics.

`Feature` | [OGC-975](https://linear.app/onegovcloud/issue/OGC-975) | [e27e1ca5e2](https://github.com/onegov/onegov-cloud/commit/e27e1ca5e209805b81c6143f8e83b08bae4c561c)

##### Prefer AnzPendentGde instead of AnzGdePendent for WabstiC formats.

`Feature` | [OGC-907](https://linear.app/onegovcloud/issue/OGC-907) | [0df166b2d9](https://github.com/onegov/onegov-cloud/commit/0df166b2d9b37e67d797774926c8b55754f1d52d)

##### Hide empty party strength lines.

`Bugfix` | [OGC-941](https://linear.app/onegovcloud/issue/OGC-941) | [96c78d3231](https://github.com/onegov/onegov-cloud/commit/96c78d32310b7fe793100eb0ed419a3a841b379d)

##### Remove counted_eligible_voters and counted_received ballots.

This was only partial solution and should have been provided for all  attributes and results. Instead of these attributes, we now make sure to zeroize uncounted entities.

`Bugfix` | [OGC-893](https://linear.app/onegovcloud/issue/OGC-893) | [ad627783b5](https://github.com/onegov/onegov-cloud/commit/ad627783b53bb230ebd8be07860bea62902567aa)

##### Standardize panachage diagrams.

`Bugfix` | [OGC-906](https://linear.app/onegovcloud/issue/OGC-906) | [9d3ca42e1f](https://github.com/onegov/onegov-cloud/commit/9d3ca42e1f80066e6f31705c5786063027eca9c0)

##### Sort entity filter by name.

`Bugfix` | [OGC-974](https://linear.app/onegovcloud/issue/OGC-974) | [3f67840bb4](https://github.com/onegov/onegov-cloud/commit/3f67840bb4c06783fe9ee9afed867a8829f91826)

### Org

##### Allows publication dates on directory entries to be required

This is useful for directories where the publication has to be limited
e.g. for planning applications, where a public participation period is
mandated, but publishing it beyond that would raise privacy concerns.

`Feature` | [OGC-913](https://linear.app/onegovcloud/issue/OGC-913) | [0504bce18a](https://github.com/onegov/onegov-cloud/commit/0504bce18af027830c98b5c4f454bd5e77f245ba)

##### Fixes rendering of external links in search results

`Bugfix` | [OGC-959](https://linear.app/onegovcloud/issue/OGC-959) | [b186e5dbd8](https://github.com/onegov/onegov-cloud/commit/b186e5dbd8feffa67cf9f65066671f06af0abff2)

### Town6

##### Adds Missing commas in the error message.

`Bugfix` | [OGC-943](https://linear.app/onegovcloud/issue/OGC-943) | [73cd1a05ce](https://github.com/onegov/onegov-cloud/commit/73cd1a05ce824cbec8330fc623c60400ffe3c04c)

##### Add the translation string.

`Bugfix` | [OGC-945](https://linear.app/onegovcloud/issue/OGC-945) | [6af98f0f3a](https://github.com/onegov/onegov-cloud/commit/6af98f0f3a96a6568c2489246106f9ef020e78aa)

### Websockets

##### Add websocket server and client.

`Feature` | [OGC-935](https://linear.app/onegovcloud/issue/OGC-935) | [4d1f7ea474](https://github.com/onegov/onegov-cloud/commit/4d1f7ea474ce4925266d0aa161e3204fe6f171ca)

## 2023.6

`2023-02-08` | [0ea641df42...ca101f7ca1](https://github.com/OneGov/onegov-cloud/compare/0ea641df42^...ca101f7ca1)

### Election Day

##### Fixes horizontal party strengths bar char data.

`Bugfix` | [030c1eda6a](https://github.com/onegov/onegov-cloud/commit/030c1eda6ae5c21a20a7657cc5770965d40cb9f9)

##### Allow uploading intermediate party results to proporz elections.

`Bugfix` | [fb9ab7bdba](https://github.com/onegov/onegov-cloud/commit/fb9ab7bdba7380e3ec20e81e02f80b8d8b9c368a)

##### Fixes progress of superregions.

`Bugfix` | [OGC-952](https://linear.app/onegovcloud/issue/OGC-952) | [769321a7f8](https://github.com/onegov/onegov-cloud/commit/769321a7f8f2b8656b7f0c56347ac064a40a800b)

### Feriennet

##### Text for Banners

`Feature` | [PRO-880](https://linear.app/projuventute/issue/PRO-880) | [ecb1042703](https://github.com/onegov/onegov-cloud/commit/ecb1042703ebf259a131ce395ca74aedefcafccf)

##### Replace privacy protection links

`Feature` | [OGC-1072](https://linear.app/onegovcloud/issue/OGC-1072) | [9ed0040f97](https://github.com/onegov/onegov-cloud/commit/9ed0040f97657a2a919323c1c1dc46ed7a5b832d)

##### Remove CS Logo

`Feature` | [PRO-1131](https://linear.app/projuventute/issue/PRO-1131) | [a96b8c2ad9](https://github.com/onegov/onegov-cloud/commit/a96b8c2ad9e803ec2e05f446c5b4cb3a39e2335e)

##### Banners between activities

Sponsor banners appear now on the activities overview.

`Feature` | [PRO-1136](https://linear.app/projuventute/issue/PRO-1136) | [3c534cce29](https://github.com/onegov/onegov-cloud/commit/3c534cce292e030c48ae859324d4d4eb689460a0)

### Form

##### Extends pricing options with a credit card payment flag

This allows users to define custom forms where the credit card payment
is mandatory based on whether or not the person submitting the form has
selected a certain option or not.

E.g. a delivery field where they have to pay online right away if they
want the item to be delivered, but they can pay later in person if
they choose to pick it up themselves instead:

```
Delivery *=
    ( ) Pickup (0 CHF)
    ( ) Delivery (5 CHF!)
```

`Feature` | [OGC-910](https://linear.app/onegovcloud/issue/OGC-910) | [de8388987a](https://github.com/onegov/onegov-cloud/commit/de8388987a23599982f02c67cae954c6bbd68d57)

##### Adds optional pricing to integer range fields

Price will be multiplied by the amount entered into the field.
The credit card payment flag works on this field as well. E.g:

```
Number of stamps *= 0..30 (0.85 CHF!)
```

`Feature` | [OGC-942](https://linear.app/onegovcloud/issue/OGC-942) | [413ccbb518](https://github.com/onegov/onegov-cloud/commit/413ccbb5183ad8630eb0c3a88f58299e4aff837b)

##### Fixes bug in price range checking.

`Bugfix` | [5841945229](https://github.com/onegov/onegov-cloud/commit/584194522977f5c8d6c9ea9f09d2e61a101a9ba1)

### Org

##### Display edit bar with delete function for links.

This makes deleting links more accessible, which
was in fact already possible.

`Feature` | [OGC-739](https://linear.app/onegovcloud/issue/OGC-739) | [8097916390](https://github.com/onegov/onegov-cloud/commit/80979163905b074a7fa80a4983da0df11a4718ac)

##### Adds a minimum price field to forms, directories and resources.

Treats submissions with negative price totals like free submissions.

`Feature` | [OGC-944](https://linear.app/onegovcloud/issue/OGC-944) | [6821a8b20b](https://github.com/onegov/onegov-cloud/commit/6821a8b20bfa5828847a085f834c952f360f4985)

### Town6

##### Integration OneGov Gever.

`Feature` | [OGC-618](https://linear.app/onegovcloud/issue/OGC-618) | [b6871d13c2](https://github.com/onegov/onegov-cloud/commit/b6871d13c26acdf7944a153e2eaab98ded454b95)

##### Change appearance of "subit your event"

`Feature` | [OGC-854](https://linear.app/onegovcloud/issue/OGC-854) | [772ebf219b](https://github.com/onegov/onegov-cloud/commit/772ebf219b7d13c3ab76f0a6163526d087c9b016)

##### Allows steps in layouts to be hidden on a per view basis

This allows sharing the same layout between e.g. a guest view which has
a sequence of steps and an editor view which does not.

Hides the step sequence when adding a new directory entry as admin.

`Feature` | [OGC-956](https://linear.app/onegovcloud/issue/OGC-956) | [27f0c3570f](https://github.com/onegov/onegov-cloud/commit/27f0c3570fbbfda2a8dcc0ad2037eba01b24d1f0)

##### Create events directly without ticket.

`Feature` | [OGC-745](https://linear.app/onegovcloud/issue/OGC-745) | [ee95988a70](https://github.com/onegov/onegov-cloud/commit/ee95988a70f348a91edcb015e9c61cd12912645f)

##### Fixes translations not being applied.

`Bugfix` | [OGC-926](https://linear.app/onegovcloud/issue/OGC-926) | [75b1dd85c3](https://github.com/onegov/onegov-cloud/commit/75b1dd85c3027944a1d15d78f249c4949f353b6e)

##### Ensure translations are applied.

`Bugfix` | [2a6f73d5b5](https://github.com/onegov/onegov-cloud/commit/2a6f73d5b5ec10321a1128997313cc701acc52c1)

## 2023.5

`2023-01-25` | [550401978d...b49ae8b1f9](https://github.com/OneGov/onegov-cloud/compare/550401978d^...b49ae8b1f9)

### Feriennet

##### Increase amount of activities shown per page

`Feature` | [PRO-1013](https://linear.app/projuventute/issue/PRO-1013) | [3be762ea96](https://github.com/onegov/onegov-cloud/commit/3be762ea96da4680a8c169a111cd74a90d9ad1c6)

##### Replace sponsor images

`Feature` | [PRO-1138](https://linear.app/projuventute/issue/PRO-1138) | [636481c58a](https://github.com/onegov/onegov-cloud/commit/636481c58a002569f1940eb8902ecde956af6440)

##### Fix order of occasions in volunteer overview

`Bugfix` | [OGC-1044](https://linear.app/onegovcloud/issue/OGC-1044) | [f2c282d806](https://github.com/onegov/onegov-cloud/commit/f2c282d8061c9a3dbcd06f915467132fd78b1a8f)

### Org

##### Multiple options for numbering on directories

`Feature` | [OGC-901](https://linear.app/onegovcloud/issue/OGC-901) | [eae9a7af91](https://github.com/onegov/onegov-cloud/commit/eae9a7af9151f34644f169866c92057bdc7074fa)

### Town6

##### Redesign all lists

More unity among all lists.

`Feature` | [ce2a235252](https://github.com/onegov/onegov-cloud/commit/ce2a23525250b3ec906a37d9c95f7f8ff29ab52e)

##### Open all files in new tab if set to true

`Bugfix` | [OGC-864](https://linear.app/onegovcloud/issue/OGC-864) | [550401978d](https://github.com/onegov/onegov-cloud/commit/550401978d46257bb6ebe08ec45056a494fb7a79)

##### Calendar Buttons

`Bugfix` | [OGC-876](https://linear.app/onegovcloud/issue/OGC-876) | [e899c42614](https://github.com/onegov/onegov-cloud/commit/e899c4261439905848b00f1cc8ec129cf4ce1054)

##### Search-Button mobile

`Bugfix` | [OGC-842](https://linear.app/onegovcloud/issue/OGC-842) | [251d95fca7](https://github.com/onegov/onegov-cloud/commit/251d95fca7a2e4d56ca791d1803db61482429aa3)

## 2023.4

`2023-01-21` | [f5e079cd91...c270610705](https://github.com/OneGov/onegov-cloud/compare/f5e079cd91^...c270610705)

### Election Day

##### Add SVGs for parts of election compounds.

`Feature` | [OGC-752](https://linear.app/onegovcloud/issue/OGC-752) | [a3ed30722e](https://github.com/onegov/onegov-cloud/commit/a3ed30722e6c597cb8bdf9b194e5a405ca0faabd)

##### Update translations.

`Feature` | [OGC-726](https://linear.app/onegovcloud/issue/OGC-726) | [78577ae649](https://github.com/onegov/onegov-cloud/commit/78577ae649ce033cf629f6d114d4baf16991a5ef)

##### Improve list panaschage format description.

`Feature` | [1ca8e4425f](https://github.com/onegov/onegov-cloud/commit/1ca8e4425fcb621c37aafb882bb6e5a4283a285e)

##### Always gray out inactive bar chart rows.

`Bugfix` | [f5e079cd91](https://github.com/onegov/onegov-cloud/commit/f5e079cd91f1297e2d49010512a85d7519b49240)

##### Zeroize not yet counted results when importing majorz election from WabstiC.

`Bugfix` | [OGC-894](https://linear.app/onegovcloud/issue/OGC-894) | [24c7e69e89](https://github.com/onegov/onegov-cloud/commit/24c7e69e893cc04a75004ee2c2a1c9a8df4a7fb7)

##### Gray out candidates in bar charts only if any mandates have been allocated.

`Bugfix` | [27a5a146af](https://github.com/onegov/onegov-cloud/commit/27a5a146af055abab06a9411f4cae3f27e29f75c)

##### Fix API doc table formatting.

`Bugfix` | [73c44510bd](https://github.com/onegov/onegov-cloud/commit/73c44510bd5b248eb8060d3803648e29d342a5e3)

### Town6

##### Display context-specific functions on person in the directory

`Feature` | [OGC-731](https://linear.app/onegovcloud/issue/OGC-731) | [e7966c9fde](https://github.com/onegov/onegov-cloud/commit/e7966c9fdeddd1947a3f161894f56993832c8879)

## 2023.3

`2023-01-19` | [38d07a8207...67c7233665](https://github.com/OneGov/onegov-cloud/compare/38d07a8207^...67c7233665)

### Election Day

##### Add map data for 2023.

`Feature` | [OGC-880](https://linear.app/onegovcloud/issue/OGC-880) | [38d07a8207](https://github.com/onegov/onegov-cloud/commit/38d07a820795d6f3ca6da52d0db6de9c02404e89)

##### Add historicized municipality data for 2023.

`Feature` | [OGC-879](https://linear.app/onegovcloud/issue/OGC-879) | [a2279bde3d](https://github.com/onegov/onegov-cloud/commit/a2279bde3d00cc94d64cddcab9e58870e95568ac)

##### Add widgets for election compound part.

`Feature` | [OGC-753](https://linear.app/onegovcloud/issue/OGC-753) | [264a1c5f10](https://github.com/onegov/onegov-cloud/commit/264a1c5f10816b165a0fe00086c1bd0896c777ca)

##### Hide party results and panachage if no real data is present.

`Feature` | [OGC-887](https://linear.app/onegovcloud/issue/OGC-887) | [60a1b1bad0](https://github.com/onegov/onegov-cloud/commit/60a1b1bad04d6ddca7158fb15d8fed60f83e9ae0)

##### Gray out names of inactive colored bars in bar charts.

`Feature` | [OGC-881](https://linear.app/onegovcloud/issue/OGC-881) | [a31b7ee196](https://github.com/onegov/onegov-cloud/commit/a31b7ee1961b36387962a2a5de21b5d7e43e1e74)

##### Fix party result export.

`Bugfix` | [dea9bda2d8](https://github.com/onegov/onegov-cloud/commit/dea9bda2d89faee5eb38557279c0e3ce1b2108ee)

##### Add docstring for update last result change CLI command.

`Bugfix` | [21280e121c](https://github.com/onegov/onegov-cloud/commit/21280e121c33feedfd268e64d1100728d44061fb)

##### Fix party result data file names.

`Bugfix` | [8727e32a5f](https://github.com/onegov/onegov-cloud/commit/8727e32a5f6c975625de302d3a935599bd11ab28)

##### Fixes party export views for majorz elections.

`Bugfix` | [ae48018ced](https://github.com/onegov/onegov-cloud/commit/ae48018ced65157a2eac8b5209de235e87272635)

##### Fix progress not being displayed when there are results available.

`Bugfix` | [OGC-889](https://linear.app/onegovcloud/issue/OGC-889) | [673c5be673](https://github.com/onegov/onegov-cloud/commit/673c5be67329594181c5dfc6a90749b508fe37ac)

### Town 6

##### Fix translation

`Bugfix` | [OGC-878](https://linear.app/onegovcloud/issue/OGC-878) | [40494e58e7](https://github.com/onegov/onegov-cloud/commit/40494e58e7ebca20980cb91c933f32bba6403827)

### Town6

##### Subpage image options

Added options for display of the subpage-images.

`Feature` | [OGC-807](https://linear.app/onegovcloud/issue/OGC-807) | [6748e8914b](https://github.com/onegov/onegov-cloud/commit/6748e8914b91f524c54eef139bd469f10b4b23b4)

##### Fix list display in editor

`Bugfix` | [OGC-865](https://linear.app/onegovcloud/issue/OGC-865) | [bdc2dda8ea](https://github.com/onegov/onegov-cloud/commit/bdc2dda8ea50c0fc020364e68b07a6b3ca9a1001)

## 2023.2

`2023-01-12` | [29a60b94dd...6c08504675](https://github.com/OneGov/onegov-cloud/compare/29a60b94dd^...6c08504675)

### Core

##### Replaces unmaintained psqlparse with pglast

`Bugfix` | [OGC-859](https://linear.app/onegovcloud/issue/OGC-859) | [29a60b94dd](https://github.com/onegov/onegov-cloud/commit/29a60b94ddf73e82462d0afebb3049cd97505711)

##### Adds missing dependency for sphinx autoapi extension.

`Bugfix` | [d315ad5de3](https://github.com/onegov/onegov-cloud/commit/d315ad5de3b31915e942fe42d66d777d216e0eb2)

##### Add missing dependencies for google-chrome-stable.

`Bugfix` | [3501430c85](https://github.com/onegov/onegov-cloud/commit/3501430c850061b5bc25ac14e7613bdff81fc2af)

### Election Day

##### Add embedded tables for party strengths.

`Feature` | [OGC-751](https://linear.app/onegovcloud/issue/OGC-751) | [b3ed54d195](https://github.com/onegov/onegov-cloud/commit/b3ed54d1951c8475e2bbcf79dd65e2ef346cb609)

##### Add election compound widgets for district and superregion tables and maps.

`Feature` | [OGC-869](https://linear.app/onegovcloud/issue/OGC-869) | [94dda1461d](https://github.com/onegov/onegov-cloud/commit/94dda1461dc1f8c7167c143ffe6c1e046850ad81)

##### Add completion widgets.

`Feature` | [OGC-874](https://linear.app/onegovcloud/issue/OGC-874) | [970db99663](https://github.com/onegov/onegov-cloud/commit/970db99663e545c5a5825518612ae8628e6d26b6)

##### Improve description of the has_expats option.

`Feature` | [OGC-736](https://linear.app/onegovcloud/issue/OGC-736) | [9b7ac22def](https://github.com/onegov/onegov-cloud/commit/9b7ac22def4e57588ef307b3a761200809924836)

##### Add party result widgets.

`Feature` | [OGC-812](https://linear.app/onegovcloud/issue/OGC-812) | [eb73d34161](https://github.com/onegov/onegov-cloud/commit/eb73d341610985157eb1ab1c056e08e193bceaf6)

##### Fixes election compound candidates table widget.

`Bugfix` | [ae5131f980](https://github.com/onegov/onegov-cloud/commit/ae5131f98016b7072504b72595fc1fa85e253b27)

##### Fix description of manual completion option.

`Bugfix` | [OGC-873](https://linear.app/onegovcloud/issue/OGC-873) | [c01c5b3f9b](https://github.com/onegov/onegov-cloud/commit/c01c5b3f9b682e5e435383fcc53a5ae6ccf59540)

### Town6

##### Multiline Icon-links

`Feature` | [OGC-843](https://linear.app/onegovcloud/issue/OGC-843) | [411678275c](https://github.com/onegov/onegov-cloud/commit/411678275c822af9486d56f93badd416e692cb06)

##### Design Adjustments

`Feature` | [f50505b293](https://github.com/onegov/onegov-cloud/commit/f50505b293b66f39ab405555ab77fd7c8360a7fc)

### User

##### Add transfer-yubikey CLI command.

`Feature` | [OGC-871](https://linear.app/onegovcloud/issue/OGC-871) | [2ac4d41833](https://github.com/onegov/onegov-cloud/commit/2ac4d41833bb119326935391ceec43b188526a55)

### Wtfs

##### Validate that scan jobs are not submitted after 17:00

`Feature` | [OGC-723](https://linear.app/onegovcloud/issue/OGC-723) | [8018691f35](https://github.com/onegov/onegov-cloud/commit/8018691f353d77f18ffd6beb26b244187703a07e)

## 2023.1

`2023-01-03` | [20d01fd6f0...0f77f7af2f](https://github.com/OneGov/onegov-cloud/compare/20d01fd6f0^...0f77f7af2f)

### Core

##### Sets default file upload limit to 10 MB

`Feature` | [OGC-827](https://linear.app/onegovcloud/issue/OGC-827) | [0b62b13e59](https://github.com/onegov/onegov-cloud/commit/0b62b13e59c4b692d6ba771cae7c0a728862a964)

##### Monkey patches more.webassets to include assets into error views.

Registers webassets_injector_tween after excview_tween_factory so that
assets are included into error views too.

`Bugfix` | [OGC-853](https://linear.app/onegovcloud/issue/OGC-853) | [d5defb78c6](https://github.com/onegov/onegov-cloud/commit/d5defb78c6d1c88de5c600027cdec8a10942bf7a)

### Town

##### Adds publication end date to files

Files are set to private (via hourly cronjob) once the publication end date has been reached.

`Feature` | [OGC-742](https://linear.app/onegovcloud/issue/OGC-742) | [d4fb7e33d0](https://github.com/onegov/onegov-cloud/commit/d4fb7e33d02a03a63ca8ff811c23b6e450e9d0c1)

### Town6

##### Small design adjustments

`Feature` | [1aa84188e2](https://github.com/onegov/onegov-cloud/commit/1aa84188e2639460d2d9571bb63a702a47e8f2b3)

##### Rename more news button

`Feature` | [OGC-820](https://linear.app/onegovcloud/issue/OGC-820) | [5f6b1b70e9](https://github.com/onegov/onegov-cloud/commit/5f6b1b70e9508ca33ffe9ac28ea5b96afcbc86bc)

##### No news in homepage tiles

`Feature` | [OGC-832](https://linear.app/onegovcloud/issue/OGC-832) | [5b623dbc49](https://github.com/onegov/onegov-cloud/commit/5b623dbc498f668a5596865b64d8543ada17fc0a)

##### Add time to event widget on homepage

`Feature` | [OGC-836](https://linear.app/onegovcloud/issue/OGC-836) | [bdf30681da](https://github.com/onegov/onegov-cloud/commit/bdf30681daba33101fc54e5cf932967a56af48aa)

##### Style overview of image sets

`Feature` | [OGC-816](https://linear.app/onegovcloud/issue/OGC-816) | [10aafbf949](https://github.com/onegov/onegov-cloud/commit/10aafbf949908bfd1860480a1a55fe8b60c8f5d6)

##### Add option for image for external link

`Feature` | [OGC-839](https://linear.app/onegovcloud/issue/OGC-839) | [bf0dd341d5](https://github.com/onegov/onegov-cloud/commit/bf0dd341d5bf72c5251116ed1de4b4005daae41c)

##### Credit card button styling

`Bugfix` | [OGC-835](https://linear.app/onegovcloud/issue/OGC-835) | [20d01fd6f0](https://github.com/onegov/onegov-cloud/commit/20d01fd6f0daeb11f0fe9dec02873724f3f67e03)

##### Fix tags field styling

`Bugfix` | [OGC-617](https://linear.app/onegovcloud/issue/OGC-617) | [147a273dfd](https://github.com/onegov/onegov-cloud/commit/147a273dfd951b8acc39c5b7f039bf0a58f2c797)

##### Don't break title beneath icon

`Bugfix` | [OGC-843](https://linear.app/onegovcloud/issue/OGC-843) | [6982bd9e2f](https://github.com/onegov/onegov-cloud/commit/6982bd9e2f805f3557503292fedc6a2a75a09ad0)

##### Fix upload image style error

`Bugfix` | [OGC-621](https://linear.app/onegovcloud/issue/OGC-621) | [a87e0ee579](https://github.com/onegov/onegov-cloud/commit/a87e0ee5794be6cdb17e52b01b43ba5b255a065a)

##### Fix html rendering in newsletters/new view

`Bugfix` | [OGC-734](https://linear.app/onegovcloud/issue/OGC-734) | [8a3b755b12](https://github.com/onegov/onegov-cloud/commit/8a3b755b12d8ca0a99c665ab9471f66d78c2d747)

## 2022.57

`2022-12-14` | [14496f2d9c...ee3b7e737b](https://github.com/OneGov/onegov-cloud/compare/14496f2d9c^...ee3b7e737b)

### Election Day

##### Remove obsolete migration command.

`Other` | [OGC-703](https://linear.app/onegovcloud/issue/OGC-703) | [14496f2d9c](https://github.com/onegov/onegov-cloud/commit/14496f2d9c11fed5066a4d77443e11fa6c4c4b84)

##### Only add years to labels in horizontal party strength bar charts in case of historical data.

`Bugfix` | [OGC-834](https://linear.app/onegovcloud/issue/OGC-834) | [89bdd2aa39](https://github.com/onegov/onegov-cloud/commit/89bdd2aa39d417c3e678937b5b79d3408645cf12)

### Town6

##### Homepage tiles pretty hover effect

`Feature` | [OGC-771](https://linear.app/onegovcloud/issue/OGC-771) | [b53d9287ac](https://github.com/onegov/onegov-cloud/commit/b53d9287acf5d52721d5fab28ca7fb3b9da8c42d)

##### Random Video

Multiple Videos can now be added and one will randomly be chosen

`Feature` | [OGC-819](https://linear.app/onegovcloud/issue/OGC-819) | [bd18460e17](https://github.com/onegov/onegov-cloud/commit/bd18460e17f5995fa8cfeacc56dc0a3a4643c0a8)

##### Small design adjustments

`Feature` | [ca490622f2](https://github.com/onegov/onegov-cloud/commit/ca490622f23063432d09664f49748793c58bb577)

##### Fix search bar suggestions

`Bugfix` | [OGC-803](https://linear.app/onegovcloud/issue/OGC-803) | [ec9ab0225e](https://github.com/onegov/onegov-cloud/commit/ec9ab0225ebff8e71a4c83c25246d6fa9e5f0b66)

##### Fix contact panel html

Use paragraphs and lists instead of only lists

`Bugfix` | [OGC-815](https://linear.app/onegovcloud/issue/OGC-815) | [42d1cdfa1d](https://github.com/onegov/onegov-cloud/commit/42d1cdfa1d1192d28a7a2df25ccd66d4b94ff5c0)

## 2022.56

`2022-12-13` | [8edea2fdcc...6ab36c0639](https://github.com/OneGov/onegov-cloud/compare/8edea2fdcc^...6ab36c0639)

### Directory

##### Fix key format problem

`Bugfix` | [OGC-814](https://linear.app/onegovcloud/issue/OGC-814) | [6042867716](https://github.com/onegov/onegov-cloud/commit/60428677168e7f9cfcf35abd692aa1118fc29476)

### Election Day

##### Enable voters counts for proporz elections.

`Feature` | [OGC-353](https://linear.app/onegovcloud/issue/OGC-353) | [46780ffb4f](https://github.com/onegov/onegov-cloud/commit/46780ffb4fbdcc1dd9b942289b78eff82ff428df)

##### Add historical party results.

`Feature` | [OGC-703](https://linear.app/onegovcloud/issue/OGC-703) | [40cb21f883](https://github.com/onegov/onegov-cloud/commit/40cb21f88345c8fd954ce6ffeeed78cea96a8950)

##### Show percentages instead of votes or voters counts in horziontal party strengths bar chart when having historical data.

`Feature` | [OGC-828](https://linear.app/onegovcloud/issue/OGC-828) | [58a4878787](https://github.com/onegov/onegov-cloud/commit/58a4878787cf9ecba0e5010c861cbc707283fc7e)

##### Remove obsolete migration step.

`Other` | [OGC-768](https://linear.app/onegovcloud/issue/OGC-768) | [8edea2fdcc](https://github.com/onegov/onegov-cloud/commit/8edea2fdcc9881bc4d8e59fcd90875a31d36ac17)

##### Drop owner columns of party and panachage results.

`Other` | [OGC-768](https://linear.app/onegovcloud/issue/OGC-768) | [25f9dfee81](https://github.com/onegov/onegov-cloud/commit/25f9dfee81db2a61810de6e5b63b388141231207)

##### Fix check for consistent total votes in party result import for results with multiple domains.

`Bugfix` | [cf8ea1cda0](https://github.com/onegov/onegov-cloud/commit/cf8ea1cda0bc3686e441401719f0632eacc79e25)

### Town6

##### Show Hashtags and year only if they exist.

`Feature` | [OGC-808](https://linear.app/onegovcloud/issue/OGC-808) | [8fc6ae7ef8](https://github.com/onegov/onegov-cloud/commit/8fc6ae7ef8c45f80f7d324abc74ac3eacb204438)

##### Fix sidebar news

`Bugfix` | [OGC-811](https://linear.app/onegovcloud/issue/OGC-811) | [db933a641b](https://github.com/onegov/onegov-cloud/commit/db933a641b02a9ded958aca18d3ce22b427e5d8b)

## 2022.55

`2022-12-07` | [da8adc1346...ce0bf0aac4](https://github.com/OneGov/onegov-cloud/compare/da8adc1346^...ce0bf0aac4)

### Ballot

##### Add foreign keys to party and panachage results.

`Bugfix` | [OGC-768](https://linear.app/onegovcloud/issue/OGC-768) | [6639df7046](https://github.com/onegov/onegov-cloud/commit/6639df7046aa1376071c3868ae7d8900b4c18c7b)

### Directory

##### Fix directory error

`Bugfix` | [OGC-783](https://linear.app/onegovcloud/issue/OGC-783) | [4d0b84299f](https://github.com/onegov/onegov-cloud/commit/4d0b84299ffedc99e8f895c4aeaa476451394688)

### Election Day

##### Remove obsolete party color column.

`Feature` | [OGC-676](https://linear.app/onegovcloud/issue/OGC-676) | [c6f8d7a351](https://github.com/onegov/onegov-cloud/commit/c6f8d7a351012c1a0fab5a41b579718098b1b133)

##### Add views for superregions.

`Feature` | [OGC-702](https://linear.app/onegovcloud/issue/OGC-702) | [d2f13fadb4](https://github.com/onegov/onegov-cloud/commit/d2f13fadb411041027a462671fd26478b15ed02e)

##### Add entity filter to list views.

`Feature` | [OGC-707](https://linear.app/onegovcloud/issue/OGC-707) | [3cab849cd6](https://github.com/onegov/onegov-cloud/commit/3cab849cd6512fe19e381e12731ece5f5b98147a)

##### Add entity filter to candidates views.

`Feature` | [OGC-706](https://linear.app/onegovcloud/issue/OGC-706) | [492ca66202](https://github.com/onegov/onegov-cloud/commit/492ca66202864899493f5be00b5c9552105540a8)

##### Add party views configuration options to elections.

`Feature` | [OGC-765](https://linear.app/onegovcloud/issue/OGC-765) | [7174ff013a](https://github.com/onegov/onegov-cloud/commit/7174ff013a3b0e4c3b1d3752f4228c59de174bb1)

##### Update voters count documentation.

`Feature` | [OGC-767](https://linear.app/onegovcloud/issue/OGC-767) | [983fdd465d](https://github.com/onegov/onegov-cloud/commit/983fdd465d8cef6da9da60fb1f237377f2183a8f)

##### Rename list panachage result columns.

`Feature` | [OGC-766](https://linear.app/onegovcloud/issue/OGC-766) | [9a6913102f](https://github.com/onegov/onegov-cloud/commit/9a6913102f1eacb655328a6cd0a58523c23db051)

##### Remove party domain data migration command.

`Other` | [OGC-709](https://linear.app/onegovcloud/issue/OGC-709) | [da8adc1346](https://github.com/onegov/onegov-cloud/commit/da8adc1346077e2b14c8610c0d2b827ab7a3c77a)

##### Shorten filename length for csv and json

`Bugfix` | [OGC-689](https://linear.app/onegovcloud/issue/OGC-689) | [4ecb615e44](https://github.com/onegov/onegov-cloud/commit/4ecb615e44a01591044b31d0314e6572ac76e552)

### Town6

##### Mobile optimizations

`Feature` | [OGC-756](https://linear.app/onegovcloud/issue/OGC-756) | [b25607054c](https://github.com/onegov/onegov-cloud/commit/b25607054c42048395aec00bc7a5fb519446dbcc)

##### Design adjustments

`Feature` | [OGC-682](https://linear.app/onegovcloud/issue/OGC-682) | [43f62e2dcc](https://github.com/onegov/onegov-cloud/commit/43f62e2dcc7b38cd08de48730b7f63d49b27cc11)

##### Option to hide "submit own event"

`Feature` | [OGC-779](https://linear.app/onegovcloud/issue/OGC-779) | [783abfeefe](https://github.com/onegov/onegov-cloud/commit/783abfeefead47010f30fcf1923d987b00c06e3b)

##### Add lead in lists on topic

`Bugfix` | [OGC-801](https://linear.app/onegovcloud/issue/OGC-801) | [43fb79ed23](https://github.com/onegov/onegov-cloud/commit/43fb79ed237b5361932a72b3adc22a864d142822)

## 2022.54

`2022-11-30` | [5c9db5044a...76ac3712ea](https://github.com/OneGov/onegov-cloud/compare/5c9db5044a^...76ac3712ea)

### Election Day

##### Add list and party colors to internal import formats.

Colors are now consistently stored in the meta of elections or the election compounds.

`Feature` | [OGC-676](https://linear.app/onegovcloud/issue/OGC-676) | [a8b3326c50](https://github.com/onegov/onegov-cloud/commit/a8b3326c50fd608635d82b3f36fd30406ef41f2f)

##### Add domains to party results.

This allows to store party results for subdomains such as superregional data in election compounds.

`Feature` | [OGC-709](https://linear.app/onegovcloud/issue/OGC-709) | [820cc8f1e3](https://github.com/onegov/onegov-cloud/commit/820cc8f1e37ea86f97227d26d8cffe61dd714744)

##### Add an option to shop party strength diagrams horizontally.

`Feature` | [OGC-708](https://linear.app/onegovcloud/issue/OGC-708) | [2b9fd9f28b](https://github.com/onegov/onegov-cloud/commit/2b9fd9f28bebd8776f1b77fa11d118943da68c67)

##### Export all votes in one flat csv (additionally)

`Feature` | [OGC-691](https://linear.app/onegovcloud/issue/OGC-691) | [10e32184c9](https://github.com/onegov/onegov-cloud/commit/10e32184c9539662abb10b33df5f109af0f8249d)

##### Fix various color issues.

`Bugfix` | [OGC-676](https://linear.app/onegovcloud/issue/OGC-676) | [a695060764](https://github.com/onegov/onegov-cloud/commit/a6950607648ddddfa9ae85e66233f1efb82c14d4)

##### Select only votes that have been counted and have results

`Bugfix` | [OGC-690](https://linear.app/onegovcloud/issue/OGC-690) | [3321910dec](https://github.com/onegov/onegov-cloud/commit/3321910decc77e4c3b1288f5c4817d3acd8664b6)

### Form

##### Fix Formcode for dependent fields with price

Form: Fix Formcode for dependent fields with price

`Bugfix` | [OGC-730](https://linear.app/onegovcloud/issue/OGC-730) | [0fa93f9588](https://github.com/onegov/onegov-cloud/commit/0fa93f958881cf6fad7e792f32e907ce82b4b13a)

### Town 6

##### Various Design improvements on Homepage

`Feature` | [OGC-748](https://linear.app/onegovcloud/issue/OGC-748) | [b2bdb09586](https://github.com/onegov/onegov-cloud/commit/b2bdb0958647b651d32dacd1723b4595ed2886aa)

### Town6

##### Change video resolution according to Viewport-size

`Feature` | [OGC-678](https://linear.app/onegovcloud/issue/OGC-678) | [5c9db5044a](https://github.com/onegov/onegov-cloud/commit/5c9db5044aea09cdb6f4561683ff24a4e77f1336)

##### Option to display map pins on directory overview with numbers

`Feature` | [OGC-654](https://linear.app/onegovcloud/issue/OGC-654) | [05e6ab6c06](https://github.com/onegov/onegov-cloud/commit/05e6ab6c06cf220b131f5d87a538eda5ea3ff37b)

##### Add option for images on subpages

`Feature` | [OGC-674](https://linear.app/onegovcloud/issue/OGC-674) | [e57fd1c690](https://github.com/onegov/onegov-cloud/commit/e57fd1c6901b5517d0bfdd296afbc4b5f504e2da)

##### Add new Font

`Feature` | [OGC-738](https://linear.app/onegovcloud/issue/OGC-738) | [1de21f4a5f](https://github.com/onegov/onegov-cloud/commit/1de21f4a5f9456b6789846e0876920e219b4cafc)

##### Make Cancel Button work for safari too

`Bugfix` | [OGC-695](https://linear.app/onegovcloud/issue/OGC-695) | [7eee02402e](https://github.com/onegov/onegov-cloud/commit/7eee02402e14985fb2b3eb292aeaa88a3e7cfba3)

##### Align table header to the left

`Bugfix` | [OGC-737](https://linear.app/onegovcloud/issue/OGC-737) | [2b49b18a55](https://github.com/onegov/onegov-cloud/commit/2b49b18a55928f8bc7b2f269276a8e8ff1890185)

### Winterthur

##### Remove urls and files from directory search

`Bugfix` | [OGC-422](https://linear.app/onegovcloud/issue/OGC-422) | [3a608ae372](https://github.com/onegov/onegov-cloud/commit/3a608ae372ff31687544e82ba0375cbb829e4cdc)

## 2022.53

`2022-11-16` | [c4b89f4698...6fb3fc3e3e](https://github.com/OneGov/onegov-cloud/compare/c4b89f4698^...6fb3fc3e3e)

### Event

##### Fix icalendar tests

`Bugfix` | [ff15e573d8](https://github.com/onegov/onegov-cloud/commit/ff15e573d8bb67a59f8120dd9836af8a12c21f19)

### Gis

##### Add zoom levels for swiss admin map

`Feature` | [OGC-694](https://linear.app/onegovcloud/issue/OGC-694) | [eefba89962](https://github.com/onegov/onegov-cloud/commit/eefba89962a70b098ad91ac6bebb74e7dd4ac7ca)

## 2022.52

`2022-11-03` | [8e75e5483a...f55f16d53e](https://github.com/OneGov/onegov-cloud/compare/8e75e5483a^...f55f16d53e)

### Election Day

##### Add provisional data for 2023.

`Feature` | [OGC-237](https://linear.app/onegovcloud/issue/OGC-237) | [69e2daf81e](https://github.com/onegov/onegov-cloud/commit/69e2daf81e8ea41da62863b8038e0d1a95324025)

## 2022.51

`2022-11-02` | [27e4250d99...2a7b5c742b](https://github.com/OneGov/onegov-cloud/compare/27e4250d99^...2a7b5c742b)

### Core

##### Use signed redirects for locales.

`Feature` | [OGC-671](https://linear.app/onegovcloud/issue/OGC-671) | [38f3fd0438](https://github.com/onegov/onegov-cloud/commit/38f3fd04385790408872fc2bb32c40fd87aa7526)

##### Fixes missing dependency.

`Bugfix` | [OGC-681](https://linear.app/onegovcloud/issue/OGC-681) | [9d9f17ab6a](https://github.com/onegov/onegov-cloud/commit/9d9f17ab6a2351582fbbb173a2ee48f448c517f6)

### Election Day

##### Update translations.

`Feature` | [27e4250d99](https://github.com/onegov/onegov-cloud/commit/27e4250d99124c905286d76c4a709e05f8b08616)

##### Disable iframes in authentication and manage views.

Also fixes connect source setting.

LING: OGC-669

`Feature` | [895ab08f36](https://github.com/onegov/onegov-cloud/commit/895ab08f36e24f27757d1f84f029c84ddba41d74)

##### Honeypot info for screen readers

`Feature` | [OGC-560](https://linear.app/onegovcloud/issue/OGC-560) | [d1bd564748](https://github.com/onegov/onegov-cloud/commit/d1bd564748e928977774e2a0d704c6a972df4290)

##### Fix typo.

`Bugfix.` | [45e0759e8d](https://github.com/onegov/onegov-cloud/commit/45e0759e8de8759864aa288d75c4131c3bdc4214)

##### Make dropdown function visible for screen reader

`Bugfix` | [OGC-548](https://linear.app/onegovcloud/issue/OGC-548) | [4e870c9a10](https://github.com/onegov/onegov-cloud/commit/4e870c9a1087969cadeb32216497e860f162b14d)

### Org

##### Add Swisstopo and aerial Map

`Feature` | [OGC-632](https://linear.app/onegovcloud/issue/OGC-632) | [d68b4024a8](https://github.com/onegov/onegov-cloud/commit/d68b4024a8086eb23af193cf7c55f17250a3b0c2)

##### Link for map-bs if map-bs is selected in settings

`Feature` | [OGC-634](https://linear.app/onegovcloud/issue/OGC-634) | [f82e1fd75c](https://github.com/onegov/onegov-cloud/commit/f82e1fd75c71a891567c2d0c7fa9fd75f98b3003)

### Town 6

##### Rename quicklinks

`Feature` | [OGC-581](https://linear.app/onegovcloud/issue/OGC-581) | [8d469c99b3](https://github.com/onegov/onegov-cloud/commit/8d469c99b3f7738855cc7da5c90a9d7245111aba)

##### Display Contact Info correctly

`Bugfix` | [OGC-648](https://linear.app/onegovcloud/issue/OGC-648) | [11dbe043ea](https://github.com/onegov/onegov-cloud/commit/11dbe043ea61f15df58c86cdb8f12354e26e2175)

### Town6

##### Add a cancel link on forms

`Feature` | [OGC-582](https://linear.app/onegovcloud/issue/OGC-582) | [1dc1d164e4](https://github.com/onegov/onegov-cloud/commit/1dc1d164e4923336ca82d7bbf3d3a9f6ede73b72)

##### Remove button class from edit link

`Feature` | [OGC-673](https://linear.app/onegovcloud/issue/OGC-673) | [44ad387a63](https://github.com/onegov/onegov-cloud/commit/44ad387a6309363f5ee2e0bcf155b14df976d7a7)

##### Add an offset for the toolbar

`Bugfix` | [OGC-672](https://linear.app/onegovcloud/issue/OGC-672) | [5b1e9b347e](https://github.com/onegov/onegov-cloud/commit/5b1e9b347e64d37e298f4139413f5e73ee360ab4)

##### Fixed Typo

`Bugfix` | [OGC-679](https://linear.app/onegovcloud/issue/OGC-679) | [f9dbb3a226](https://github.com/onegov/onegov-cloud/commit/f9dbb3a226bc67226371dc59291775f86b69e92e)

## 2022.50

`2022-10-18` | [882bf8e010...f016c97cc8](https://github.com/OneGov/onegov-cloud/compare/882bf8e010^...f016c97cc8)

### Agency

##### Add information for changes form

`Feature` | [OGC-650](https://linear.app/onegovcloud/issue/OGC-650) | [c0a04a906d](https://github.com/onegov/onegov-cloud/commit/c0a04a906d0dd7af513f92f85648f954a4cc5fff)

##### Delete reference on non-existant address fields

`Bugfix` | [OGC-645](https://linear.app/onegovcloud/issue/OGC-645) | [f4d2fd08c2](https://github.com/onegov/onegov-cloud/commit/f4d2fd08c20bac393533e55ab0837d1a98940364)

### Election Day

##### Export all votes and elections of all time.

`Feature` | [OGC-483](https://linear.app/onegovcloud/issue/OGC-483) | [882bf8e010](https://github.com/onegov/onegov-cloud/commit/882bf8e0100dcd7bcf1e13386ab8531c48677033)

##### Allow alternative expats column name.

`Feature` | [404e98a5e5](https://github.com/onegov/onegov-cloud/commit/404e98a5e5c3b236636ea920f3c60a434bb73055)

##### Color contrasts

`Feature` | [OGC-556](https://linear.app/onegovcloud/issue/OGC-556) | [77ce7da75c](https://github.com/onegov/onegov-cloud/commit/77ce7da75c90a4cc5c0557a4c046389a84d6fbc1)

##### Add white background to terms of usage image

`Feature` | [OGC-538](https://linear.app/onegovcloud/issue/OGC-538) | [23a89290b4](https://github.com/onegov/onegov-cloud/commit/23a89290b47e6fb19ec6e489d66b4aa7fd9cdf14)

##### Fix HTML Errors

`Bugfix` | [OGC-562](https://linear.app/onegovcloud/issue/OGC-562) | [aa9ca0ca1b](https://github.com/onegov/onegov-cloud/commit/aa9ca0ca1bcaaafbce8fff7f174998566f65ad86)

##### Fix broken up definition list

`Bugfix` | [OGC-552](https://linear.app/onegovcloud/issue/OGC-552) | [05705527e2](https://github.com/onegov/onegov-cloud/commit/05705527e2e89bad6a25c7c44524ba2340a306f7)

### Feriennet

##### Fix age check options being escaped.

`Bugfix` | [PRO-1094](https://linear.app/projuventute/issue/PRO-1094) | [0e58e5755c](https://github.com/onegov/onegov-cloud/commit/0e58e5755c79b2280d3712c02f08db1967b455e3)

### Org

##### Fix signed class rendering.

`Bugfix` | [94ea74c201](https://github.com/onegov/onegov-cloud/commit/94ea74c20182cd0693cae7a097c635156aa9aea5)

##### Fix label nesting problem

Fixed problem with nested labels on multiple choice fields in forms

`Bugfix` | [OGC-554](https://linear.app/onegovcloud/issue/OGC-554) | [e4a799e5c0](https://github.com/onegov/onegov-cloud/commit/e4a799e5c0b3eab6be8c1b5766c996987e00e0fe)

### Town6

##### Display contact information correctly

`Bugfix` | [OGC-648](https://linear.app/onegovcloud/issue/OGC-648) | [9fe7bd211a](https://github.com/onegov/onegov-cloud/commit/9fe7bd211add87148fd0ea88965d2cf487121c5e)

##### Homepage widget adjustments

`Bugfix` | [cc30098a80](https://github.com/onegov/onegov-cloud/commit/cc30098a80f5ba810f143b8c78db825d3c0d95fb)

## 2022.49

`2022-10-04` | [c6b209efef...173144825b](https://github.com/OneGov/onegov-cloud/compare/c6b209efef^...173144825b)

### Agency

##### Remove address fields below map

`Bugfix` | [OGC-241](https://linear.app/onegovcloud/issue/OGC-241) | [47fc126888](https://github.com/onegov/onegov-cloud/commit/47fc126888261ac45530de0b5e5a42935cc87b03)

### Api

##### Return 404s.

`Feature` | [OGC-636](https://linear.app/onegovcloud/issue/OGC-636) | [7791975102](https://github.com/onegov/onegov-cloud/commit/7791975102626db0e56ee93fe0d70d21ca57350d)

##### Catch type missmatches when querying API endpoint items.

`Bugfix` | [OGC-636](https://linear.app/onegovcloud/issue/OGC-636) | [65185cec2e](https://github.com/onegov/onegov-cloud/commit/65185cec2e773d428cf1cc94d8816a57891627b9)

### Election Day

##### Order archive descending.

`Feature` | [OGC-627](https://linear.app/onegovcloud/issue/OGC-627) | [d597f8e32c](https://github.com/onegov/onegov-cloud/commit/d597f8e32c71a95359e78eb04d229ba3b3ed9ca5)

##### Prevent double clicks on forms.

`Feature` | [OGC-629](https://linear.app/onegovcloud/issue/OGC-629) | [92b5d38ea9](https://github.com/onegov/onegov-cloud/commit/92b5d38ea9e7bdf7b5c4cd1fd01743945471549a)

##### Improve notification form hints.

`Feature` | [OGC-628](https://linear.app/onegovcloud/issue/OGC-628) | [dfaef0d9d3](https://github.com/onegov/onegov-cloud/commit/dfaef0d9d39f77dcb8e1433f3824f0fb13916477)

##### Disable autocomplete on honeypot fields.

`Bugfix` | [OGC-633](https://linear.app/onegovcloud/issue/OGC-633) | [38b276bc6e](https://github.com/onegov/onegov-cloud/commit/38b276bc6e2d5ecbca6ecc86533656c2eebf951f)

### Feriennet

##### Avoid throwing an error when displaying QR bills with invalid zip codes.

`Feature` | [PRO-1083](https://linear.app/projuventute/issue/PRO-1083) | [c02ef1e5af](https://github.com/onegov/onegov-cloud/commit/c02ef1e5af8b1363e58ce23f5d0821abb0befda3)

### Form

##### Harden formcode-fields.

`Other` | [OGC-616](https://linear.app/onegovcloud/issue/OGC-616) | [c6b209efef](https://github.com/onegov/onegov-cloud/commit/c6b209efefb95e0541b93d5927c1159e693a7617)

### Org

##### Add header links option

`Feature` | [OGC-581](https://linear.app/onegovcloud/issue/OGC-581) | [da3d6eb22a](https://github.com/onegov/onegov-cloud/commit/da3d6eb22adeecbb5aa8b2b31b4eb46d420e8fef)

##### Add option for linking announcement

`Feature` | [OGC-159](https://linear.app/onegovcloud/issue/OGC-159) | [2996c3f2a7](https://github.com/onegov/onegov-cloud/commit/2996c3f2a75c9ce49e04777e20b1ed2daa4c8d22)

##### Check if resource exists first

`Bugfix` | [OGC-575](https://linear.app/onegovcloud/issue/OGC-575) | [d007384d89](https://github.com/onegov/onegov-cloud/commit/d007384d890888d51ff4c1b441c1bd69bc7d39a2)

##### Check if notification-type keys exist before checking value

`Bugfix` | [OGC-264](https://linear.app/onegovcloud/issue/OGC-264) | [6848f7c90e](https://github.com/onegov/onegov-cloud/commit/6848f7c90ed0eac637365f2ad15b9c5603f3f510)

##### Switch out .xlsx library to produce valid excel file.

`Bugfix` | [OGC-574](https://linear.app/onegovcloud/issue/OGC-574) | [6e4ba08df7](https://github.com/onegov/onegov-cloud/commit/6e4ba08df7fb4f9c83a17f3b196577a7bb0495d5)

### Town6

##### Add optional news image

`Feature` | [OGC-511](https://linear.app/onegovcloud/issue/OGC-511) | [5c58386cbd](https://github.com/onegov/onegov-cloud/commit/5c58386cbd21a5e4a1596ebd50457dcac79c5745)

## 2022.48

`2022-09-21` | [31de20c003...97aa3fe995](https://github.com/OneGov/onegov-cloud/compare/31de20c003^...97aa3fe995)

### Core

##### Catch no matching schemas in transfer command.

Also improve help texts.

`Feature` | [OGC-614](https://linear.app/onegovcloud/issue/OGC-614) | [53a304ad9b](https://github.com/onegov/onegov-cloud/commit/53a304ad9b52967dda8e3414a28473e9517c0f39)

### Election Day

##### Center skip links

`Feature` | [OGC-558](https://linear.app/onegovcloud/issue/OGC-558) | [31de20c003](https://github.com/onegov/onegov-cloud/commit/31de20c0037bef6a0b07a8aa66b8e45aeb5b94d2)

##### Avoid using an empty selector

`Bugfix` | [OGC-561](https://linear.app/onegovcloud/issue/OGC-561) | [30ea5adfbe](https://github.com/onegov/onegov-cloud/commit/30ea5adfbe0e154bd79cf7817ba32773cddc6a58)

### Feriennet

##### Replace concordia banners.

`Other` | [PRO-1082](https://linear.app/projuventute/issue/PRO-1082) | [25ebc75d2c](https://github.com/onegov/onegov-cloud/commit/25ebc75d2c021dc1f5077799943da5a2a469a5bb)

##### Fix donation form providing invalid selection when custom donation amounts configuration is empty.

`Bugfix` | [OGC-608](https://linear.app/onegovcloud/issue/OGC-608) | [1aba0a9b11](https://github.com/onegov/onegov-cloud/commit/1aba0a9b11ac92a3fbab5d844296fccb495ff97e)

### Org

##### Ability to export several reservations at once

`Feature` | [OGC-574](https://linear.app/onegovcloud/issue/OGC-574) | [b7e9efcc5b](https://github.com/onegov/onegov-cloud/commit/b7e9efcc5b7b0fb3fe573d96ff1964e169d37c9a)

##### Fully integrate Geo-BS

`Feature` | [OGC-241](https://linear.app/onegovcloud/issue/OGC-241) | [ba82b41bfa](https://github.com/onegov/onegov-cloud/commit/ba82b41bfa95f166071f3a60e34bd2dd2756d3b3)

### Swissvotes

##### Fixes wildcard search.

`Bugfix` | [OGC-609](https://linear.app/onegovcloud/issue/OGC-609) | [eba3224818](https://github.com/onegov/onegov-cloud/commit/eba32248189fd1393e7851bcd108112cfa56f50f)

### Town6

##### Add icon widget

`Feature` | [OGC-579](https://linear.app/onegovcloud/issue/OGC-579) | [938e99fb75](https://github.com/onegov/onegov-cloud/commit/938e99fb7598a9070f670a5cd9679165bff7b6d5)

##### Add option to receive a notification for new reservations

`Feature` | [OGC-575](https://linear.app/onegovcloud/issue/OGC-575) | [c08e159593](https://github.com/onegov/onegov-cloud/commit/c08e1595937731c91ef904c4ab3d6eaa86c0df59)

##### Add testimonial widget

`Feature` | [OGC-580](https://linear.app/onegovcloud/issue/OGC-580) | [e4dc9ed6ab](https://github.com/onegov/onegov-cloud/commit/e4dc9ed6ab1fb9fd15367f418e41e1e5ebc7a492)

##### Fix inconsistencies in setting option names

`Bugfix` | [OGC-504](https://linear.app/onegovcloud/issue/OGC-504) | [a6f818ae1d](https://github.com/onegov/onegov-cloud/commit/a6f818ae1dbe72edf311fe2d4b123ea32c9cc43e)

##### Remove unused tile image option in settings

`Bugfix` | [OGC-592](https://linear.app/onegovcloud/issue/OGC-592) | [9c4de71ac3](https://github.com/onegov/onegov-cloud/commit/9c4de71ac3aac6efcbe4cda6e9c020aef63d3a95)

### Winterthur

##### Fixes flaky test.

`Bugfix` | [ba468fc43d](https://github.com/onegov/onegov-cloud/commit/ba468fc43d98f668dbca7a6bb0e7b6b5a3e623fa)

