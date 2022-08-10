# Changes

## 2022.41

`2022-08-10` | [ad737f8401...fca971342e](https://github.com/OneGov/onegov-cloud/compare/ad737f8401^...fca971342e)

### Core

##### Improve compatibility with SQLAlchemy 1.4.

Updates adjacency lists used by page and gazette.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [6342638855](https://github.com/onegov/onegov-cloud/commit/634263885533fa645d6af959663c195d265c742d)

##### Makes sure Request.application_url strips X_VHM_ROOT

`Bugfix` | [c8d5819e4e](https://github.com/onegov/onegov-cloud/commit/c8d5819e4e1dba9c312f56560c9727f244ead695)

### Election Day

##### Add seat allocation view.

`Feature` | [OGC-487](https://linear.app/onegovcloud/issue/OGC-487) | [2aab61c554](https://github.com/onegov/onegov-cloud/commit/2aab61c5545c49c82047ad6681013589118fde8c)

##### Add apportionment PDFs to election compounds.

`Feature` | [OGC-490](https://linear.app/onegovcloud/issue/OGC-490) | [0f1e8eeb5e](https://github.com/onegov/onegov-cloud/commit/0f1e8eeb5e4e3f71f9e27d12ae196cf38e2ff7ef)

##### Add elected candidates statistics to election compounds.

`Feature` | [OGC-489](https://linear.app/onegovcloud/issue/OGC-489) | [9f9f03f7d2](https://github.com/onegov/onegov-cloud/commit/9f9f03f7d2f25fefe893e42a07a8c7dac6d819ac)

##### Add "no results" text and layout changes

`Feature` | [OGC-282](https://linear.app/onegovcloud/issue/OGC-282) | [2bb2c87a8b](https://github.com/onegov/onegov-cloud/commit/2bb2c87a8bf72181f2cab25e031ed82269c5f013)

##### Fixes election compound statistics showing wrong aggregation level.

Also adds statistics to PDF.

`Bugfix` | [OGC-531](https://linear.app/onegovcloud/issue/OGC-531) | [ff9d88102e](https://github.com/onegov/onegov-cloud/commit/ff9d88102ec923d5a8e819ceb25b8c56dbf82eb5)

### Feriennet

##### Filter for active period and add phase info

`Feature` | [OGC-991](https://linear.app/onegovcloud/issue/OGC-991) | [fca971342e](https://github.com/onegov/onegov-cloud/commit/fca971342eebb1958aaedfe646eca12dd6e010da)

### Org

##### Add option for external resources

It is now possible to add external resources as links.

`Feature` | [OGC-354](https://linear.app/onegovcloud/issue/OGC-354) | [943ea1b337](https://github.com/onegov/onegov-cloud/commit/943ea1b3371526062bffbe15d27b4429b6dfda6c)

##### Fixes AttributeError in Find Your Spot form validation

`Bugfix` | [84299db8c6](https://github.com/onegov/onegov-cloud/commit/84299db8c66be71b6c99b612ff6e573b6265dd9d)

##### Handles DST/ST time transitions better when creating reservations

`Bugfix` | [OGC-466](https://linear.app/onegovcloud/issue/OGC-466) | [9b9a0e6f82](https://github.com/onegov/onegov-cloud/commit/9b9a0e6f826fe5dcf3acf0cda89d3caaceeac61a)

##### Cleans up some additional DST related issues

`Bugfix` | [OGC-466](https://linear.app/onegovcloud/issue/OGC-466) | [7a373969fe](https://github.com/onegov/onegov-cloud/commit/7a373969fee568d274e2bce4d69fd2e255de2bbb)

### Town6

##### Search bar in header

The search bar can now directly be used in the header

`Feature` | [OGC-80](https://linear.app/onegovcloud/issue/OGC-80) | [e05a65d2d5](https://github.com/onegov/onegov-cloud/commit/e05a65d2d57c6802a9be056f720ccf37361f60f6)

##### Add title homepage widget

`Feature` | [OGC-521](https://linear.app/onegovcloud/issue/OGC-521) | [dfe5dd95c7](https://github.com/onegov/onegov-cloud/commit/dfe5dd95c7faa964d929187f8b564518abe23a86)

##### Remove external link icons from partner widget and footer

`Bugfix` | [OGC-522](https://linear.app/onegovcloud/issue/OGC-522) | [d3d71d82ed](https://github.com/onegov/onegov-cloud/commit/d3d71d82ed580fb9b51b7c37caf7dc62b959bf2a)

### User

##### Adds test to ensure CI fails if container is missing xmlsec1

`Bugfix` | [ad737f8401](https://github.com/onegov/onegov-cloud/commit/ad737f84015fbab241fd745b858c8677fa2e141a)

## 2022.40

`2022-07-27` | [373f3fe922...e2512b7706](https://github.com/OneGov/onegov-cloud/compare/373f3fe922^...e2512b7706)

### User

##### Adds SAML2 authentication provider

`Feature` | [OGC-430](https://linear.app/onegovcloud/issue/OGC-430) | [373f3fe922](https://github.com/onegov/onegov-cloud/commit/373f3fe9224ddac7a031593a35deb31c270fe808)

## 2022.39

`2022-07-20` | [7f482cb1e0...3914d75524](https://github.com/OneGov/onegov-cloud/compare/7f482cb1e0^...3914d75524)

### Agency

##### Add optional immediate notification for AGN and PER tickets

`Feature` | [OGC-480](https://linear.app/onegovcloud/issue/OGC-480) | [2061ed3588](https://github.com/onegov/onegov-cloud/commit/2061ed35880f867d8c7427093c0be0673530bf22)

### Org

##### Optionally allows members to view resource occupancy

`Feature` | [OGC-482](https://linear.app/onegovcloud/issue/OGC-482) | [c1cc1f4f4e](https://github.com/onegov/onegov-cloud/commit/c1cc1f4f4e45e181d6812bbe1e07d95498c92807)

##### Excludes invisible allocations in find my spot search results

`Bugfix` | [7f482cb1e0](https://github.com/onegov/onegov-cloud/commit/7f482cb1e09f84a510e85a6aad79c05aff6b27ee)

## 2022.38

`2022-07-13` | [489484c4d7...31f79338d8](https://github.com/OneGov/onegov-cloud/compare/489484c4d7^...31f79338d8)

### Org

##### Add find your spot to search across all rooms in a category

`Feature` | [OGC-328](https://linear.app/onegovcloud/issue/OGC-328) | [87243827ad](https://github.com/onegov/onegov-cloud/commit/87243827ad0dcc655921580d0aa583742a098467)

##### Fixes typo in translation

`Bugfix` | [27b9816e79](https://github.com/onegov/onegov-cloud/commit/27b9816e79b512086c565200dfa94509b4676474)

### Winterthur

##### Fixes title not using translations.

`Bugfix` | [OGC-447](https://linear.app/onegovcloud/issue/OGC-447) | [489484c4d7](https://github.com/onegov/onegov-cloud/commit/489484c4d7fd58f90348ba15314c758456f70b16)

## 2022.37

`2022-07-10` | [230fbfbab3...fd6a1c15cc](https://github.com/OneGov/onegov-cloud/compare/230fbfbab3^...fd6a1c15cc)

### Winterthur

##### Fixes shift schedule image path colliding with cached files.

`Bugfix` | [OGC-447](https://linear.app/onegovcloud/issue/OGC-447) | [230fbfbab3](https://github.com/onegov/onegov-cloud/commit/230fbfbab3b96de35609edd9083e313547760892)

## 2022.36

`2022-07-09` | [1de8d90f39...8cde20cbf7](https://github.com/OneGov/onegov-cloud/compare/1de8d90f39^...8cde20cbf7)

### Core

##### Add function to check if an enum exists.

`Feature` | [542436165a](https://github.com/onegov/onegov-cloud/commit/542436165aedc25e0c724cf6703bf4544b8b40fb)

##### Fix result of enum_exists.

`Bugfix` | [dd767a7f1e](https://github.com/onegov/onegov-cloud/commit/dd767a7f1ebca0a0302c4149a7729a901ca52fee)

## 2022.35

`2022-07-09` | [2e71bf09b2...60f18c065e](https://github.com/OneGov/onegov-cloud/compare/2e71bf09b2^...60f18c065e)

### Activity

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [97cbf7747a](https://github.com/onegov/onegov-cloud/commit/97cbf7747a0979419227f59b360408a0060249d1)

### Election Day

##### Cleanup party name translation migrations.

`Feature` | [OGC-471](https://linear.app/onegovcloud/issue/OGC-471) | [1314183b38](https://github.com/onegov/onegov-cloud/commit/1314183b38ffa02e6fe84b484c67b70d11abf35f)

##### Add test to check for orphaned party results.

`Feature` | [OGC-494](https://linear.app/onegovcloud/issue/OGC-494) | [261735ad69](https://github.com/onegov/onegov-cloud/commit/261735ad69fa0f489c28d1bb89cbee3203f97a0d)

##### Add gender to candidates.

`Feature` | [OGC-489](https://linear.app/onegovcloud/issue/OGC-489) | [cf8397c303](https://github.com/onegov/onegov-cloud/commit/cf8397c303722e6a9145ba79593957e37ed5b13a)

##### Add year of birth to candidates.

`Feature` | [OGC-489](https://linear.app/onegovcloud/issue/OGC-489) | [bee734bc9e](https://github.com/onegov/onegov-cloud/commit/bee734bc9ed788d86da207cd28948bc3906e5e00)

##### Add expats to ballot and election results.

`Feature` | [OGC-394](https://linear.app/onegovcloud/issue/OGC-394) | [bef115bd9d](https://github.com/onegov/onegov-cloud/commit/bef115bd9de48b36989389c04bb54ceba2b9cc95)

##### Remove election compound lists view.

`Bugfix` | [OGC-495](https://linear.app/onegovcloud/issue/OGC-495) | [1ff774b7e9](https://github.com/onegov/onegov-cloud/commit/1ff774b7e920f6b688c731f397b1f5313a07cfc0)

##### Remove election compound lists view.

`Bugfix` | [OGC-495](https://linear.app/onegovcloud/issue/OGC-495) | [1029bd7432](https://github.com/onegov/onegov-cloud/commit/1029bd74321fb7495eee97431bddac7c78e66298)

### Feriennet

##### Also return activities for periods in payment phase in JSON.

`Bugfix` | [PRO-991](https://linear.app/projuventute/issue/PRO-991) | [63b5157779](https://github.com/onegov/onegov-cloud/commit/63b5157779c2d55d2e6cbf6d38db7e06bf009836)

### Org

##### Allows auto-accepting tickets for specific user roles

`Feature` | [OGC-481](https://linear.app/onegovcloud/issue/OGC-481) | [2e71bf09b2](https://github.com/onegov/onegov-cloud/commit/2e71bf09b20ce241ed66d2c6dfc14dae24d45f7b)

##### Activates date navigation and week numbers for room reservations

`Feature` | [OGC-334](https://linear.app/onegovcloud/issue/OGC-334) | [d8233e81d7](https://github.com/onegov/onegov-cloud/commit/d8233e81d74d02befb1c2362df825a96307341f6)

##### Fixes warning in cronjob tests.

`Bugfix` | [7a19572b62](https://github.com/onegov/onegov-cloud/commit/7a19572b62f99cadfc08ba5893e90e0833c04978)

##### Fix anchor position for category links

`Bugfix` | [OGC-460](https://linear.app/onegovcloud/issue/OGC-460) | [c295a89b61](https://github.com/onegov/onegov-cloud/commit/c295a89b61c92838e9c94e8424111155115a94dd)

##### Fix assign ticket function

Excluded inactive users from choices, listed non-admin users with ticket-rights

`Bugfix` | [OGC-428](https://linear.app/onegovcloud/issue/OGC-428) | [dbc8b4f511](https://github.com/onegov/onegov-cloud/commit/dbc8b4f511d67023c5323bcfbb7e232cdce6a270)

### Pay

##### Fixes stripe public identity if business name is missing.

`Bugfix` | [PRO-1050](https://linear.app/projuventute/issue/PRO-1050) | [35cf745058](https://github.com/onegov/onegov-cloud/commit/35cf7450581b8518897f638ebcfc46a9c05baeb6)

### People

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [dbab1c0e98](https://github.com/onegov/onegov-cloud/commit/dbab1c0e98a04f4181be0cb92e7887db5450f4b5)

### Recipient

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [bc0d39c3b3](https://github.com/onegov/onegov-cloud/commit/bc0d39c3b3263692ba7176ee2bbf305946608209)

### Reservation

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [005550581d](https://github.com/onegov/onegov-cloud/commit/005550581d5310eecd0a62b55ea04907eb1f8fb9)

### User

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [c2cae6a465](https://github.com/onegov/onegov-cloud/commit/c2cae6a4654f8718f87329472a55f84f0046d136)

### Winterthur

##### Add schichtplan image.

`Feature` | [OGC-447](https://linear.app/onegovcloud/issue/OGC-447) | [56863a3141](https://github.com/onegov/onegov-cloud/commit/56863a3141ea8cf3ce4272ad795bb813c1eecf05)

## 2022.34

`2022-06-29` | [2087d4d1d8...914b428fee](https://github.com/OneGov/onegov-cloud/compare/2087d4d1d8^...914b428fee)

### Ballot

##### Get rid of constants.

`Feature` | [33670009d9](https://github.com/onegov/onegov-cloud/commit/33670009d92c60ebec872df25223d36793d3f940)

### Core

##### Silence some packages during tests.

`Feature` | [c9c21e806e](https://github.com/onegov/onegov-cloud/commit/c9c21e806e51dc790497e62dc668a365603b1629)

##### Fixes translation hybrid trying to access unitialized session_manager in some rare cases.

`Bugfix` | [cc0ed66bd7](https://github.com/onegov/onegov-cloud/commit/cc0ed66bd7b0b5f208b6e9ca0191d93cd1346e7d)

### Election Day

##### Cleanup unused parsing function.

`Feature` | [960c69efae](https://github.com/onegov/onegov-cloud/commit/960c69efae5127bb078a274e44444e75958edfe6)

##### Always generate SVGs for all locales.

`Feature` | [OGC-471](https://linear.app/onegovcloud/issue/OGC-471) | [19bf4c3c13](https://github.com/onegov/onegov-cloud/commit/19bf4c3c138136f676f4bc8cb7d5aad9304c6829)

##### Improve open data download texts.

`Feature` | [OGC-379](https://linear.app/onegovcloud/issue/OGC-379) | [f26fc2cfbb](https://github.com/onegov/onegov-cloud/commit/f26fc2cfbbe5a5be2809a7ed9ab161be4a343c95)

##### Add party name translations to party results.

`Feature` | [OGC-471](https://linear.app/onegovcloud/issue/OGC-471) | [34d16b9d01](https://github.com/onegov/onegov-cloud/commit/34d16b9d01f9bef652aab00ec79840128c695071)

##### Fixes Italian translation.

`Bugfix` | [812dcf9424](https://github.com/onegov/onegov-cloud/commit/812dcf9424df6076cc33be66d5ff98bcfe9fc9f1)

##### Fixes styling of dropdown menus.

`Bugfix` | [26b0f1b141](https://github.com/onegov/onegov-cloud/commit/26b0f1b14152b36f835c14a802928ef6467d8600)

##### Fixes SVGs not generated for cantons without districts.

`Bugfix` | [97fbaab6a9](https://github.com/onegov/onegov-cloud/commit/97fbaab6a9600fe0f8341f130fcec6a2ace68aa1)

##### Set the current locale in the session manager when generating SVGs and PDFs.

Also simplify the D3 renderer a bit.

`Bugfix` | [e3543d9ed4](https://github.com/onegov/onegov-cloud/commit/e3543d9ed4775d6a735a821c32dc7c0965671f46)

### Feriennet

##### Add JSON view of activities.

`Feature` | [PRO-991](https://linear.app/projuventute/issue/PRO-991) | [8fa14f7aeb](https://github.com/onegov/onegov-cloud/commit/8fa14f7aebd11787f20cc44b28a191fcd1b60fef)

##### Change order of sponsors

`Bugfix` | [PRO-1043](https://linear.app/projuventute/issue/PRO-1043) | [df9b976f13](https://github.com/onegov/onegov-cloud/commit/df9b976f130e0e6b2bf384200d3ff0a9ed10def2)

### File

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [9fafda956a](https://github.com/onegov/onegov-cloud/commit/9fafda956aaca3cc45dbf10733a7b8e59e0c3077)

### Form

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [d226b5e6f1](https://github.com/onegov/onegov-cloud/commit/d226b5e6f1f164d3b015b93e0e2e4ab4c9f9ae17)

### Org

##### Long menu items scrollable

`Feature` | [OGC-477](https://linear.app/onegovcloud/issue/OGC-477) | [3e019fd29e](https://github.com/onegov/onegov-cloud/commit/3e019fd29e235c75e21c85f4de780b568715ec45)

### Pay

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [2087d4d1d8](https://github.com/onegov/onegov-cloud/commit/2087d4d1d82199f2a2f49e49ffea9957813bed4e)

### Town6

##### Make it possible to have an empty form lead

Leave lead empty if empty event_form_lead exists in .yaml.

`Bugfix` | [OGC-484](https://linear.app/onegovcloud/issue/OGC-484) | [994a5cda69](https://github.com/onegov/onegov-cloud/commit/994a5cda693ce01815b3d54ef9c605a1a805e179)

## 2022.33

`2022-06-13` | [6c05577c73...23af17cf33](https://github.com/OneGov/onegov-cloud/compare/6c05577c73^...23af17cf33)

### Feriennet

##### Improve compatibility with SQLAlchemy 1.4.

Removes the order_by mapper argument from activities and bookings.

`Feature` | [PRO-1028](https://linear.app/projuventute/issue/PRO-1028) | [1bd8bc51a9](https://github.com/onegov/onegov-cloud/commit/1bd8bc51a9762b84544bc1d61a525c9f86f6daef)

## 2022.32

`2022-06-13` | [96e5b775d4...e3432d6a6f](https://github.com/OneGov/onegov-cloud/compare/96e5b775d4^...e3432d6a6f)

### Core

##### Enables python linting in VSCode.

`Feature` | [89bdc84d38](https://github.com/onegov/onegov-cloud/commit/89bdc84d38cfd2bdce5b11bdd829ea550c37d043)

##### Lint tests too.

`Bugfix` | [ef4ffa3514](https://github.com/onegov/onegov-cloud/commit/ef4ffa35148d70cc30a22dbc97c8a1e76c835e22)

### Directory

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [121c43a22c](https://github.com/onegov/onegov-cloud/commit/121c43a22c621a603fad348ffefed357fcd3cdd6)

### Election Day

##### Show percentages of votes in elected candidates widgets for majorz elections.

`Feature` | [OGC-172](https://linear.app/onegovcloud/issue/OGC-172) | [96e5b775d4](https://github.com/onegov/onegov-cloud/commit/96e5b775d4ac24e580bdc3a10efb7b2545410abe)

##### Sort elected candidates in election compound mail by name.

`Feature` | [OGC-449](https://linear.app/onegovcloud/issue/OGC-449) | [dfd7446034](https://github.com/onegov/onegov-cloud/commit/dfd74460342c03c0ce17538469c166fd26ae7f80)

##### Reuse the party ID provided at upload.

`Feature` | [OGC-448](https://linear.app/onegovcloud/issue/OGC-448) | [4779d125de](https://github.com/onegov/onegov-cloud/commit/4779d125de68c943aa52f5a74aa62513619a4a8e)

##### Always sort list gropus by voters count.

`Bugfix` | [OGC-472](https://linear.app/onegovcloud/issue/OGC-472) | [9c1cdf6d46](https://github.com/onegov/onegov-cloud/commit/9c1cdf6d4624653332a844f89d65b5d09891b920)

##### Fixes generating list groups SVG with empty voters count.

`Bugfix` | [e18d441498](https://github.com/onegov/onegov-cloud/commit/e18d441498b97b0a4579737a5f5fa661985d7b96)

### Feriennet

##### Show date of birth in volunteers details.

`Feature` | [PRO-1036](https://linear.app/projuventute/issue/PRO-1036) | [74698171a5](https://github.com/onegov/onegov-cloud/commit/74698171a54b1cf602ce7d6b88414ad95fece689)

##### Adds compatibility with splinter 0.18.

`Bugfix` | [2ef9c4d375](https://github.com/onegov/onegov-cloud/commit/2ef9c4d375d2c6c14ec232523c899530e375ec1c)

### Form

##### Allow to define long descriptions.

`Feature` | [afba159d48](https://github.com/onegov/onegov-cloud/commit/afba159d48eea3577bcacd285daf20339830c364)

### Gazette

##### Stop running old upgrade steps.

`Bugfix` | [b698bd1039](https://github.com/onegov/onegov-cloud/commit/b698bd103995cf8748435da68b924e29b606cbe3)

### Org

##### Make user roles filter and management forms overwriteable.

`Feature` | [2b89502ce8](https://github.com/onegov/onegov-cloud/commit/2b89502ce811c2b7fa7fb2634cdf57ac7288dafc)

##### Allow ticket mails to be sent to logged in users.

`Feature` | [dd2c3b1563](https://github.com/onegov/onegov-cloud/commit/dd2c3b1563b4c836a187ccedddc437205f5738a6)

##### Allow to define form hints and helptexts in the form class.

`Feature` | [b9c216b1f9](https://github.com/onegov/onegov-cloud/commit/b9c216b1f9f2161605a835f71799a1de9ee2a3c9)

##### Make events editable until published.

`Feature` | [OGC-459](https://linear.app/onegovcloud/issue/OGC-459) | [4b1c2c0cb9](https://github.com/onegov/onegov-cloud/commit/4b1c2c0cb9fb46b18f8a04e8491255305de2a701)

### Ticket

##### Stop running old upgrade steps.

`Bugfix` | [3fb6a29036](https://github.com/onegov/onegov-cloud/commit/3fb6a29036499bed22fa5474bc92f47dc0a877ea)

### User

##### Change interface of logout_all_session to require only the app, not the whole request.

`Feature` | [b4db812018](https://github.com/onegov/onegov-cloud/commit/b4db81201812bf4824eb69353769fe77c00d9d6b)

## 2022.31

`2022-06-01` | [6a0671236e...3ba71360d0](https://github.com/OneGov/onegov-cloud/compare/6a0671236e^...3ba71360d0)

### Agency

##### Make all attributes sortable in organisation pdf exports

`Feature` | [OGC-445](https://linear.app/onegovcloud/issue/OGC-445) | [4635cdc640](https://github.com/onegov/onegov-cloud/commit/4635cdc640de10d30f573fc1d22fe765b22d5328)

### Core

##### Add compatibility with webdriver-manager 3.6.

`Feature` | [2065e0b0ba](https://github.com/onegov/onegov-cloud/commit/2065e0b0ba9cbbdb2ba66f9016f3bc203d6ab9f7)

##### Remove SameSite workaround for Sarafri 12.

`Other` | [OGC-464](https://linear.app/onegovcloud/issue/OGC-464) | [1604a474f5](https://github.com/onegov/onegov-cloud/commit/1604a474f5d08b03e5ef5267c8a1dcaf9950a5d5)

##### Set SameSite to locale cookie.

`Bugfix` | [OGC-465](https://linear.app/onegovcloud/issue/OGC-465) | [5be093c6e2](https://github.com/onegov/onegov-cloud/commit/5be093c6e27dedd291efb557bfda55b97fa460fd)

##### Avoid lua stack overflow when flushing caches.

`Bugfix` | [OGC-453](https://linear.app/onegovcloud/issue/OGC-453) | [b28edd3af8](https://github.com/onegov/onegov-cloud/commit/b28edd3af8de5e37a42150cc3b81139d6f984bd5)

### Election Day

##### Add HEAD views for elections, election compounds and votes.

`Feature` | [6d1959c2e8](https://github.com/onegov/onegov-cloud/commit/6d1959c2e8077b708b4adb710be9aa9d19ebd610)

##### Sort candidates by total votes in ElectionCandidatesByEntityTableWidget.

`Feature` | [OGC-174](https://linear.app/onegovcloud/issue/OGC-174) | [2f528524b7](https://github.com/onegov/onegov-cloud/commit/2f528524b79ab8ccebfd2e65d3ad82a98116a10c)

##### Remove open data load test hotfix.

`Other` | [OGC-417](https://linear.app/onegovcloud/issue/OGC-417) | [6a0671236e](https://github.com/onegov/onegov-cloud/commit/6a0671236e5c0fa11927a8ba8fb5e627ea5d630d)

##### Set SameSite to Lax for cache control cookie.

`Bugfix` | [OGC-463](https://linear.app/onegovcloud/issue/OGC-463) | [8b15800766](https://github.com/onegov/onegov-cloud/commit/8b158007667470bb17af387d946a35a68d801c7a)

##### Never cache views with Set-Cookie header.

`Bugfix` | [SEA-708](https://linear.app/seantis/issue/SEA-708) | [b6c50cdc78](https://github.com/onegov/onegov-cloud/commit/b6c50cdc78d5d458b71a1e8a3dbc88ed7b4cd206)

##### Only cache GET request responses.

`Bugfix` | [SEA-708](https://linear.app/seantis/issue/SEA-708) | [4feb7cfae9](https://github.com/onegov/onegov-cloud/commit/4feb7cfae95cec65e6f0fc0cb6d478879b2b1ca6)

### Feriennet

##### Banners

Banners can now be added with custom info texts

`Feature` | [PRO-1022](https://linear.app/projuventute/issue/PRO-1022) | [b99c03f9b4](https://github.com/onegov/onegov-cloud/commit/b99c03f9b48a2726b0ddbc10d27a589c4bd39f5e)

##### Hints dependent on wishlist-phase

`Bugfix` | [PRO-1035](https://linear.app/projuventute/issue/PRO-1035) | [7c3fb70f8f](https://github.com/onegov/onegov-cloud/commit/7c3fb70f8ffdbb8dfc9af279131eca228707041d)

### Fsi

##### Fix empty value problem in creating course forms

`Bugfix` | [OGC-433](https://linear.app/onegovcloud/issue/OGC-433) | [208867dbda](https://github.com/onegov/onegov-cloud/commit/208867dbda5e6ce194a81b75890ce36b82f0df87)

### Org

##### Adds school holidays setting so that Allocations may skip them.

`Feature` | [OGC-333](https://linear.app/onegovcloud/issue/OGC-333) | [21cbb9c54f](https://github.com/onegov/onegov-cloud/commit/21cbb9c54fa406cb6090047367e6ddde2ff60cec)

##### Allows frequency of status mail to be changed to weekly/monthly

`Feature` | [OGC-330](https://linear.app/onegovcloud/issue/OGC-330) | [8622172f2c](https://github.com/onegov/onegov-cloud/commit/8622172f2c9489d1b8af9e8ba3ec0b7de2d9b263)

##### Custom event text

`Feature` | [OGC-451](https://linear.app/onegovcloud/issue/OGC-451) | [d8b78907d0](https://github.com/onegov/onegov-cloud/commit/d8b78907d09efd5d78eca3feb78768a9af499f70)

##### Adds text modules that can be inserted in textareas

`Feature` | [OGC-331](https://linear.app/onegovcloud/issue/OGC-331) | [bb7c57a174](https://github.com/onegov/onegov-cloud/commit/bb7c57a174023d9d98d4df3fe92239631d9aabc4)

##### Add spam folder hint on registration.

`Feature` | [PRO-1039](https://linear.app/projuventute/issue/PRO-1039) | [d329208c9e](https://github.com/onegov/onegov-cloud/commit/d329208c9e6092423f528f6df4b36ab76a5695d3)

##### New settings overview

`Feature` | [b1d1fd3549](https://github.com/onegov/onegov-cloud/commit/b1d1fd3549b0423a99e6fefb62656816bce92f00)

##### Hide navi icon when all pages are private

`Feature` | [OGC-455](https://linear.app/onegovcloud/issue/OGC-455) | [11c24829b7](https://github.com/onegov/onegov-cloud/commit/11c24829b7deca192873551a7a4e6a4bb324bbb2)

##### Remembers previous form submission for reservations

`Feature` | [OGC-326](https://linear.app/onegovcloud/issue/OGC-326) | [0915bacf1e](https://github.com/onegov/onegov-cloud/commit/0915bacf1ea449bb8611f0d223fdd0dab188185b)

##### Logout users when changing their role or state.

`Bugfix` | [136](https://github.com/onegov/onegov-cloud/issues/136) | [e189d46194](https://github.com/onegov/onegov-cloud/commit/e189d46194b19e865edfc766c7990ea8ccdb098f)

##### Added phone type on vcf-cards

`Bugfix` | [OGC-419](https://linear.app/onegovcloud/issue/OGC-419) | [cc8f4dab4d](https://github.com/onegov/onegov-cloud/commit/cc8f4dab4dbec13afd3e4814c4f359a5fc491aef)

##### Change "signature" to "seal"

`Bugfix` | [OGC-401](https://linear.app/onegovcloud/issue/OGC-401) | [c460cf3525](https://github.com/onegov/onegov-cloud/commit/c460cf3525bdb48f7581ee14ae3097d13b13f36a)

##### Delete duplicated script

`Bugfix` | [OGC-447](https://linear.app/onegovcloud/issue/OGC-447) | [15f3db90e7](https://github.com/onegov/onegov-cloud/commit/15f3db90e7330a201f4c71821f8b45baaa5f0e1f)

### Town6

##### Remove space below and title of partner widget on subpages

`Bugfix` | [OGC-391](https://linear.app/onegovcloud/issue/OGC-391) | [12035672df](https://github.com/onegov/onegov-cloud/commit/12035672df0d17f99a487df8d480f0a65be3643e)

##### Fix resource popup view

`Bugfix` | [OGC-456](https://linear.app/onegovcloud/issue/OGC-456) | [b186383dcb](https://github.com/onegov/onegov-cloud/commit/b186383dcb0ab68d0b0445c1d53540ac2cf60564)

### User

##### Add logout commands to CLI.

Also ensure that users are logged out when they are modified via the 
CLI.

`Feature` | [SEA-708](https://linear.app/seantis/issue/SEA-708) | [b4a5abb62a](https://github.com/onegov/onegov-cloud/commit/b4a5abb62ac93160f0416354735f7a20c5464e32)

##### Rotate session ID when logging in.

`Bugfix` | [SEA-70](https://linear.app/seantis/issue/SEA-70) | [55b8edb7d2](https://github.com/onegov/onegov-cloud/commit/55b8edb7d295f4c961ec26025ccd88da8e1ac266)

### Winterthur

##### Add script for iframe

`Feature` | [OGC-447](https://linear.app/onegovcloud/issue/OGC-447) | [306d309695](https://github.com/onegov/onegov-cloud/commit/306d309695cc9fe7ba407de4eca0d24f65b7bae8)

## 2022.30

`2022-05-18` | [a381989943...cb7ef86c1d](https://github.com/OneGov/onegov-cloud/compare/a381989943^...cb7ef86c1d)

### Ballot

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [f1855379fb](https://github.com/onegov/onegov-cloud/commit/f1855379fbc9e7542376b4787a6027126d25898b)

### Core

##### Pin pytest-localserver.

Also, remove unused smtp fixture for old python version.

`Bugfix` | [OGC-444](https://linear.app/onegovcloud/issue/OGC-444) | [17a7c7d70b](https://github.com/onegov/onegov-cloud/commit/17a7c7d70b228c3a976bc3d84f4b7db1bc914785)

### Election Day

##### Improve compatibility with SQLAlchemy 1.4. (#338)

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [3bf5fbda3d](https://github.com/onegov/onegov-cloud/commit/3bf5fbda3de5f5202f05f1d6c7fc58078980f635)

##### Update Italian translations.

`Bugfix` | [f1f56d41ae](https://github.com/onegov/onegov-cloud/commit/f1f56d41aec4c60d0c467805e8d18969bba06c80)

##### Remove Set-Cookie header from cached pages.

`Bugfix` | [SEA-708](https://linear.app/seantis/issue/SEA-708) | [7c7be1908b](https://github.com/onegov/onegov-cloud/commit/7c7be1908be147cc54adab9e2d867a8885637fb0)

### Event

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [86d8c5f60d](https://github.com/onegov/onegov-cloud/commit/86d8c5f60d0f58af4b3d239935843fdbc77cebee)

### Feriennet

##### Fix invoice layout

`Bugfix` | [PRO-1020](https://linear.app/projuventute/issue/PRO-1020) | [191c35cc7f](https://github.com/onegov/onegov-cloud/commit/191c35cc7f1807153d36f98a212d49175d8c4177)

### Notice

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [a381989943](https://github.com/onegov/onegov-cloud/commit/a38198994383d3822e1e164f1dc4bf164e28b8cf)

### Org

##### Notifications for new tickets

Add field for standard new ticket notification email

`Feature` | [OGC-227](https://linear.app/onegovcloud/issue/OGC-227) | [aefb383e1a](https://github.com/onegov/onegov-cloud/commit/aefb383e1ad082792f7dc5b7202fb321948d6881)

##### Make registration hints more visible

`Feature` | [OGC-399](https://linear.app/onegovcloud/issue/OGC-399) | [a858d4687a](https://github.com/onegov/onegov-cloud/commit/a858d4687a70d27d77916518a1b385344b2d5603)

##### Cache custom event tags in redis

`Bugfix` | [OGC-368](https://linear.app/onegovcloud/issue/OGC-368) | [6e23afe751](https://github.com/onegov/onegov-cloud/commit/6e23afe751ded23fe42895392c237fb39ded9c54)

##### Credit card payment translations

`Bugfix` | [OGC-993](https://linear.app/onegovcloud/issue/OGC-993) | [086187f155](https://github.com/onegov/onegov-cloud/commit/086187f15583a532503db6e69ec3b0564ad35383)

### Town6

##### Fix position of hr-tag

`Bugfix` | [OGC-434](https://linear.app/onegovcloud/issue/OGC-434) | [632cb4871f](https://github.com/onegov/onegov-cloud/commit/632cb4871f1bd02cec2aca367d2a99358c3b7b27)

### Winterthur

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [1a82c60e89](https://github.com/onegov/onegov-cloud/commit/1a82c60e89bc422be5c890241009eb38a698ec7c)

### Wtfs

##### Improve compatibility with SQLAlchemy 1.4.

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [542e174dc8](https://github.com/onegov/onegov-cloud/commit/542e174dc8ec8db8b1783bbeba34c7db4b9ebc06)

## 2022.29

`2022-05-04` | [545369b9e1...984c251bdf](https://github.com/OneGov/onegov-cloud/compare/545369b9e1^...984c251bdf)

### Core

##### Unpin pytest.

`Other` | [OGC-293](https://linear.app/onegovcloud/issue/OGC-293) | [5a6a758dce](https://github.com/onegov/onegov-cloud/commit/5a6a758dce87b75a97eabc2622053bfa4b6c94ae)

### Election Day

##### Fix Italian translation.

`Bugfix` | [545369b9e1](https://github.com/onegov/onegov-cloud/commit/545369b9e1237e3b26be397eeebb493561e8c972)

##### Fixes embed and download link texts.

`Bugfix` | [OGC-274](https://linear.app/onegovcloud/issue/OGC-274) | [9a943ae864](https://github.com/onegov/onegov-cloud/commit/9a943ae864e58ef4951e12f399776e33a1d2b3de)

##### Fixes another embed link text.

`Bugfix` | [OGC-274](https://linear.app/onegovcloud/issue/OGC-274) | [de701c9324](https://github.com/onegov/onegov-cloud/commit/de701c9324df9d1cb668e8c8f107991a76c87e36)

##### Update Open Data Swiss metadata format.

`Other` | [OGC-416](https://linear.app/onegovcloud/issue/OGC-416) | [b229e4bde9](https://github.com/onegov/onegov-cloud/commit/b229e4bde959b43674a67041c6f0ea0b2ddb3987)

##### Avoid publishing intermediate results on Open Data Swiss.

`Bugfix` | [OGC-414](https://linear.app/onegovcloud/issue/OGC-414) | [d2e7dd1424](https://github.com/onegov/onegov-cloud/commit/d2e7dd1424d0e2b42ec800eb6166725f6e805680)

### Form

##### Adds compatibility with pyparsing 3.

`Other` | [OGC-117](https://linear.app/onegovcloud/issue/OGC-117) | [3ab76c7ae1](https://github.com/onegov/onegov-cloud/commit/3ab76c7ae1cf9ffc13e325eec403622740a66399)

### Org

##### Allows setting of access for individual allocations and rules

`Feature` | [OGC-420](https://linear.app/onegovcloud/issue/OGC-420) | [91ad52e1df](https://github.com/onegov/onegov-cloud/commit/91ad52e1df3aa1f6b20cd654131a74597e58f206)

##### Open only external forms in new tabs

Option for external-links in new tabs removed, only external form links will be opened in new tabs

`Bugfix` | [OGC-373](https://linear.app/onegovcloud/issue/OGC-373) | [0642270f30](https://github.com/onegov/onegov-cloud/commit/0642270f30f2a799fa390739f29bb2a51d0389ab)

### Winterthur

##### Fix styling

`Bugfix` | [FW-96](https://stadt-winterthur.atlassian.net/browse/FW-96) | [627cd4e914](https://github.com/onegov/onegov-cloud/commit/627cd4e914ce6b7efa3f2f12473a343d62fe8770)

## 2022.28

`2022-04-29` | [e44871e509...f07e6fabb0](https://github.com/OneGov/onegov-cloud/compare/e44871e509^...f07e6fabb0)

### Election Day

##### Hide empty candidates tables and figures. (#322)

`Feature` | [OGC-427](https://linear.app/onegovcloud/issue/OGC-427) | [3147e96447](https://github.com/onegov/onegov-cloud/commit/3147e9644759236d13c3e5702f5846c82b94b838)

##### Add notifications for election compounds.

`Feature` | [OGC-424](https://linear.app/onegovcloud/issue/OGC-424) | [cc096ff1b0](https://github.com/onegov/onegov-cloud/commit/cc096ff1b09e8782b580de71518835f307c677c3)

##### Use cached layout property instead of model properties in various views.

`Bugfix` | [4faea51ad6](https://github.com/onegov/onegov-cloud/commit/4faea51ad6bce9c2500b3792388396089da74fce)

### Org

##### Add access level "member"

Topics, people, etc. can now be assigned the access level "member"

`Feature` | [393](https://github.com/onegov/onegov-cloud/issues/393) | [e44871e509](https://github.com/onegov/onegov-cloud/commit/e44871e5097cdafe7529132e28a440e28e189c7f)

##### Fix typo

`Bugfix` | [OGC-409](https://linear.app/onegovcloud/issue/OGC-409) | [87768bd84f](https://github.com/onegov/onegov-cloud/commit/87768bd84f5d9825b9da54688ef921435f57b70a)

##### Fix custom_event_tags getting cached globally.

`Bugfix` | [OGC-368](https://linear.app/onegovcloud/issue/OGC-368) | [2835da5064](https://github.com/onegov/onegov-cloud/commit/2835da5064177cd4fa8bca1965a7cbc66a41e6a0)

##### Fix topic children links.

`Bugfix` | [OGC-426](https://linear.app/onegovcloud/issue/OGC-426) | [f4b36d4c4e](https://github.com/onegov/onegov-cloud/commit/f4b36d4c4ecacece5c8bf6c71c1cb49155c54e2d)

## 2022.27

`2022-04-27` | [aebf7f9623...1eec46ba9d](https://github.com/OneGov/onegov-cloud/compare/aebf7f9623^...1eec46ba9d)

## 2022.26

`2022-04-26` | [1a1867726e...a00696ed84](https://github.com/OneGov/onegov-cloud/compare/1a1867726e^...a00696ed84)

### Activity

##### Fixes calculation of available weeks.

`Bugfix` | [PRO-997](https://linear.app/projuventute/issue/PRO-997) | [6cc708de97](https://github.com/onegov/onegov-cloud/commit/6cc708de97788d3df5dc2e1e016f49d16d56ec9e)

### Core

##### Removes deprecated mailer argument.

`Other` | [OGC-307](https://linear.app/onegovcloud/issue/OGC-307) | [44159aa6db](https://github.com/onegov/onegov-cloud/commit/44159aa6dbafb0ddd0828e28b9c7e99b2b35f3eb)

##### Disable docs build step for now.

`Other` | [OGC-418](https://linear.app/onegovcloud/issue/OGC-418) | [2ace66d8de](https://github.com/onegov/onegov-cloud/commit/2ace66d8dea38d14aedc51c64924b6d6fb4141ae)

### Election Day

##### Add cache control tween.

`Feature` | [OGC-406](https://linear.app/onegovcloud/issue/OGC-406) | [3f69497348](https://github.com/onegov/onegov-cloud/commit/3f694973482928e0888ca73735b317971c30f96f)

##### Make mandates translation configurable by principal.

`Feature` | [OGC-404](https://linear.app/onegovcloud/issue/OGC-404) | [47b77d7800](https://github.com/onegov/onegov-cloud/commit/47b77d7800aed6b4792ba252aac661e7b93437fe)

##### Hide load test data in open data catalog.

`Other` | [OGC-417](https://linear.app/onegovcloud/issue/OGC-417) | [468b92f6a2](https://github.com/onegov/onegov-cloud/commit/468b92f6a2a1cbec159b12190f0069a63f64ed80)

##### Fixes pages cache not distinquishing query parameters.

Some cached (data) views used for the screen widgets may have query 
parameters such as limit or other filters.

`Bugfix` | [d8d29f07a6](https://github.com/onegov/onegov-cloud/commit/d8d29f07a67162416f4e4fcdfc2781ce3b2ef859)

##### Avoid showing relative timestamps.

This does not play well with caches.

`Bugfix` | [edee466f93](https://github.com/onegov/onegov-cloud/commit/edee466f9325d8b68ab0c49fa79cca46dba7cf47)

##### Clear all related election results when clearing an election compound result.

`Bugfix` | [OGC-403](https://linear.app/onegovcloud/issue/OGC-403) | [f2dac55868](https://github.com/onegov/onegov-cloud/commit/f2dac558680e456595084e2a9e37b468b8c3530b)

### File

##### Improve AIS2.py efficiency.

`Feature` | [3de2b4fa00](https://github.com/onegov/onegov-cloud/commit/3de2b4fa00b1c5ba86265232191bb46001898b5b)

### Org

##### Fix external links.

`Bugfix` | [OGC-373](https://linear.app/onegovcloud/issue/OGC-373) | [e8a70b7d26](https://github.com/onegov/onegov-cloud/commit/e8a70b7d26d5d1b89547c244a41942bbec40aa18)

## 2022.25

`2022-04-14` | [d5a2f507b2...0011026036](https://github.com/OneGov/onegov-cloud/compare/d5a2f507b2^...0011026036)

### Org

##### Allows tenants to specify custom tags

`Feature` | [OGC-368](https://linear.app/onegovcloud/issue/OGC-368) | [d5a2f507b2](https://github.com/onegov/onegov-cloud/commit/d5a2f507b21288b529a1e9faf35da9cc590ee441)

## 2022.24

`2022-04-12` | [52883745a4...fa02e35953](https://github.com/OneGov/onegov-cloud/compare/52883745a4^...fa02e35953)

### Event

##### Add compatibility with bleach 5.

`Bugfix` | [03d7cd4776](https://github.com/onegov/onegov-cloud/commit/03d7cd4776bac5601470279425d0d034a2b2d739)

### File

##### Switches to AIS2.py

`Feature` | [OGC-144](https://linear.app/onegovcloud/issue/OGC-144) | [ca4eb0c3fb](https://github.com/onegov/onegov-cloud/commit/ca4eb0c3fb5c83d841499e7a70403865eacdb6dd)

### Pdf

##### Add compatibility with bleach 5.

`Bugfix` | [374ce1a2ae](https://github.com/onegov/onegov-cloud/commit/374ce1a2aec5aeb1b73f10e48647f727c3ed06de)

## 2022.23

`2022-04-07` | [f0848d421d...ee0b0ad5c5](https://github.com/OneGov/onegov-cloud/compare/f0848d421d^...ee0b0ad5c5)

### Election Day

##### Fixes flaky test.

`Bugfix` | [f0848d421d](https://github.com/onegov/onegov-cloud/commit/f0848d421d99cac7e50d6ac0c9eb256c5b3acad7)

## 2022.22

`2022-04-06` | [54afaaa8bb...8b0903010b](https://github.com/OneGov/onegov-cloud/compare/54afaaa8bb^...8b0903010b)

### Core

##### Adds back the ability to send mails through SMTP.

`Feature` | [OGC-307](https://linear.app/onegovcloud/issue/OGC-307) | [54afaaa8bb](https://github.com/onegov/onegov-cloud/commit/54afaaa8bb09d76fe72a6e68b7f2783d40197f91)

##### Adds back smtp4dev for local development.

`Feature` | [OGC-307](https://linear.app/onegovcloud/issue/OGC-307) | [5c1ff9054f](https://github.com/onegov/onegov-cloud/commit/5c1ff9054f87c849cdd6cbd8183e5de616f09a3e)

### Winterthur

##### Add last updated timestamp and status to streets.

`Feature` | [FW-96](https://stadt-winterthur.atlassian.net/browse/FW-96) | [18ee0a32ea](https://github.com/onegov/onegov-cloud/commit/18ee0a32eaa64ec09bf49363125cd2f8c5fb577d)

## 2022.21

`2022-04-06` | [aab7cbddca...5ab05b5da9](https://github.com/OneGov/onegov-cloud/compare/aab7cbddca^...5ab05b5da9)

### Election Day

##### Add statistics view for votes.

`Feature` | [OGC-311](https://linear.app/onegovcloud/issue/OGC-311) | [75c7b74e97](https://github.com/onegov/onegov-cloud/commit/75c7b74e97518a135a721cb647fb3bb88bc1a4d2)

##### Add sort option to candidates and lists widgets.

`Feature` | [OGC-171](https://linear.app/onegovcloud/issue/OGC-171) | [846d81fb9a](https://github.com/onegov/onegov-cloud/commit/846d81fb9a9b6b2c21f165ce6c7916fd20d08314)

##### Add explanations PDF.

`Feature` | [OGC-72](https://linear.app/onegovcloud/issue/OGC-72) | [309dfa54bb](https://github.com/onegov/onegov-cloud/commit/309dfa54bb84ec7f89b96c80380c9f5e3b922024)

### Feriennet

##### Removes edit button from homepage

`Bugfix` | [PRO-1010](https://linear.app/projuventute/issue/PRO-1010) | [1579c442dd](https://github.com/onegov/onegov-cloud/commit/1579c442dd46a9444e856fc42c314014deb9e46d)

### Fsi

##### Restricts LDAP import to @gibz.ch users.

`Feature` | [OGC-325](https://linear.app/onegovcloud/issue/OGC-325) | [aab7cbddca](https://github.com/onegov/onegov-cloud/commit/aab7cbddca9bb83f77ca2812c76711041d897571)

### Town6

##### Add missing unsubscribe link.

`Bugfix` | [OGC-392](https://linear.app/onegovcloud/issue/OGC-392) | [73a250e567](https://github.com/onegov/onegov-cloud/commit/73a250e567c11b8c4b611ce1b671031fb8a9412f)

## 2022.20

`2022-03-30` | [9330c1793c...b5955d3b38](https://github.com/OneGov/onegov-cloud/compare/9330c1793c^...b5955d3b38)

### Activity

##### Fixes end of deadline calculation.

`Bugfix` | [PRO-1012](https://linear.app/projuventute/issue/PRO-1012) | [b898b4ce1e](https://github.com/onegov/onegov-cloud/commit/b898b4ce1ef2cf937c6f3911821bb4fcfe35b401)

### Election Day

##### Add turnout widget.

`Feature` | [OGC-178](https://linear.app/onegovcloud/issue/OGC-178) | [f11127ef99](https://github.com/onegov/onegov-cloud/commit/f11127ef9968c63ad5b24c8bb965285a64aa76d8)

##### Ensure at least one election or vote is selected when triggering notifications.

`Feature` | [OGC-302](https://linear.app/onegovcloud/issue/OGC-302) | [3eb06fbd95](https://github.com/onegov/onegov-cloud/commit/3eb06fbd95843a090b372f8c1d0a71626d9cbcf7)

##### Add counted and total number of entities widget.

`Feature` | [OGC-360](https://linear.app/onegovcloud/issue/OGC-360) | [01deeb6cc2](https://github.com/onegov/onegov-cloud/commit/01deeb6cc279653f012bfa2aefe041a758142a3f)

##### Define aria-current attribute to active elements in navigation.

`Feature` | [OGC-271](https://linear.app/onegovcloud/issue/OGC-271) | [4d506b0536](https://github.com/onegov/onegov-cloud/commit/4d506b0536e55e12a24ccbda94d5a020810c2975)

##### Add last result change widget.

`Feature` | [OGC-169](https://linear.app/onegovcloud/issue/OGC-169) | [9c5cbba464](https://github.com/onegov/onegov-cloud/commit/9c5cbba4642a623aa448c6265067e054db30bd2d)

##### Update last result change when assigning elections to compounds.

But only update to a newer date than the existing.

`Bugfix` | [OGC-358](https://linear.app/onegovcloud/issue/OGC-358) | [98e0fdbee0](https://github.com/onegov/onegov-cloud/commit/98e0fdbee0224ee54ea5ec54c1a87bda477396d1)

##### Update translation.

`Bugfix` | [OGC-278](https://linear.app/onegovcloud/issue/OGC-278) | [f51f18e6d6](https://github.com/onegov/onegov-cloud/commit/f51f18e6d6dfc940c12daa40ae910c920271d99d)

### Org

##### Show date of current registration window and available spots in forms list.

`Feature` | [OGC-381](https://linear.app/onegovcloud/issue/OGC-381) | [8a5330e309](https://github.com/onegov/onegov-cloud/commit/8a5330e3093b0697c264e0aa172387a40e132129)

##### Rename Payments to Credit card payments.

`Bugfix` | [PRO-993](https://linear.app/projuventute/issue/PRO-993) | [6f637071ea](https://github.com/onegov/onegov-cloud/commit/6f637071eae7d569a85eab64a5bdad4c22a20d07)

### Swissvotes

##### Add seantis to patrons.

`Feature` | [SWI-31](https://linear.app/swissvotes/issue/SWI-31) | [7a7a8a61d3](https://github.com/onegov/onegov-cloud/commit/7a7a8a61d340e0508c609d15d3936b51818e9236)

### Win

##### Fixes iframe resizer setup

`Bugfix` | [FW-101](https://stadt-winterthur.atlassian.net/browse/FW-101) | [173c88f420](https://github.com/onegov/onegov-cloud/commit/173c88f4209de415096b91e4b625f2507742ef4d)

## 2022.19

`2022-03-22` | [a99a63595a...1aaf29d721](https://github.com/OneGov/onegov-cloud/compare/a99a63595a^...1aaf29d721)

### Core

##### Ensures address fields are formatted correctly for Postmark API.

`Bugfix` | [OGC-310](https://linear.app/onegovcloud/issue/OGC-310) | [0fba25044c](https://github.com/onegov/onegov-cloud/commit/0fba25044c3bb7f50b8901cd80c763caf3665826)

### Election Day

##### Hide list connection svg for screen readers.

`Feature` | [OGC-280](https://linear.app/onegovcloud/issue/OGC-280) | [733f0194f1](https://github.com/onegov/onegov-cloud/commit/733f0194f12545caf32ace33a34fed2e908cd3e6)

##### Make focus more visible.

`Feature` | [OGC-269](https://linear.app/onegovcloud/issue/OGC-269) | [7c3c9994a8](https://github.com/onegov/onegov-cloud/commit/7c3c9994a8e491677565e0ab0a5b98a8ff77ebfc)

##### Improve accessability of the breadcrumb navigation.

`Feature` | [OGC-285](https://linear.app/onegovcloud/issue/OGC-285) | [99590f32a3](https://github.com/onegov/onegov-cloud/commit/99590f32a362492143cb7b5be7a49391e645ba4d)

##### Add skip links to archive views.

`Feature` | [OGC-265](https://linear.app/onegovcloud/issue/OGC-265) | [3a362e0f9e](https://github.com/onegov/onegov-cloud/commit/3a362e0f9e42a840d3bddc3adf8bb6a11c27e77a)

##### Change alt description of link to terms.

`Feature` | [OGC-276](https://linear.app/onegovcloud/issue/OGC-276) | [7aaf02adf3](https://github.com/onegov/onegov-cloud/commit/7aaf02adf3eec7bb3cd27fa007f0d28092f5fe1c)

##### Specify download and embed links.

`Feature` | [OGC-274](https://linear.app/onegovcloud/issue/OGC-274) | [3374a0675e](https://github.com/onegov/onegov-cloud/commit/3374a0675e463910d6c2291459844cd71dd0b565)

##### Link the whole title in archive views.

`Feature` | [OGC-283](https://linear.app/onegovcloud/issue/OGC-283) | [d1529725e5](https://github.com/onegov/onegov-cloud/commit/d1529725e5dadea969b34cc8616c23b1e95ac467)

##### Use percentual voters count.

`Feature` | [OGC-355](https://linear.app/onegovcloud/issue/OGC-355) | [da1616a1fc](https://github.com/onegov/onegov-cloud/commit/da1616a1fc5a4594cf941d83261420a91aae015d)

##### Add principal name to all ab titles.

`Feature` | [OGC-272](https://linear.app/onegovcloud/issue/OGC-272) | [d60471bcf7](https://github.com/onegov/onegov-cloud/commit/d60471bcf7da6b53a9f25b5e35acd247542f5174)

##### Add absolute majority widget.

`Feature` | [OGC-177](https://linear.app/onegovcloud/issue/OGC-177) | [e0e22d8580](https://github.com/onegov/onegov-cloud/commit/e0e22d8580cd0470765f99b0c23cf9c193451f3f)

##### Add party results JSON export.

`Feature` | [OGC-346](https://linear.app/onegovcloud/issue/OGC-346) | [7c8ed3db86](https://github.com/onegov/onegov-cloud/commit/7c8ed3db86065716f8de1b917f002f2d9a086d32)

##### Make mandates, votes and total_votes optional for party results import.

`Feature` | [OGC-345](https://linear.app/onegovcloud/issue/OGC-345) | [3860e7a63a](https://github.com/onegov/onegov-cloud/commit/3860e7a63ac3f993b3c3aae8ebe01499ddb4b46a)

##### Clear the results of all elections of a compound when uploading.

`Bugfix` | [OGC-356](https://linear.app/onegovcloud/issue/OGC-356) | [8e6f60eeb9](https://github.com/onegov/onegov-cloud/commit/8e6f60eeb9e7bd2299e590c21c356386aa166a04)

### Feriennet

##### Add categories and translations.

`Feature` | [PRO-900](https://linear.app/projuventute/issue/PRO-900) | [ec0c32673f](https://github.com/onegov/onegov-cloud/commit/ec0c32673fbabd61d4dc8684f2cfc419027b9d44)

##### Remove CS banner.

`Other` | [PRO-994](https://linear.app/projuventute/issue/PRO-994) | [ea55b1acd7](https://github.com/onegov/onegov-cloud/commit/ea55b1acd7578bc2653619cd9570e828a28e6802)

##### Log QR bill errors instead of throwing an exception.

Bills may be paid with the displayed information.

`Bugfix` | [PRO-1011](https://linear.app/projuventute/issue/PRO-1011) | [4dfc76502a](https://github.com/onegov/onegov-cloud/commit/4dfc76502af918f13141e53a7322bcc610329348)

### Org

##### Add an event category for elderly.

`Feature` | [OGC-361](https://linear.app/onegovcloud/issue/OGC-361) | [0aff416995](https://github.com/onegov/onegov-cloud/commit/0aff416995a34b4f7b50028c6d9753ae58fcae01)

##### Improves form error text.

`Feature` | [OGC-278](https://linear.app/onegovcloud/issue/OGC-278) | [0de7ca376c](https://github.com/onegov/onegov-cloud/commit/0de7ca376c4fc9024eb942c8eaaa64a02837a487)

##### Update translations.

`Feature` | [PRO-1006](https://linear.app/projuventute/issue/PRO-1006) | [386661597b](https://github.com/onegov/onegov-cloud/commit/386661597b6d5beced0476c3b24426eaf0e3fb63)

##### Fixes news widget on homepage.

`Bugfix` | [OGC-363](https://linear.app/onegovcloud/issue/OGC-363) | [e0f33daf5b](https://github.com/onegov/onegov-cloud/commit/e0f33daf5bfa7f7026dd8a358fa5e011bf7f7424)

##### Fixes publication date ignored when indexing.

`Bugfix` | [OGC-372](https://linear.app/onegovcloud/issue/OGC-372) | [1e81d6f964](https://github.com/onegov/onegov-cloud/commit/1e81d6f96428cf9c32127badc77c80f1342819e8)

##### Fixes news widget on homepage.

`Bugfix` | [OGC-363](https://linear.app/onegovcloud/issue/OGC-363) | [0963e963f5](https://github.com/onegov/onegov-cloud/commit/0963e963f5e466b60d37c693750d057bf63eaed0)

### Town6

##### Enable redirect option in homepage settings.

`Feature` | [OGC-370](https://linear.app/onegovcloud/issue/OGC-370) | [2cde2466ad](https://github.com/onegov/onegov-cloud/commit/2cde2466ad7f872b2c04d1acb98d0a5b71f5e966)

##### Show event organizers in the overview.

`Feature` | [OGC-362](https://linear.app/onegovcloud/issue/OGC-362) | [39bdc3a588](https://github.com/onegov/onegov-cloud/commit/39bdc3a5883cefb3d501bf36f7a54c0b1ce8f94e)

##### Style event overview side panel.

`Feature` | [OGC-200](https://linear.app/onegovcloud/issue/OGC-200) | [dd54912437](https://github.com/onegov/onegov-cloud/commit/dd549124370e3552006e6ce9a0d14f39e0c9b906)

##### Use main font size as rule for max-width.

`Bugfix` | [OGC-319](https://linear.app/onegovcloud/issue/OGC-319) | [b492cf4d8b](https://github.com/onegov/onegov-cloud/commit/b492cf4d8b46c3b225b37bc53a8b5e3b842fd348)

### Winterthur

##### Adjust daycare calculation.

`Feature` | [OGC-210](https://linear.app/onegovcloud/issue/OGC-210) | [e9e2e193c4](https://github.com/onegov/onegov-cloud/commit/e9e2e193c4d1f702aca13632c3cc292d203cd447)

## 2022.18

`2022-03-03` | [c26f5a6d76...83b91cc916](https://github.com/OneGov/onegov-cloud/compare/c26f5a6d76^...83b91cc916)

### Election Day

##### Add superregions to compounds.

`Feature` | [OGC-320](https://linear.app/onegovcloud/issue/OGC-320) | [9143e8c31b](https://github.com/onegov/onegov-cloud/commit/9143e8c31b58ae6ee4f75e8ed9d7a1b81bb835cc)

##### Allow to use voters count in non-pukelsheim compounds.

`Feature` | [OGC-321](https://linear.app/onegovcloud/issue/OGC-321) | [66de846c45](https://github.com/onegov/onegov-cloud/commit/66de846c45e94ef0b9d3e7ecfc4d1a48b4b5848a)

##### Add total voters count column to party results.

`Feature` | [OGC-344](https://linear.app/onegovcloud/issue/OGC-344) | [c40f83a48a](https://github.com/onegov/onegov-cloud/commit/c40f83a48a84c869af6f4a544d87fb89c6592a12)

##### Always include votes and voters count in party result JSON views.

`Feature` | [OGC-348](https://linear.app/onegovcloud/issue/OGC-348) | [e4e79bc6de](https://github.com/onegov/onegov-cloud/commit/e4e79bc6deea29306485ae320338c3bd916ec268)

##### Fixes JSON serialization of party results.

`Bugfix` | [f0b9bd9158](https://github.com/onegov/onegov-cloud/commit/f0b9bd9158a8007ddffeb0b5f073c0b7e21d8bcb)

### Feriennet

##### Use less ressources by avoiding cloning browser.

`Bugfix` | [OGC-349](https://linear.app/onegovcloud/issue/OGC-349) | [f356e26c6d](https://github.com/onegov/onegov-cloud/commit/f356e26c6df1362a57be886eb24e00999547558f)

### Org

##### Only show archived tickets in the ticket archive.

`Other` | [OGC-242](https://linear.app/onegovcloud/issue/OGC-242) | [c26f5a6d76](https://github.com/onegov/onegov-cloud/commit/c26f5a6d76d68eb498f498c3ba84add0bafd8743)

##### Fixes migrate newsletter command.

`Bugfix` | [71e0992d12](https://github.com/onegov/onegov-cloud/commit/71e0992d12999efb93e3f8747897baacc098be01)

##### Fixes sorting of root pages.

`Bugfix` | [OGC-259](https://linear.app/onegovcloud/issue/OGC-259) | [b3a5813554](https://github.com/onegov/onegov-cloud/commit/b3a5813554afc4fcbac1c77a4dce06eb2ccef69f)

##### Fixes ordering of pages in tiles widget.

`Bugfix` | [OGC-261](https://linear.app/onegovcloud/issue/OGC-261) | [cdbb4de64f](https://github.com/onegov/onegov-cloud/commit/cdbb4de64fea7321345f653726d128ee1e5b6259)

### Town6

##### Fix calendar nav icon.

`Bugfix` | [OGC-302](https://linear.app/onegovcloud/issue/OGC-302) | [b5e20598c2](https://github.com/onegov/onegov-cloud/commit/b5e20598c2a0e0a5a3823c6504f9b72199ab7c58)

## 2022.17

`2022-02-28` | [afe9de72f0...1feabb29f9](https://github.com/OneGov/onegov-cloud/compare/afe9de72f0^...1feabb29f9)

### Election Day

##### Improve archive titles for screenreaders.

`Feature` | [OGC-281](https://linear.app/onegovcloud/issue/OGC-281) | [2ddd563610](https://github.com/onegov/onegov-cloud/commit/2ddd5636106682617ed509fe1e99b970800ef3ca)

##### Make some tests less flaky.

`Bugfix` | [afe9de72f0](https://github.com/onegov/onegov-cloud/commit/afe9de72f0c57ec580f323bb30ba0708e1fa7f40)

##### Add alt text to logo.

`Other` | [OGC-281](https://linear.app/onegovcloud/issue/OGC-281) | [03b25811ff](https://github.com/onegov/onegov-cloud/commit/03b25811ffdbd2daffa06410a99e596f1679282b)

##### Show file import errors in cleanup subscriber form.

`Bugfix` | [40e9bf14f1](https://github.com/onegov/onegov-cloud/commit/40e9bf14f1b9583dc54e3f93b2766fc6dd17d9f8)

### Feriennet

##### Update translations.

`Other` | [PRO-981](https://linear.app/projuventute/issue/PRO-981) | [175330c738](https://github.com/onegov/onegov-cloud/commit/175330c738910d6b55decf4eb770b9c88963ee71)

##### Remove Lidle and WUP app.

`Other` | [PRO-994](https://linear.app/projuventute/issue/PRO-994) | [c89335fd6e](https://github.com/onegov/onegov-cloud/commit/c89335fd6e66ecdb4080bb2cd89fd72ab14a8f20)

### Fsi

##### Improve LDAP log messages.

`Other` | [OGC-325](https://linear.app/onegovcloud/issue/OGC-325) | [d897928ebc](https://github.com/onegov/onegov-cloud/commit/d897928ebc0f699ea8b912e76fdcc773e38e717b)

### Org

##### Fixes disabling newsletter not working.

`Bugfix` | [OGC-211](https://linear.app/onegovcloud/issue/OGC-211) | [1bce8a9f37](https://github.com/onegov/onegov-cloud/commit/1bce8a9f371b3f20f99dbd4c46aad8d14d83a136)

## 2022.16

`2022-02-24` | [f66cece404...9ece574c51](https://github.com/OneGov/onegov-cloud/compare/f66cece404^...9ece574c51)

### Election Day

##### Change text of PDF download link.

`Other` | [OGC-286](https://linear.app/onegovcloud/issue/OGC-286) | [3bc90c9149](https://github.com/onegov/onegov-cloud/commit/3bc90c9149d03119af6b1a62ff84ab6a0cf3013c)

##### Improve accessibility of footer.

`Other` | [OGC-270](https://linear.app/onegovcloud/issue/OGC-270) | [228360f89b](https://github.com/onegov/onegov-cloud/commit/228360f89bfd389c46ee99559e9dcb189b6cf47b)

##### Fixes archive header title level.

`Other` | [OGC-335](https://linear.app/onegovcloud/issue/OGC-335) | [b9ebf5752b](https://github.com/onegov/onegov-cloud/commit/b9ebf5752bcdd6e6fa09a891be8f343d17e37a2d)

##### Use table header cells for election and vote titles in archive tables.

`Other` | [OGC-268](https://linear.app/onegovcloud/issue/OGC-268) | [6b074a4c5d](https://github.com/onegov/onegov-cloud/commit/6b074a4c5d589bffe82e1a5bdcbcba193ab88034)

### Fsi

##### Add log messages to LDAP import.

`Other` | [OGC-325](https://linear.app/onegovcloud/issue/OGC-325) | [1a880ca764](https://github.com/onegov/onegov-cloud/commit/1a880ca764019967e2ac7cd38865afcd6e6303d5)

### Org

##### Reindex models with changed publication timestamps during the hourly mainteance task.

`Feature` | [OGC-183](https://linear.app/onegovcloud/issue/OGC-183) | [8d49dcb0a6](https://github.com/onegov/onegov-cloud/commit/8d49dcb0a60672ba119769392fdb06643f00ddce)

### Town6

##### Allow event-links to have full width.

`Bugfix` | [OGC-318](https://linear.app/onegovcloud/issue/OGC-318) | [22fa676dde](https://github.com/onegov/onegov-cloud/commit/22fa676dde821f382e316c45023c101262e98c38)

## 2022.15

`2022-02-19` | [b289e1cd6e...c80d1d6686](https://github.com/OneGov/onegov-cloud/compare/b289e1cd6e^...c80d1d6686)

### Core

##### Update bjeorn.

`Other` | [OGC-313](https://linear.app/onegovcloud/issue/OGC-313) | [b289e1cd6e](https://github.com/onegov/onegov-cloud/commit/b289e1cd6e2851940e369407795e2b0a5ec71429)

### Election Day

##### Fixes wrong API CSV template links.

`Bugfix` | [ca7ffe1ea9](https://github.com/onegov/onegov-cloud/commit/ca7ffe1ea9749ac30b1c0503946c6c9ae2d73e7a)

##### Fixes translation.

`Bugfix` | [3496cb94fb](https://github.com/onegov/onegov-cloud/commit/3496cb94fb02f7f9d126165c6925405c14846f31)

##### Checks panachage data instead of panachage headers and ignores superfluous panachage data.

`Bugfix` | [3c8d16a37e](https://github.com/onegov/onegov-cloud/commit/3c8d16a37ebf0f3e4e5247e5888d5a0560156ede)

##### Removes mandate allocation view.

`Other` | [OGC-322](https://linear.app/onegovcloud/issue/OGC-322) | [5e51608505](https://github.com/onegov/onegov-cloud/commit/5e51608505df35eefe57f7c208f4dd2790462cad)

##### Remove empty paragraphs.

`Bugfix` | [OGC-275](https://linear.app/onegovcloud/issue/OGC-275) | [9f570388f0](https://github.com/onegov/onegov-cloud/commit/9f570388f0489ce04d9546cb8929c00e7b38ed92)

##### Fixes inconsistent progress display in election compounds for election with more than one municipality.

`Bugfix` | [df7a90ed0f](https://github.com/onegov/onegov-cloud/commit/df7a90ed0fdcea037f0fb4a59393adf922ef51cf)

##### Fixes JSON serialization of voters counts.

`Bugfix` | [35a5e18765](https://github.com/onegov/onegov-cloud/commit/35a5e187650a717210e2c4794dccfb91f685404a)

### Org

##### Catch more invalid ticket state changes.

`Other` | [OGC-290](https://linear.app/onegovcloud/issue/OGC-290) | [b44a8e49f6](https://github.com/onegov/onegov-cloud/commit/b44a8e49f6711458b5c4333096e6b1a630fb42a7)

## 2022.14

`2022-02-17` | [4fe96a321f...d0df117ff2](https://github.com/OneGov/onegov-cloud/compare/4fe96a321f^...d0df117ff2)

### Election Day

##### Add REST interface for party results of election compounds.

`Feature` | [OGC-295](https://linear.app/onegovcloud/issue/OGC-295) | [3d6dd520f9](https://github.com/onegov/onegov-cloud/commit/3d6dd520f99a0938c0fa48865d54bc807e425b88)

##### Add election compound import format.

`Feature` | [OGC-291](https://linear.app/onegovcloud/issue/OGC-291) | [c439b05596](https://github.com/onegov/onegov-cloud/commit/c439b055966b422c6366525c8b4e4463056ec529)

##### Sort elections of compounds by shortcode only.

`Bugfix` | [OGC-294](https://linear.app/onegovcloud/issue/OGC-294) | [624eab47f6](https://github.com/onegov/onegov-cloud/commit/624eab47f625c1a3d2ceec24ea843fcb951db017)

##### Fixes wildcard archive search.

`Bugfix` | [OGC-303](https://linear.app/onegovcloud/issue/OGC-303) | [fe458ad8e7](https://github.com/onegov/onegov-cloud/commit/fe458ad8e70226a89a623c94577c5de1608e9d4a)

##### Always show number of mandates ander voters count in list groups.

`Other` | [OGC-162](https://linear.app/onegovcloud/issue/OGC-162) | [c7000e717c](https://github.com/onegov/onegov-cloud/commit/c7000e717c8569171d7a3d61e7f258f3e3746a4f)

##### Update figcaption of list groups diagram.

`Other` | [OGC-162](https://linear.app/onegovcloud/issue/OGC-162) | [56dcc274d9](https://github.com/onegov/onegov-cloud/commit/56dcc274d934c5ac6193c448ca26b34b20070ac3)

##### Update translations.

`Other` | [OGC-291](https://linear.app/onegovcloud/issue/OGC-291) | [1ea31ea9b0](https://github.com/onegov/onegov-cloud/commit/1ea31ea9b0ca2df9f441d9786a91e304c3494083)

##### Separate manual completion of election compounds from the Double Pukelsheim setting.

`Other` | [OGC-167](https://linear.app/onegovcloud/issue/OGC-167) | [9dbbd5caca](https://github.com/onegov/onegov-cloud/commit/9dbbd5cacabdce5c416d9f88bf1bb80961e28c4e)

##### Store the voters count as decimal numbers.

`Other` | [OGC-296](https://linear.app/onegovcloud/issue/OGC-296) | [0d36c8d33a](https://github.com/onegov/onegov-cloud/commit/0d36c8d33a74384b0a08bc51cf583c7e5bd99bfd)

### Org

##### Fixes setting up logging too late.

`Bugfix` | [OGC-309](https://linear.app/onegovcloud/issue/OGC-309) | [4fe96a321f](https://github.com/onegov/onegov-cloud/commit/4fe96a321fbd02daecf347fbe9a7860221394647)

##### Fixes submission not deletable if not completed.

`Bugfix` | [OGC-243](https://linear.app/onegovcloud/issue/OGC-243) | [0c01377bbf](https://github.com/onegov/onegov-cloud/commit/0c01377bbf0c6f250c150781aa3cc3f83507ea58)

##### Use the same unsubscribe link in the daily statistics mail body and headers.

`Bugfix` | [c9fc2ae586](https://github.com/onegov/onegov-cloud/commit/c9fc2ae586c8544181d5c06fa160b3d73aa9f777)

##### Disable newsletter by default.

`Other` | [OGC-314](https://linear.app/onegovcloud/issue/OGC-314) | [6d322f612f](https://github.com/onegov/onegov-cloud/commit/6d322f612f00b8a356390453a4b7446e38245370)

##### Fixes keyword converter struggling with plus signs.

`Bugfix` | [OGC-240](https://linear.app/onegovcloud/issue/OGC-240) | [c60082c6dc](https://github.com/onegov/onegov-cloud/commit/c60082c6dcbba1f8e48cbc6c7255aae8213a43eb)

## 2022.13

`2022-02-13` | [b6ae0228ad...250eadea7f](https://github.com/OneGov/onegov-cloud/compare/b6ae0228ad^...250eadea7f)

### Core

##### Ignores inactive recipient errors in postmark mailer.

`Bugfix` | [d679ef3917](https://github.com/onegov/onegov-cloud/commit/d679ef3917ba23488447e2f7ad18a24c75e7195d)

##### Fixes CLI commands without selectors not logging.

`Bugfix` | [OGC-309](https://linear.app/onegovcloud/issue/OGC-309) | [456156a694](https://github.com/onegov/onegov-cloud/commit/456156a6947166f0d88494841385e72ab449574c)

### Election Day

##### Update translations.

`Other` | [OGC-147](https://linear.app/onegovcloud/issue/OGC-147) | [4f60ddc732](https://github.com/onegov/onegov-cloud/commit/4f60ddc732b95b10a4cd5b2e83edc7e0117b8e6e)

### Feriennet

##### Update bank statement import hint.

`Other` | [PRO-998](https://linear.app/projuventute/issue/PRO-998) | [127c6efdc5](https://github.com/onegov/onegov-cloud/commit/127c6efdc5235061ae738c7b6c1d01cbf93a7d96)

### Org

##### Use a honeypot for newsletter signup.

`Feature` | [OGC-306](https://linear.app/onegovcloud/issue/OGC-306) | [7bfcfca307](https://github.com/onegov/onegov-cloud/commit/7bfcfca307859967c5c4452261caa89d81b0bb22)

##### Send daily ticket statistics as marketing mails.

`Feature` | [OGC-305](https://linear.app/onegovcloud/issue/OGC-305) | [1ea0e47ca8](https://github.com/onegov/onegov-cloud/commit/1ea0e47ca8a33c1b70deb4ba2c15ca697d9b6cca)

##### Set form defaults for room allocations to not partly available.

`Other` | [OGC-308](https://linear.app/onegovcloud/issue/OGC-308) | [c3b82dda74](https://github.com/onegov/onegov-cloud/commit/c3b82dda74e68c63d9bb3697e555f008c414b270)

### Town6

##### Fixes hidden form fields not being hidden.

`Bugfix` | [ec15c054bb](https://github.com/onegov/onegov-cloud/commit/ec15c054bb03ff0b802d863349c7ab4a6fb1f987)

## 2022.12

`2022-02-08` | [32c4931bf0...e7bcf7d0af](https://github.com/OneGov/onegov-cloud/compare/32c4931bf0^...e7bcf7d0af)

### Agency

##### Show membership function in membership instead of person function.

`Bugfix` | [OGC-288](https://linear.app/onegovcloud/issue/OGC-288) | [a22c0e1a7b](https://github.com/onegov/onegov-cloud/commit/a22c0e1a7b40b77592ffe548c07b6a197b1dfc68)

### Ferien

##### Add checkbox to confirm that the notification is not spam.

`Feature` | [PRO-995](https://linear.app/projuventute/issue/PRO-995) | [0328795335](https://github.com/onegov/onegov-cloud/commit/0328795335684e89298ee065ca1ee55d9856bbe6)

### Feriennet

##### Exchange sponsor banners

`Other` | [OGC-989](https://linear.app/onegovcloud/issue/OGC-989) | [a401fa7bfd](https://github.com/onegov/onegov-cloud/commit/a401fa7bfdb875db813b10081699bc031b7c3e2d)

##### Update Italian translations.

`Other` | [PRO-983](https://linear.app/projuventute/issue/PRO-983) | [607cae50d5](https://github.com/onegov/onegov-cloud/commit/607cae50d5dbf1542e3f958d1b1cd813ca5150bb)

### Fsi

##### Send mails in batches.

`Feature` | [OGC-289](https://linear.app/onegovcloud/issue/OGC-289) | [2baa95326a](https://github.com/onegov/onegov-cloud/commit/2baa95326a84d62c424b3f0113164da016ca2458)

### Org

##### Fixes hidden contact in directory-entries.

`Bugfix` | [OGC-297](https://linear.app/onegovcloud/issue/OGC-297) | [32c4931bf0](https://github.com/onegov/onegov-cloud/commit/32c4931bf08e68bc519e8d5986e29d444cb23918)

##### Change email-adress in top-bar to account

`Other` | [PRO-926](https://linear.app/projuventute/issue/PRO-926) | [c422144454](https://github.com/onegov/onegov-cloud/commit/c422144454c532a628ecb8ec23db1f94d6157267)

### Server

##### Make join of debug server more tolerant.

`Bugfix` | [834757a243](https://github.com/onegov/onegov-cloud/commit/834757a243f319d8cf06ad07b5ab89c5514b5835)

## 2022.11

`2022-02-06` | [e68aed973c...f01da08089](https://github.com/OneGov/onegov-cloud/compare/e68aed973c^...f01da08089)

### Core

##### Add batch sending of emails.

Replace old SMTP mailer with Postmark API.

`Feature` | [OGC-153](https://linear.app/onegovcloud/issue/OGC-153) | [e68aed973c](https://github.com/onegov/onegov-cloud/commit/e68aed973c50374a97591a5096a454d7c2c6ce9a)

### Election Day

##### Allow to bulk deletion of subscribers.

`Feature` | [OGC-147](https://linear.app/onegovcloud/issue/OGC-147) | [ee40c2bb36](https://github.com/onegov/onegov-cloud/commit/ee40c2bb36167e8a403886884895f8427c478324)

##### Add double opt-in and out to email subscriptions.

`Feature` | [OGC-147](https://linear.app/onegovcloud/issue/OGC-147) | [2c6e8ddc88](https://github.com/onegov/onegov-cloud/commit/2c6e8ddc8880ad8c16f877bb837a633802916b7c)

##### Fixes party result calculation for missing voters counts.

`Bugfix` | [07cd12c9d1](https://github.com/onegov/onegov-cloud/commit/07cd12c9d12dabcf2a554169e8e2a7359853ae66)

### Server

##### Fixes race condition in debug server.

`Bugfix` | [022d4e358f](https://github.com/onegov/onegov-cloud/commit/022d4e358f09fda012cbfe4d84b0eb1e3629651e)

## 2022.10

`2022-02-03` | [ba55b1b9d8...b4b4d08647](https://github.com/OneGov/onegov-cloud/compare/ba55b1b9d8^...b4b4d08647)

### Election Day

##### Fixes wrong opendata.swiss metadata.

`Bugfix` | [OGC-252](https://linear.app/onegovcloud/issue/OGC-252) | [4ab1240f50](https://github.com/onegov/onegov-cloud/commit/4ab1240f5058863e0332986e31e0262a094ad2b8)

### Org

##### Improve page content macro.

`Other` | [OGC-206](https://linear.app/onegovcloud/issue/OGC-206) | [8190112deb](https://github.com/onegov/onegov-cloud/commit/8190112debc3df1536afd21146a67fd111e63098)

##### Add hint to user group form.

`Other` | [OGC-257](https://linear.app/onegovcloud/issue/OGC-257) | [ed36b3f57f](https://github.com/onegov/onegov-cloud/commit/ed36b3f57fdba9b8d6210b55296a1e2d1fe43c28)

## 2022.9

`2022-01-25` | [e2b7e13929...5ad78bf058](https://github.com/OneGov/onegov-cloud/compare/e2b7e13929^...5ad78bf058)

### Agency

##### Disable person link extensions.

`Bugfix` | [OGC-228](https://linear.app/onegovcloud/issue/OGC-228) | [e2b7e13929](https://github.com/onegov/onegov-cloud/commit/e2b7e13929be041df236ded402217244c6c7165f)

### Election Day

##### Add year filters to backend views.

`Feature` | [OGC-68](https://linear.app/onegovcloud/issue/OGC-68) | [599ddb9fbf](https://github.com/onegov/onegov-cloud/commit/599ddb9fbfbcb8c2d9a025b31f8888bc16bc2169)

##### Add actions menus to election, election compound and votes views if logged in.

`Feature` | [OGC-69](https://linear.app/onegovcloud/issue/OGC-69) | [aac4de597d](https://github.com/onegov/onegov-cloud/commit/aac4de597de764bc455cdb15b1d7bf48c09d8085)

##### Allow to change the IDs of elections, election compounds and votes.

`Feature` | [OGC-60](https://linear.app/onegovcloud/issue/OGC-60) | [92b1acb4b0](https://github.com/onegov/onegov-cloud/commit/92b1acb4b0c1a698b4434a13d6bd0d8deb7f862b)

##### Add honepot fields to subscription forms.

`Feature` | [OGC-114](https://linear.app/onegovcloud/issue/OGC-114) | [40e9bd0cb5](https://github.com/onegov/onegov-cloud/commit/40e9bd0cb5c8fce272ec7a28eaa512c62553eff2)

##### Removes inconsistencies in the display of embedded links for items without results.

`Bugfix` | [43a7957afd](https://github.com/onegov/onegov-cloud/commit/43a7957afd1b6258c6b6c0da7ab4debe58aebc21)

### Town6

##### Style occurences side panel.

`Bugfix` | [OGC-200](https://linear.app/onegovcloud/issue/OGC-200) | [5037c85660](https://github.com/onegov/onegov-cloud/commit/5037c85660cbfd3a9747c775ab409042a24ad0e1)

##### Style more side panels.

`Bugfix` | [OGC-200](https://linear.app/onegovcloud/issue/OGC-200) | [ba24957bb8](https://github.com/onegov/onegov-cloud/commit/ba24957bb8eadc1cb48155c6f2855b4d6676f1a9)

## 2022.8

`2022-01-23` | [73b49c2696...28fc743aba](https://github.com/OneGov/onegov-cloud/compare/73b49c2696^...28fc743aba)

### Election Day

##### Add voters count to election compound party results.

For election compounds with Doppelter Pukelsheim only. Also adds a new view and widgets based on the party results to display list groups and changes the existing list view to display voters counts instead of votes. Adds these views to the PDFs and SVGs. Futerhmore removes inconsistencies with displaying intermediate results, cleans up Doppelter Pukelsheim namings and descriptions and a lot of other things.

`Feature` | [OGC-162](https://linear.app/onegovcloud/issue/OGC-162) | [d30032b59e](https://github.com/onegov/onegov-cloud/commit/d30032b59ebddd6255ce9f01b9c5d3770bd2067e)

### Swissvotes

##### Fixes sorting search results with empty titles throwing an error.

`Bugfix` | [73b49c2696](https://github.com/onegov/onegov-cloud/commit/73b49c2696528fdf657d27b351dbff4cb1732ab9)

## 2022.7

`2022-01-19` | [1ab8ecb547...c1a735c644](https://github.com/OneGov/onegov-cloud/compare/1ab8ecb547^...c1a735c644)

### Election Day

##### Allows SMS to be sent to multiple recipients at once.

`Feature` | [155](https://github.com/onegov/onegov-cloud/issues/155) | [936c6fc4f7](https://github.com/onegov/onegov-cloud/commit/936c6fc4f713cdb1519b2e06efb6c2d4e17eed18)

##### Fixes purging old SVGs and PDFs for large numbers not possible.

`Bugfix` | [35b5389362](https://github.com/onegov/onegov-cloud/commit/35b5389362335bb50641365f139aaffe98d8aca1)

### Town6

##### Remove margin of alert-box on homepage.

`Bugfix` | [OGC-202](https://linear.app/onegovcloud/issue/OGC-202) | [1ab8ecb547](https://github.com/onegov/onegov-cloud/commit/1ab8ecb547c6ac61d80af9af4caab47a47e88ed4)

##### Link images from events on the home page.

`Bugfix` | [OGC-203](https://linear.app/onegovcloud/issue/OGC-203) | [a8daa373a8](https://github.com/onegov/onegov-cloud/commit/a8daa373a82b4a7272191ae4c787b2af19980dfc)

## 2022.6

`2022-01-18` | [0c38fb0d05...98e29a2470](https://github.com/OneGov/onegov-cloud/compare/0c38fb0d05^...98e29a2470)

### Election Day

##### Add map to election compound districts view.

`Feature` | [OGC-163](https://linear.app/onegovcloud/issue/OGC-163) | [0c38fb0d05](https://github.com/onegov/onegov-cloud/commit/0c38fb0d051f519cda592488a006af7901f667f9)

##### Add a management view for clearing the SVGs and PDFs of an election, election compound or vote.

`Feature` | [172c03e0d8](https://github.com/onegov/onegov-cloud/commit/172c03e0d828ccb6ee851b68a63aa4084d2be114)

##### Use a DB column for the last result change timespamps.

Requires to run the update-last-result-change CLI command after upgrading.

`Feature` | [OGC-151](https://linear.app/onegovcloud/issue/OGC-151) | [d95b9bca40](https://github.com/onegov/onegov-cloud/commit/d95b9bca4057d6925d392b46bf6d603ca2938fa5)

##### Add last modified headers to all embeded views.

`Bugfix` | [OGC-231](https://linear.app/onegovcloud/issue/OGC-231) | [854acc118b](https://github.com/onegov/onegov-cloud/commit/854acc118bcfbbfa0167ecc7f56a69766eac27e4)

##### Hides districts in PDFs of regional elections.

`Bugfix` | [OGC-232](https://linear.app/onegovcloud/issue/OGC-232) | [ab69b8152c](https://github.com/onegov/onegov-cloud/commit/ab69b8152c5a5e203ddc3ee68931c2cb8f6afb70)

##### Avoid SVG and PDF name collisions in elections and election compounds.

`Bugfix` | [3d1b3dfc12](https://github.com/onegov/onegov-cloud/commit/3d1b3dfc1283883852c9c7f3e5c82c047eec6987)

##### Avoid raising errors in generate media, they will likely never be seen.

`Bugfix` | [b5ae9f2375](https://github.com/onegov/onegov-cloud/commit/b5ae9f237589710b3f54ec47016afa06d99757e6)

##### Avoid re-creating PDFs and SVGs when setting an earlier date than the last modification date.

`Bugfix` | [2c589dc418](https://github.com/onegov/onegov-cloud/commit/2c589dc41810bfcdf92647c0b35e26dd4f28764d)

## 2022.5

`2022-01-16` | [a545c14565...5b115ef214](https://github.com/OneGov/onegov-cloud/compare/a545c14565^...5b115ef214)

### Election Day

##### Add new domains for regional Elections.

`Feature` | [OGC-166](https://linear.app/onegovcloud/issue/OGC-166) | [a545c14565](https://github.com/onegov/onegov-cloud/commit/a545c14565e99c78bb0fce63e0c31ed00733db99)

## 2022.4

`2022-01-13` | [e3c0bff5a8...4752b36a5d](https://github.com/OneGov/onegov-cloud/compare/e3c0bff5a8^...4752b36a5d)

### Swissvotes

##### Hide press articles in full-text search results.

`Bugfix` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [e3c0bff5a8](https://github.com/onegov/onegov-cloud/commit/e3c0bff5a8df3056cd47800c531ef7caba89c361)

##### Updates translations.

`Other` | [SWI-16](https://linear.app/swissvotes/issue/SWI-16) | [770ad7e3c8](https://github.com/onegov/onegov-cloud/commit/770ad7e3c81fcb0b78f1d0ae26a4a63941d0e630)

##### Hide campaign material with no metadata in full-text search results. Always show them when logged-in.

`Bugfix` | [SWI-16](https://linear.app/swissvotes/issue/SWI-16) | [2fbeb92b02](https://github.com/onegov/onegov-cloud/commit/2fbeb92b020e0cc9689966c06f0eee67edb937ec)

## 2022.3

`2022-01-09` | [642818ca15...82ad29c86f](https://github.com/OneGov/onegov-cloud/compare/642818ca15^...82ad29c86f)

### Swissvotes

##### Split importing campaign material in multiple transactions.

`Feature` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [c1e5f4ef0e](https://github.com/onegov/onegov-cloud/commit/c1e5f4ef0ee43bb50a1969c12c1ff6a3d61363d0)

##### Update translations.

`Other` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [642818ca15](https://github.com/onegov/onegov-cloud/commit/642818ca15ca76f4534b916d6cf6271ab436907c)

## 2022.2

`2022-01-07` | [f7e892211d...22a8a3665a](https://github.com/OneGov/onegov-cloud/compare/f7e892211d^...22a8a3665a)

### Org

##### Add options to hide the online counter and reserverations link on the homepage.

`Feature` | [OGC-212](https://linear.app/onegovcloud/issue/OGC-212) | [f7e892211d](https://github.com/onegov/onegov-cloud/commit/f7e892211dda171317462ddc2545d5f6ed8dad1b)

## 2022.1

`2022-01-04` | [62416c3a0f...9fabebc6ee](https://github.com/OneGov/onegov-cloud/compare/62416c3a0f^...9fabebc6ee)

### Election Day

##### Add year 2022.

`Feature` | [OGC-225](https://linear.app/onegovcloud/issue/OGC-225) | [4bd51d99dd](https://github.com/onegov/onegov-cloud/commit/4bd51d99dd037b5be07c17bf019393fd0810d8dd)

##### Add static data for regions and superregions.

`Feature` | [OGC-164](https://linear.app/onegovcloud/issue/OGC-164) | [c0be59074d](https://github.com/onegov/onegov-cloud/commit/c0be59074d3c0a43f39503c37bac9b98d9ea84fc)

##### Remove Bodensee from mapdata.

`Bugfix` | [OGC-148](https://linear.app/onegovcloud/issue/OGC-148) | [ed069923c3](https://github.com/onegov/onegov-cloud/commit/ed069923c31fa0e8ba5cb201a928919130aa53eb)

### Swissvotes

##### Don't allow to download press article for copyright reasons.

`Feature` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [6fbab571af](https://github.com/onegov/onegov-cloud/commit/6fbab571afff266fc83732780bb4b1922eb4ea9d)

##### Update translations.

`Bugfix` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [62416c3a0f](https://github.com/onegov/onegov-cloud/commit/62416c3a0f631d0eed77e392598a99b6fa67b14f)

## 2021.101

`2021-12-29` | [d7e8950d11...d7e8950d11](https://github.com/OneGov/onegov-cloud/compare/d7e8950d11^...d7e8950d11)

## 2021.100

`2021-12-29` | [14d227380f...212583fb9d](https://github.com/OneGov/onegov-cloud/compare/14d227380f^...212583fb9d)

## 2021.99

`2021-12-22` | [6cebe417d2...579dbd0974](https://github.com/OneGov/onegov-cloud/compare/6cebe417d2^...579dbd0974)

## 2021.98

`2021-12-22` | [35e78c3645...34dc2ac0a5](https://github.com/OneGov/onegov-cloud/compare/35e78c3645^...34dc2ac0a5)

### Election Day

##### Add date to screen dropdown menus.

`Feature` | [OGC-173](https://linear.app/onegovcloud/issue/OGC-173) | [663f2c1adc](https://github.com/onegov/onegov-cloud/commit/663f2c1adc83ab30fd6ff6a8666fa7d6c541f4aa)

##### Add screens export.

`Feature` | [OGC-181](https://linear.app/onegovcloud/issue/OGC-181) | [a14f57fb02](https://github.com/onegov/onegov-cloud/commit/a14f57fb021f5dfc66d5235dc3c5a1e2bb786f06)

### Feriennet

##### Update translations.

`Other` | [PRO-946](https://linear.app/projuventute/issue/PRO-946) | [e6efa3e617](https://github.com/onegov/onegov-cloud/commit/e6efa3e61772f1ffea75651d3e8f1e2899f05232)

### Swissvotes

##### Fixes language of attachments not being translate in the search.

`Bugfix` | [92f96dc9bd](https://github.com/onegov/onegov-cloud/commit/92f96dc9bdb112b76caacec81d353cf2a4bda18b)

## 2021.97

`2021-12-08` | [b14a8d105b...182ae78670](https://github.com/OneGov/onegov-cloud/compare/b14a8d105b^...182ae78670)

### Election Day

##### Make party panachage view on compounds configurable.

`Feature` | [OGC-165](https://linear.app/onegovcloud/issue/OGC-165) | [09b7462f11](https://github.com/onegov/onegov-cloud/commit/09b7462f1186e49c775b7c4581c49731016a3cd9)

##### Don't show districts for regional elections.

`Other` | [OGC-30](https://linear.app/onegovcloud/issue/OGC-30) | [b14a8d105b](https://github.com/onegov/onegov-cloud/commit/b14a8d105b01e7a5c8845cba31cae26a92d0dbbf)

##### Make aggretaed lists view of election compounds optional. Also add a warning because this view is not meaningful.

`Bugfix` | [OGC-40](https://linear.app/onegovcloud/issue/OGC-40) | [65ec908289](https://github.com/onegov/onegov-cloud/commit/65ec9082899f67bb127063f0f35db67b03ec699f)

### Swissvotes

##### Update full-text search.

`Feature` | [SWI-16](https://linear.app/swissvotes/issue/SWI-16) | [ea8856d556](https://github.com/onegov/onegov-cloud/commit/ea8856d556336482a50499cd8ee45067a4514c04)

## 2021.96

`2021-12-08` | [01e1b2652d...1a0a0c1d30](https://github.com/OneGov/onegov-cloud/compare/01e1b2652d^...1a0a0c1d30)

### Election Day

##### Add links to votes, elections, election compounds to breadcrumbs.

`Feature` | [OGC_30](#OGC_30) | [0c19358eb8](https://github.com/onegov/onegov-cloud/commit/0c19358eb87b0abb85d8194bcc22eea1eda08c1d)

### Org

##### Fix setting bold problem with Chrome.

`Feature` | [OGC-138](https://linear.app/onegovcloud/issue/OGC-138) | [81a267b69d](https://github.com/onegov/onegov-cloud/commit/81a267b69d0a3a57b784891e925d1e380a24da90)

### Swissvotes

##### Adds english fall back for full-text search and use less strict language handling.

`Feature` | [SWI-16](https://linear.app/swissvotes/issue/SWI-16) | [d43b010753](https://github.com/onegov/onegov-cloud/commit/d43b0107539e7aaec7b6cff2df86c060a81c22bc)

### Town6

##### Fix problem with SVG without width not showing.

`Bugfix` | [OGC-156](https://linear.app/onegovcloud/issue/OGC-156) | [01e1b2652d](https://github.com/onegov/onegov-cloud/commit/01e1b2652d6ba2ced1e8da4674de54a0a7665501)

## 2021.95

`2021-12-05` | [93aa02d789...0723514278](https://github.com/OneGov/onegov-cloud/compare/93aa02d789^...0723514278)

### Swissvotes

##### Add document full-text search to votes.

`Feature` | [SWI-16](https://linear.app/swissvotes/issue/SWI-16) | [93aa02d789](https://github.com/onegov/onegov-cloud/commit/93aa02d7892396bb2975eccab9e78005ad92cb7a)

## 2021.94

`2021-12-02` | [1f20e02e1b...fc7802f4dd](https://github.com/OneGov/onegov-cloud/compare/1f20e02e1b^...fc7802f4dd)

### Core

##### Allow table elements in HTML sanitation.

`Bugfix` | [OGC-131](https://linear.app/onegovcloud/issue/OGC-131) | [ac95559cc6](https://github.com/onegov/onegov-cloud/commit/ac95559cc6e2b235baedb40869b9616980c734a8)

### Swissvotes

##### Show tie-breaker positions in the bar chart.

`Bugfix` | [SWI-25](https://linear.app/swissvotes/issue/SWI-25) | [ff973db631](https://github.com/onegov/onegov-cloud/commit/ff973db631d6022cdb0b7c45a4b7231ffa9a33b0)

## 2021.93

`2021-12-01` | [2388f01b4a...f3cfb23787](https://github.com/OneGov/onegov-cloud/compare/2388f01b4a^...f3cfb23787)

### Feriennet

##### Add payment date to export.

`Feature` | [PRO-946](https://linear.app/projuventute/issue/PRO-946) | [42631665c2](https://github.com/onegov/onegov-cloud/commit/42631665c2cf82de94268a3d42f31f85507ad1df)

### Org

##### Add tables to editor.

`Feature` | [OGC-131](https://linear.app/onegovcloud/issue/OGC-131) | [6338d15748](https://github.com/onegov/onegov-cloud/commit/6338d1574860f2257435a314e243b1df45122315)

##### Add categories to forms and resources.

`Feature` | [OGC-140](https://linear.app/onegovcloud/issue/OGC-140) | [ba2a63d909](https://github.com/onegov/onegov-cloud/commit/ba2a63d9092eec669c6b1488ffc3b39c18050c19)

### Swissvotes

##### Index campaign material for full text search.

Addionally, store text extracts per file.

`Feature` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [2388f01b4a](https://github.com/onegov/onegov-cloud/commit/2388f01b4a9c5eb951ca35c0cde5b6ee998c7c32)

##### Add ordering to campaign material.

`Other` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [29eb157d85](https://github.com/onegov/onegov-cloud/commit/29eb157d858af9ca746e9a0601a5ad309c65dd85)

