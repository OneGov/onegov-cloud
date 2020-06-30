# Changes

## Release `2020.63`

> commits: **1 / [e0b7235d3f...e0b7235d3f](https://github.com/OneGov/onegov-cloud/compare/e0b7235d3f^...e0b7235d3f)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.63)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🐞 **Audit Improvements I**

Fixes audit query, fixes non-localized course event repr, Adaptions for audit reports

**`Bugfix`** | **[e0b7235d3f](https://github.com/onegov/onegov-cloud/commit/e0b7235d3f95d63296c662b029ecb37bbe79a60a)**

## Release `2020.62`

> released: **2020-06-26 12:20**<br>
> commits: **10 / [7aee249d6c...86888f7f6b](https://github.com/OneGov/onegov-cloud/compare/7aee249d6c^...86888f7f6b)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.62)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🐞 **Ensure user not existing when adding external attendee**

**`Bugfix`** | **[5ae103fd1e](https://github.com/onegov/onegov-cloud/commit/5ae103fd1eb4e14bf914f9480ae66a6bc6faa154)**

## Release `2020.61`

> released: **2020-06-24 15:00**<br>
> commits: **9 / [391cbd795e...4c39b3bbb6](https://github.com/OneGov/onegov-cloud/compare/391cbd795e^...4c39b3bbb6)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.61)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🐞 **Fixes billing reset not possible when not in booking phase**

**`Bugfix`** | **[391cbd795e](https://github.com/onegov/onegov-cloud/commit/391cbd795e78590db7ddd6c729eadd2544ae9cef)**

### Fsi

✨ **Fixes caching for last chosen organisations in /audit**

Needs to be a Post request form in order to set and get cache.
Mimic a Get request by redirecting the user to the new collection.

**`Other`** | **[4977e43af0](https://github.com/onegov/onegov-cloud/commit/4977e43af0daeb6ef3474c0bfac689253fbf7a6d)**

🐞 **Fixes rendering pdf for all subscriptions**

**`Bugfix`** | **[5951a6db01](https://github.com/onegov/onegov-cloud/commit/5951a6db01b01e8701441a38ae316f8dd182548b)**

## Release `2020.60`

> released: **2020-06-18 20:22**<br>
> commits: **8 / [f2626f8640...c00ab10ea4](https://github.com/OneGov/onegov-cloud/compare/f2626f8640^...c00ab10ea4)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.60)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🐞 **Fixes volunteer query**

Fixes query for volunteers on /attendees/{activity_name}

**`Bugfix`** | **[f2626f8640](https://github.com/onegov/onegov-cloud/commit/f2626f8640e1d0029eebd0ed5f8d76808dbcd9f2)**

### Org

🐞 **Fixes bug where file entry is not None but an empty dict**

**`Bugfix`** | **[05c68af4cf](https://github.com/onegov/onegov-cloud/commit/05c68af4cf303df706cbcb1f37a48e5c1143391d)**

🐞 **Prevents elastic from failing if user inputs string > 1001 letters**

**`Bugfix`** | **[77bf467959](https://github.com/onegov/onegov-cloud/commit/77bf46795910e839c799c8c8e645610075326e91)**

## Release `2020.59`

> released: **2020-05-27 08:09**<br>
> commits: **14 / [bb363d6795...1ad7db4cd5](https://github.com/OneGov/onegov-cloud/compare/bb363d6795^...1ad7db4cd5)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.59)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🐞 **Fixes ensurance validation error**

**`Bugfix`** | **[5eb3ef1444](https://github.com/onegov/onegov-cloud/commit/5eb3ef1444b756f08cc4aa2f10ba142578cfbf66)**

### Org

🐞 **Fixes withdrawing an imported event.py**

- adapt breadcrumbs for event detail view
- allow submitted events to be withdrawn
- Change translations "Delete" to "Withdraw" on detail page

**`Bugfix`** | **[c7bccd3fa9](https://github.com/onegov/onegov-cloud/commit/c7bccd3fa966fa5f8a83f1ca5562b4ecb08e7f64)**

🐞 **Fixes creating ticket message**

- Fix case where an event is withdrawn where there isn't a ticket
- imported events can have no ticket but can be withdrawn

**`Bugfix`** | **[7fdc7123dc](https://github.com/onegov/onegov-cloud/commit/7fdc7123dc30345b13ebe84a58b442640f1ed27b)**

🐞 **Ensure DirectoryFile for all files on a DirectoryEntry**

Uploaded files by form submissions resulted in FormFile attached to DirectoryEntry's.
When adopting an entry from a submission, add references as DirectoryFile.
Test manually also for change requests of the files.

**`Bugfix`** | **[3735433747](https://github.com/onegov/onegov-cloud/commit/3735433747c70f67f67c04deef5d8a7c998055de)**

## Release `2020.58`

> released: **2020-05-19 15:14**<br>
> commits: **3 / [6f3e950596...e85d32ce84](https://github.com/OneGov/onegov-cloud/compare/6f3e950596^...e85d32ce84)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.58)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.57`

> released: **2020-05-14 13:19**<br>
> commits: **2 / [48e335c296...548ccf0690](https://github.com/OneGov/onegov-cloud/compare/48e335c296^...548ccf0690)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.57)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Minor adjustments Rega Widget**

- remove italic font
- place logo bottom right aligned with text
- removes ":" in title

**`Feature`** | **[48e335c296](https://github.com/onegov/onegov-cloud/commit/48e335c29652df7bdd23a24e3e5082835f9303e2)**

## Release `2020.56`

> released: **2020-05-13 15:04**<br>
> commits: **7 / [38feae1527...94c40f3668](https://github.com/OneGov/onegov-cloud/compare/38feae1527^...94c40f3668)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.56)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds rega widget and bugfixes**

Adds rega banner for rega partnership to /my-bookings

Fixes changing booking start when period was setup without wishing phase (FER-861). Fixes allowing children to book if they were at max age during the year of the occasion (FER-863).

**`Feature`** | **[FER-718](https://issues.seantis.ch/browse/FER-718)** | **[2c8cd1d128](https://github.com/onegov/onegov-cloud/commit/2c8cd1d128888a7ef965fbb696983e0ee8022f3a)**

### Swissvotes

🐞 **Updates poster urls consequently**

Replace all the image url consequently on update. Fixes removing poster url when source was removed

**`Bugfix`** | **[ef626cbfbe](https://github.com/onegov/onegov-cloud/commit/ef626cbfbe619a62622c31bddc1d0c5ccefcdef8)**

🐞 **Changes order of posters ot the one in the dataset**

**`Bugfix`** | **[5090c09252](https://github.com/onegov/onegov-cloud/commit/5090c092528e466acc4488f294078fdb7a2828b5)**

## Release `2020.55`

> released: **2020-05-11 08:33**<br>
> commits: **3 / [c04602a89d...c7ec8af976](https://github.com/OneGov/onegov-cloud/compare/c04602a89d^...c7ec8af976)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.55)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Improves ticket email sending**

Minor fixes and tests.

**`Bugfix`** | **[8a1988818c](https://github.com/onegov/onegov-cloud/commit/8a1988818cf721543ff17ffd3f8a106914d03fe6)**

## Release `2020.54`

> released: **2020-05-06 23:32**<br>
> commits: **2 / [a588f63b57...442c4e9775](https://github.com/OneGov/onegov-cloud/compare/a588f63b57^...442c4e9775)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.54)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Global settings for the ticket email system (automatic handling)**

Adds Ticket settings to organisation model. Two status emails for tickets can be configured individually. Adds feature to automatically close tickets and accept events (EVN) and reservations (RSV).

**`Feature`** | **[a588f63b57](https://github.com/onegov/onegov-cloud/commit/a588f63b57828a31d11ceb1066fe1b54cacb61b3)**

## Release `2020.53`

> released: **2020-05-06 10:29**<br>
> commits: **5 / [2d4cd916d4...dde751266e](https://github.com/OneGov/onegov-cloud/compare/2d4cd916d4^...dde751266e)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.53)](https://buildkite.com/seantis/onegov-cloud)

### Event

🎉 **Adds ticket creation for fetch cli for events**

- Switch to import only published events
- Flags for state transfer if existing
- flag to automatically close or delete tickets of purged events
- Adapted UI for tickets of imported events
- moves cli to org due to app hierarchy

**`Feature`** | **[VER-1](https://kanton-zug.atlassian.net/browse/VER-1)** | **[1f89845b6b](https://github.com/onegov/onegov-cloud/commit/1f89845b6bda80cb83712dad5a377072c2880afb)**

## Release `2020.52`

> released: **2020-05-05 08:28**<br>
> commits: **3 / [30dd5086f9...e7545454a7](https://github.com/OneGov/onegov-cloud/compare/30dd5086f9^...e7545454a7)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.52)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds reservation quota for room resource**

Adds a quota for allocations of Rooms so that multiple reservations per time slot are possible. If the time slot can be booked partially, the quota will be set to 1. Limit edit possiblities for allocations set to `partly_available`. Adds form validation for `EditRoomAllocationForm`.

**`Feature`** | **[30dd5086f9](https://github.com/onegov/onegov-cloud/commit/30dd5086f9315ebbfa9ab6bf30eef8519149a1cc)**

## Release `2020.51`

> released: **2020-04-30 14:15**<br>
> commits: **5 / [d22727d4ae...651af27668](https://github.com/OneGov/onegov-cloud/compare/d22727d4ae^...651af27668)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.51)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🐞 **Hides /districts tab for sz for 2020 ongoing**

The districts tab should be hidden for votes if all entities are districts.
Solves Problem of wrong label "Districts" in a vote with date 2020,
but results using the entities from 2016.

**`Bugfix`** | **[7de0e43cec](https://github.com/onegov/onegov-cloud/commit/7de0e43cec122dcda5f7615dfafcc37f7dab46d2)**

### Onegov

🐞 **Minor bugfixes and improved form validation**

- changes the lint step to be more rigorous
- Added additional form validations
- deactives password reset for fsi application as default
- adds app.disable_password_reset for org applications

**`Bugfix`** | **[35094d589a](https://github.com/onegov/onegov-cloud/commit/35094d589a225399ddf4bd02a8cda60725f615f5)**

## Release `2020.50`

> released: **2020-04-27 11:01**<br>
> commits: **7 / [41923b358d...4ff04c134a](https://github.com/OneGov/onegov-cloud/compare/41923b358d^...4ff04c134a)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.50)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.49`

> released: **2020-04-24 09:33**<br>
> commits: **5 / [f0b15642c0...df0c831228](https://github.com/OneGov/onegov-cloud/compare/f0b15642c0^...df0c831228)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.49)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Adds migration FormFiles to DirectoryFiles**

Files uploaded with a UploadField defined in a directory are added as DiretoryFile. Migrates FormFiles attached to DirectoryEntries in order to be accessed as anon user in a public DirectoryEntry.

**`Bugfix`** | **[ONEGOV-10](#ONEGOV-10)** | **[6c446639c3](https://github.com/onegov/onegov-cloud/commit/6c446639c3fa7bcb51f296d01200a81e83cd6724)**

## Release `2020.48`

> released: **2020-04-22 23:06**<br>
> commits: **3 / [30952ea2bd...1a9e507db6](https://github.com/OneGov/onegov-cloud/compare/30952ea2bd^...1a9e507db6)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.48)](https://buildkite.com/seantis/onegov-cloud)

### Swissvotes

🎉 **Add poster of eMuesum.ch**

- Import of poster urls from dataset
- responsive Image gallery (not IE 11 supported)
- Routine to fetch image urls for posters and save them to the database
- changed translation "Schlagwort"
- hint for Internet Explorer uses

**`Feature`** | **[VOTES-71](https://issues.seantis.ch/browse/VOTES-71)** | **[1796883d6b](https://github.com/onegov/onegov-cloud/commit/1796883d6b6cac664a341dc86dcd7f46037a15ca)**

## Release `2020.47`

> released: **2020-04-22 12:01**<br>
> commits: **2 / [7b09649188...89895df1d1](https://github.com/OneGov/onegov-cloud/compare/7b09649188^...89895df1d1)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.47)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.46`

> released: **2020-04-22 10:15**<br>
> commits: **5 / [fa03e0d4ef...347cc50438](https://github.com/OneGov/onegov-cloud/compare/fa03e0d4ef^...347cc50438)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.46)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Additional Directory Optimisations**

- adds image popup to thumbnails on a entry
- Fixes uppercase footer label for custom link
- Adds comment button to formcode toolbar

**`Feature`** | **[ONEGOV-5](#ONEGOV-5)** | **[c20b8a380a](https://github.com/onegov/onegov-cloud/commit/c20b8a380a88500ff9b3648c96c9f5c42bf51796)**

## Release `2020.45`

> released: **2020-04-09 10:20**<br>
> commits: **6 / [eb6b6612a6...1a13643021](https://github.com/OneGov/onegov-cloud/compare/eb6b6612a6^...1a13643021)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.45)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds field descriptions to Formcode**

Underneath formcode fields using same identation, the field description can be defined using `<< ...>>`.

**`Feature`** | **[73ecd5f505](https://github.com/onegov/onegov-cloud/commit/73ecd5f505d7ae358113619c20407192546b9b01)**

🎉 **Adds default font family set**

Adds fonts Arial, Verdana, Courier New, and Google fonts LatoWeb, Roboto and OpenSans.

**`Feature`** | **[3d1906e45a](https://github.com/onegov/onegov-cloud/commit/3d1906e45a3a161070d020445e26edf63ec4ef36)**

🎉 **Adds keyword count for available filters**

Adds a count per keyword for all visible models on `/directories/{directory_name}`.

**`Feature`** | **[9f056dae17](https://github.com/onegov/onegov-cloud/commit/9f056dae1781f5d2cb27f2fe7db9525ec7c38bb4)**

🎉 **Adds display as thumbnail on DirectoryConfiguration**

For UploadFields defined in formcode, one can choose to display if a field should be shown as thumbnail on an director entry.

**`Feature`** | **[15a3924914](https://github.com/onegov/onegov-cloud/commit/15a3924914b2d29c5457d99d5fffffb949d25280)**

## Release `2020.44`

> released: **2020-04-04 07:07**<br>
> commits: **4 / [6fac7588d4...c4216ba2b2](https://github.com/OneGov/onegov-cloud/compare/6fac7588d4^...c4216ba2b2)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.44)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🐞 **Fixes label districts for sz for pre 2020**

**`Bugfix`** | **[1efc88aa9a](https://github.com/onegov/onegov-cloud/commit/1efc88aa9ac7302ee8970494396cfbe8f012c814)**

### Feriennet

🐞 **Fixes division by zero error**

**`Bugfix`** | **[cf8d7187c5](https://github.com/onegov/onegov-cloud/commit/cf8d7187c55cd021456fac8a9fc8fe34aefe60e5)**

### Org

🎉 **Integrates js counter for maximum length**

Integrates server-side length validation with a javascript counter for formcode fields.

**`Feature`** | **[6fac7588d4](https://github.com/onegov/onegov-cloud/commit/6fac7588d4f288a29a2ee1085e0caed3a0a36755)**

## Release `2020.43`

> released: **2020-04-02 13:00**<br>
> commits: **4 / [94b3e7b77b...7753e17809](https://github.com/OneGov/onegov-cloud/compare/94b3e7b77b^...7753e17809)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.43)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds font choices in general-settings**

New sans-serif fonts can be included by placing them as scss files in `theme/fonts`. 
The font family for a file is derived from it's filename which must be congruent
to the css syntax. They are not lazy loaded, but will be cached by the browser.

**`Feature`** | **[6a6d5ef60b](https://github.com/onegov/onegov-cloud/commit/6a6d5ef60b4ea912ed3b1aad769714d86b864497)**

🎉 **Adds 3 static custom footer links**

**`Feature`** | **[1be0f28e91](https://github.com/onegov/onegov-cloud/commit/1be0f28e9195a0be087cf9d3183c5b8b6860dc63)**

🐞 **Fixes File publish date**

**`Bugfix`** | **[94b3e7b77b](https://github.com/onegov/onegov-cloud/commit/94b3e7b77b3f16c63de3f41b9833fff40e26d922)**

## Release `2020.42`

> released: **2020-03-30 16:39**<br>
> commits: **4 / [17ab53cb70...434fc835ea](https://github.com/OneGov/onegov-cloud/compare/17ab53cb70^...434fc835ea)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.42)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🐞 **Fixes cancel link**

**`Bugfix`** | **[bedbdbb12b](https://github.com/onegov/onegov-cloud/commit/bedbdbb12b8822c0e1cccfa70cba12e67266ffa6)**

### Org

🐞 **Improves homepage alert and alert padding**

**`Bugfix`** | **[55a7ebe664](https://github.com/onegov/onegov-cloud/commit/55a7ebe664e46ad1011a637d75c807e3766df6e7)**

## Release `2020.41`

> released: **2020-03-26 07:59**<br>
> commits: **6 / [6457276d64...606c9f0995](https://github.com/OneGov/onegov-cloud/compare/6457276d64^...606c9f0995)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.41)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.40`

> released: **2020-03-24 13:01**<br>
> commits: **4 / [3b28334755...dc30694a00](https://github.com/OneGov/onegov-cloud/compare/3b28334755^...dc30694a00)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.40)](https://buildkite.com/seantis/onegov-cloud)

### Town

🎉 **Adds eUmzug Label and Url**

- Hide this entry if no url is defined
- add the default e-move url when creating new town app

**`Feature`** | **[8db8a825f7](https://github.com/onegov/onegov-cloud/commit/8db8a825f7b98449b5b9b7ccd202403325b8d347)**

## Release `2020.39`

> released: **2020-03-23 11:46**<br>
> commits: **5 / [d83aded397...0873416984](https://github.com/OneGov/onegov-cloud/compare/d83aded397^...0873416984)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.39)](https://buildkite.com/seantis/onegov-cloud)

### Core

🎉 **Replaces pyreact with dukpy as jsx compiler**

Replaces depreceated pyreact library.

**`Feature`** | **[f0f777bdb8](https://github.com/onegov/onegov-cloud/commit/f0f777bdb8c10a0b4f414df700c1f9df2c702060)**

### Feriennet

✨ **Minor Fixes**

- Fixes unclosed html tag
- Fixes not hiding past dates on /activities/volunteer
- Show links on occasion to rescind even if billing has been done (=> period.finalized is True)
- Fixes non-localized date on /volunteer-cart

**`Other`** | **[93a3a18f1d](https://github.com/onegov/onegov-cloud/commit/93a3a18f1dae39e29bcad9eaf9c9ad50c318d971)**

## Release `2020.38`

> released: **2020-03-18 12:10**<br>
> commits: **2 / [ff8d897a2d...46625efdf3](https://github.com/OneGov/onegov-cloud/compare/ff8d897a2d^...46625efdf3)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.38)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🎉 **Modifies ElectionCompound list view**

If the ElectionCompound is after_pukelsheim, hides by default the votes from the list table on the ElectionCompound. Also if after_pukelheim, the bar chart shows only the mandates not the sum of all ListResult.votes.

**`Feature`** | **[ff8d897a2d](https://github.com/onegov/onegov-cloud/commit/ff8d897a2da2cd561979033a05c1ec6064f054e6)**

## Release `2020.37`

> released: **2020-03-17 12:16**<br>
> commits: **3 / [20f716cc1e...79aa0463c3](https://github.com/OneGov/onegov-cloud/compare/20f716cc1e^...79aa0463c3)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.37)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🐞 **Fixes form field depends_on boolean value**

**`Bugfix`** | **[537cde1080](https://github.com/onegov/onegov-cloud/commit/537cde10803d592cb7151597b98a75d3ef0267f5)**

## Release `2020.36`

> released: **2020-03-17 11:19**<br>
> commits: **4 / [c5769b4cb3...ed50ff6709](https://github.com/OneGov/onegov-cloud/compare/c5769b4cb3^...ed50ff6709)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.36)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Adds cli tool to fix german tags for OccurrenceMixin**

Imported tags were not coherent with tags defined in forms. Adds a tool to identify german words that are in the database even when translations exist. Identifies also unknown translations.

**`Bugfix`** | **[ZW-264](https://kanton-zug.atlassian.net/browse/ZW-264)** | **[c5769b4cb3](https://github.com/onegov/onegov-cloud/commit/c5769b4cb3c68522d24689984fa86338c4532692)**

🐞 **Fixes not using localized date in Ticket.subtitle**

Fixes not using localized time in Ticket.subtitle, updated by EventSubmissionHandler.

**`Bugfix`** | **[ZW-268](https://kanton-zug.atlassian.net/browse/ZW-268)** | **[b2ef85d50c](https://github.com/onegov/onegov-cloud/commit/b2ef85d50c2d81e6b9d4dfa9e64a46af4ea536f0)**

## Release `2020.35`

> released: **2020-03-16 13:23**<br>
> commits: **2 / [680a480bf7...163cb11542](https://github.com/OneGov/onegov-cloud/compare/680a480bf7^...163cb11542)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.35)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🎉 **Adds Doppelter Pukelsheim and Adaptions for Kt. SZ**

- Adds CheckBox Doppelter Pukelsheim to Election and ElectionCompound
- Adds Feature to mark elections as completed when a common ElectionCompound
for Doppelter Pukelsheim
- Adds lists and statistics tab to CompoundElection
- Adds feature to hide any tab in votes, elections and election compound
- Adds Cli helpter tool

**`Feature`** | **[680a480bf7](https://github.com/onegov/onegov-cloud/commit/680a480bf7cb43e6820cbb6136b1b041319e732f)**

## Release `2020.34`

> released: **2020-03-11 16:34**<br>
> commits: **2 / [9dceb83c5b...c0a99cf250](https://github.com/OneGov/onegov-cloud/compare/9dceb83c5b^...c0a99cf250)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.34)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🎉 **Adaptions for SZ Elections**

In SZ since 2020, entity and district are named the same. For elections of a compound (Kantonsratswahl), the UI has to be changed.

- Changes canton district label starting 2020 using translations
- Introduces property `district_are_entities` on `ElectionLayout`
- Changes `statistics_table` to remove district column if `district_are_entities`  is True
- Hides `candidate-by-district` if `district_are_entities` is True (the are the same)
- Changes progress macro to display e.g. "Yes" instead of "1 of 1" if flagged

**`Feature`** | **[9dceb83c5b](https://github.com/onegov/onegov-cloud/commit/9dceb83c5b01dc2f128bcaf8fa9b08d00575edad)**

## Release `2020.33`

> released: **2020-03-11 11:40**<br>
> commits: **2 / [9e784ae306...4a00e596e6](https://github.com/OneGov/onegov-cloud/compare/9e784ae306^...4a00e596e6)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.33)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.32`

> released: **2020-03-11 09:13**<br>
> commits: **16 / [1cbd5352e8...3991fa1380](https://github.com/OneGov/onegov-cloud/compare/1cbd5352e8^...3991fa1380)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.32)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.31`

> released: **2020-03-10 08:12**<br>
> commits: **2 / [10b8e57d50...b5760ebe22](https://github.com/OneGov/onegov-cloud/compare/10b8e57d50^...b5760ebe22)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.31)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

✨ **Fixes candidate percentages by-entity and by-district**

Majorz by district is using accounted_votes instead of accounted ballots. For proporz election, the total as devider for candidate votes is using `ListResult.votes`

**`Fix`** | **[10b8e57d50](https://github.com/onegov/onegov-cloud/commit/10b8e57d50e53cf3f5d2ce9ae5e0da30e81dbbc8)**

## Release `2020.30`

> released: **2020-03-05 16:12**<br>
> commits: **3 / [edeff88f92...ca149c611f](https://github.com/OneGov/onegov-cloud/compare/edeff88f92^...ca149c611f)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.30)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Adds new view for past events**

Editors and admins have to check attendance of attendees. Past courses are hidden from `/courses` view since the list gets too long. A new view for this purpose was introduced with `/past-events`

**`Feature`** | **[ZW-265](https://kanton-zug.atlassian.net/browse/ZW-265)** | **[636069e476](https://github.com/onegov/onegov-cloud/commit/636069e476491382fbb66a1ecbe9e83f1329b8ad)**

## Release `2020.29`

> released: **2020-03-02 19:15**<br>
> commits: **4 / [3970f94e5c...7468e0b9e4](https://github.com/OneGov/onegov-cloud/compare/3970f94e5c^...7468e0b9e4)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.29)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🎉 **Improvements for Kantons+Regierungsratswahlen**

For intermediary results, the source data might flag a candidate as elected. For the Web UI,
`allocated_mandates` (e.g. Mandates **1** of 15 in `/lists`) will now always show 0 if the election is not completed.
Also for compound election, the sum of allocated mandates will only consider completed elections. For majorz elections,
`absolute_majority` and `candidate_elected` will be None if the election is not completed viewing the results with the api (`/json` and `/data-json` views). However, when exporting as CSV the original data gets exported.

- Fixes possible division by zero (`counted_eligible_voters`)
- Removes the year at the end of compound election title (`create_wabstic_proporz`)
- Re-introduces election status `interim` for `upload_wabstic_majorz` view.

**`Feature`** | **[5f1e445093](https://github.com/onegov/onegov-cloud/commit/5f1e4450936bbcb4ce7d8cb10341a73bdfc54f63)**

## Release `2020.28`

> released: **2020-02-20 18:42**<br>
> commits: **2 / [e7f76d69a7...92296ffed5](https://github.com/OneGov/onegov-cloud/compare/e7f76d69a7^...92296ffed5)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.28)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.27`

> released: **2020-02-20 17:04**<br>
> commits: **2 / [c34ce0e627...d8d1024087](https://github.com/OneGov/onegov-cloud/compare/c34ce0e627^...d8d1024087)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.27)](https://buildkite.com/seantis/onegov-cloud)

### Org

🎉 **Adds "Further occurrences" to event search results**

- Limit to 10 future occurrences
- Least intrusive and not blowing up elasticsearch

**`Feature`** | **[ZW-260](https://kanton-zug.atlassian.net/browse/ZW-260)** | **[c34ce0e627](https://github.com/onegov/onegov-cloud/commit/c34ce0e627c13e7e44c1208c8a30cfaf71e3120e)**

## Release `2020.26`

> released: **2020-02-18 14:35**<br>
> commits: **5 / [0e7fa93022...840c5fff7a](https://github.com/OneGov/onegov-cloud/compare/0e7fa93022^...840c5fff7a)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.26)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Fixes failing upgrade with add_column_with_defaults**

Looping through columns to add a default for a not yet migrated table
caused upgrade failures. The fix will skip empty tables when adding defaults.

**`Bugfix`** | **[59174e4b85](https://github.com/onegov/onegov-cloud/commit/59174e4b858efa9b0056a49c8fa715252e11f149)**

### Org

🐞 **Fixes virtual occurence for dates 2+ years ahead**

Fixes form input "send daily ticket statistics" and error in template when seeing an event with a date that is two years from now.

**`Bugfix`** | **[6ef0d2e664](https://github.com/onegov/onegov-cloud/commit/6ef0d2e664c76f4ee2e8759677d6a84f206244dd)**

## Release `2020.25`

> released: **2020-02-13 15:42**<br>
> commits: **6 / [122cca97ab...5dc09181d1](https://github.com/OneGov/onegov-cloud/compare/122cca97ab^...5dc09181d1)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.25)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.24`

> released: **2020-02-11 17:16**<br>
> commits: **2 / [458bc88d4a...70f2f36546](https://github.com/OneGov/onegov-cloud/compare/458bc88d4a^...70f2f36546)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.24)](https://buildkite.com/seantis/onegov-cloud)

### Electionday

🎉 **Adds auto-creation of election compound / proporz elections for WabstiC**

Based on the data in `WP_Wahl` and an existing DataSource, the endpoint `/create-wabsti-proporz` will create all elections, the election compound, and the all DataSourceItems. The same DataSource can then be used to upload the results.

**`Feature`** | **[458bc88d4a](https://github.com/onegov/onegov-cloud/commit/458bc88d4aeee18a38cc0f057020505e947538f6)**

## Release `2020.23`

> released: **2020-02-10 17:25**<br>
> commits: **4 / [1a03df3bc1...d07ea4e28b](https://github.com/OneGov/onegov-cloud/compare/1a03df3bc1^...d07ea4e28b)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.23)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🐞 **Fixes cascade deletion of Volunteer if OccasionNeed is deleted**

**`Bugfix`** | **[bdededb15e](https://github.com/onegov/onegov-cloud/commit/bdededb15ed603d2a9055d7731d411850415dbbb)**

### Swissvotes

🎉 **Disables Matomo Tracking Cookie**

**`Feature`** | **[1e091f6bde](https://github.com/onegov/onegov-cloud/commit/1e091f6bde31bc8b30ee22c0351c76f80333c152)**

## Release `2020.22`

> released: **2020-02-07 10:35**<br>
> commits: **2 / [dae588359c...203ae504ed](https://github.com/OneGov/onegov-cloud/compare/dae588359c^...203ae504ed)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.22)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.21`

> released: **2020-02-05 11:05**<br>
> commits: **7 / [746ef98ff3...3effc10ba0](https://github.com/OneGov/onegov-cloud/compare/746ef98ff3^...3effc10ba0)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.21)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.20`

> released: **2020-02-03 11:42**<br>
> commits: **2 / [618d2f5aae...8dc47a99b4](https://github.com/OneGov/onegov-cloud/compare/618d2f5aae^...8dc47a99b4)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.20)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.19`

> released: **2020-02-03 11:31**<br>
> commits: **5 / [24a1bfe659...e520dc3892](https://github.com/OneGov/onegov-cloud/compare/24a1bfe659^...e520dc3892)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.19)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.18`

> released: **2020-01-30 18:29**<br>
> commits: **3 / [98512a4cf5...94fffb910d](https://github.com/OneGov/onegov-cloud/compare/98512a4cf5^...94fffb910d)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.18)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Adds auditing feature for courses**

Adds printable audit for attendee's last course subscriptions for courses with mandatory refresh.

Further changes:

- changes sorting of event in event listing
- removed long course description from emails
- hides hidden course events for editors in `/courses`

**`Feature`** | **[FSI-16](https://kanton-zug.atlassian.net/browse/FSI-16)** | **[804d25e03a](https://github.com/onegov/onegov-cloud/commit/804d25e03a19dd07d964bcdc05b0ac8601d42dfe)**

### Org

🐞 **Fixes logo being resized disproportionately**

**`Bugfix`** | **[98512a4cf5](https://github.com/onegov/onegov-cloud/commit/98512a4cf5cb24e1bbcd2084ad53bad0795ba996)**

## Release `2020.17`

> released: **2020-01-30 07:42**<br>
> commits: **8 / [2bfc0ed77a...ec65424f72](https://github.com/OneGov/onegov-cloud/compare/2bfc0ed77a^...ec65424f72)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.17)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Adds ics calender files as attachments for course events**

**`Feature`** | **[FSI-15](https://kanton-zug.atlassian.net/browse/FSI-15)** | **[20e9e2d95f](https://github.com/onegov/onegov-cloud/commit/20e9e2d95f374945c3bf5677b3fb6936fe0f1607)**

## Release `2020.16`

> released: **2020-01-28 14:14**<br>
> commits: **2 / [f60596884f...8e165127c5](https://github.com/OneGov/onegov-cloud/compare/f60596884f^...8e165127c5)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.16)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Minor improvements**

- Adds property to hide a course from the collection
- Adapted Email Template texts and translations
- order courses by name
- hides Course "Details" button for non-admins
- disables "Subscribe Button" based on other events of the selected year
- prevents selecting attendees that have already other subscriptions of same course in the same year
- adds icons for locked and hidden_from_public
- sends cancellation email when subscription is deleted
- fixes table wrapping even listing macro

**`Feature`** | **[f60596884f](https://github.com/onegov/onegov-cloud/commit/f60596884f56e9eaaebefc0330ddc785b70ed436)**

## Release `2020.15`

> released: **2020-01-28 09:51**<br>
> commits: **9 / [05f502fe6d...bb292e8e0f](https://github.com/OneGov/onegov-cloud/compare/05f502fe6d^...bb292e8e0f)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.15)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🐞 **Fixes matching error**

When limiting attendees to a low limit of occasions, an error would result in
attendees with lots of wishes not getting as many occasions as possible.

**`Bugfix`** | **[abad982bed](https://github.com/onegov/onegov-cloud/commit/abad982bed79a0780c107c05a49fe3de55a5b33c)**

🐞 **Fixes "next page" not working for volunteers**

**`Bugfix`** | **[FER-843](https://issues.seantis.ch/browse/FER-843)** | **[6af8d7bb42](https://github.com/onegov/onegov-cloud/commit/6af8d7bb425511286640c9f46ebc6b1b1af53736)**

### Org

🐞 **Fixes attribute error when setting image size**

For some images, the size cannot be determined on the server, so in this
case we just don't annotate the html.

Fixes ONEGOV-CLOUD-39B

**`Bugfix`** | **[e65bfcbeb5](https://github.com/onegov/onegov-cloud/commit/e65bfcbeb506598564a99cca27f4f7b2dce3f97e)**

🐞 **Shows a proper error when a file cannot be parsed**

This solves ONEGOV-CLOUD-3AM

**`Bugfix`** | **[8dfc4a7076](https://github.com/onegov/onegov-cloud/commit/8dfc4a7076787fce94de7032f33535a921561069)**

### Wtfs

🎉 **Extend new print styles to more reports**

**`Feature`** | **[b1b121763b](https://github.com/onegov/onegov-cloud/commit/b1b121763be840b53109ccb854af68e90b1ca609)**

## Release `2020.14`

> released: **2020-01-24 06:34**<br>
> commits: **12 / [3187fdea56...435b2985f8](https://github.com/OneGov/onegov-cloud/compare/3187fdea56^...435b2985f8)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.14)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Improve page_range resilience**

With some odd inputs, an error could be provoked.

**`Bugfix`** | **[e63a0797b0](https://github.com/onegov/onegov-cloud/commit/e63a0797b0fbafcf5dd229663ca141f48c156196)**

### Election-Day

🐞 **Fixes Status Mixin and default status for wabstic**

Fixes default status to `unknown` for election proporz/majorz and vote so that they are completed if fully counted.

**`Bugfix`** | **[d47ce90bca](https://github.com/onegov/onegov-cloud/commit/d47ce90bca2752b586cf3fd17788b5f9512a2b56)**

### Feriennet

🐞 **Fixes error in group invite**

The group invite would not work for admins, unless they entered the view
through the booking view.

**`Bugfix`** | **[3187fdea56](https://github.com/onegov/onegov-cloud/commit/3187fdea560babf3d498ba4e80e08bba917c8467)**

🐞 **Fixes division by zero error in volunteers view**

**`Bugfix`** | **[d8213704a4](https://github.com/onegov/onegov-cloud/commit/d8213704a4e1924ed23f7bea5d8ac3748d0b0093)**

🐞 **Fixes error in notifications template**

The error was caused by the lack of an active period, which is now
explicitly required.

**`Bugfix`** | **[4f65eefe32](https://github.com/onegov/onegov-cloud/commit/4f65eefe32f5032aa47ea48a5df823311b73aef7)**

### Winterthur

✨ **Update address URLs**

**`Other`** | **[8749ba7008](https://github.com/onegov/onegov-cloud/commit/8749ba7008ad7659ea62bb815feae3f0e882a88b)**

## Release `2020.13`

> released: **2020-01-22 15:32**<br>
> commits: **5 / [5b67e10c52...3906284a47](https://github.com/OneGov/onegov-cloud/compare/5b67e10c52^...3906284a47)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.13)](https://buildkite.com/seantis/onegov-cloud)

### Ferienent

🐞 **Fixes lack of rounding in dashboard**

**`Bugfix`** | **[FER-842](https://issues.seantis.ch/browse/FER-842)** | **[2541f96fb1](https://github.com/onegov/onegov-cloud/commit/2541f96fb1857375a116aeb0f18ab2d63c465f5a)**

### Feriennet

🐞 **Fixes top-header display issue**

Uses an alternative approach to text-ellipsis than before.

**`Bugfix`** | **[FER-841](https://issues.seantis.ch/browse/FER-841)** | **[5b67e10c52](https://github.com/onegov/onegov-cloud/commit/5b67e10c5206bec12e381eca4a1b5553ed42a25f)**

### Winterthur

🐞 **Fixes mission reports error**

**`Bugfix`** | **[FW-76](https://stadt-winterthur.atlassian.net/browse/FW-76)** | **[9e82805b74](https://github.com/onegov/onegov-cloud/commit/9e82805b7464eddb6b4a4645a2d868bf0c39573d)**

## Release `2020.12`

> released: **2020-01-21 17:11**<br>
> commits: **7 / [dee367655e...eabde3ad06](https://github.com/OneGov/onegov-cloud/compare/dee367655e^...eabde3ad06)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.12)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Changes wabstic import vote status reading**

Changes wabstic import for votes: `AnzGdePedent` is new indicator if `vote.status` is `interim` or `final`
unknown` as status for wabstic import is deprecated and a fallback.

**`Feature`** | **[7c65662d95](https://github.com/onegov/onegov-cloud/commit/7c65662d95153d1033bec67d78b01c8cac6d9eb6)**

### Events

🎉 **Imports sync/import**

More images are now imported and it is possible to do a clean guidle
import.

**`Feature`** | **[dd31dff4d7](https://github.com/onegov/onegov-cloud/commit/dd31dff4d791627c6f95db1b2bf5db9b5997586b)**

### Winterthur

🎉 **Use less whitespace on reports**

Some reports used quite a bit of paper due to a lot of whitespace, this
commit changes this, resulting in more compact prints.

**`Feature`** | **[2db6e4d35c](https://github.com/onegov/onegov-cloud/commit/2db6e4d35c8e8d7ba3c6737229f54488d2bebdb7)**

## Release `2020.11`

> released: **2020-01-20 16:03**<br>
> commits: **2 / [47b6879cbd...00a95b7a0a](https://github.com/OneGov/onegov-cloud/compare/47b6879cbd^...00a95b7a0a)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.11)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.10`

> released: **2020-01-20 15:36**<br>
> commits: **3 / [fe9445a220...e8a9546111](https://github.com/OneGov/onegov-cloud/compare/fe9445a220^...e8a9546111)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.10)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds a dashboard**

**`Feature`** | **[FER-78](https://issues.seantis.ch/browse/FER-78)** | **[fe9445a220](https://github.com/onegov/onegov-cloud/commit/fe9445a22024e3650893d271b506b0e00ab98bcf)**

## Release `2020.9`

> released: **2020-01-20 13:33**<br>
> commits: **2 / [05d3cc2313...df025b625e](https://github.com/OneGov/onegov-cloud/compare/05d3cc2313^...df025b625e)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.9)](https://buildkite.com/seantis/onegov-cloud)

### Activity

🐞 **Fixes upgrade script failing on some hosts**

**`Bugfix`** | **[05d3cc2313](https://github.com/onegov/onegov-cloud/commit/05d3cc2313d86911c633f593b03c64f7cc14adad)**

## Release `2020.8`

> released: **2020-01-20 13:10**<br>
> commits: **2 / [12805c2f2e...ceefca4a3f](https://github.com/OneGov/onegov-cloud/compare/12805c2f2e^...ceefca4a3f)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.8)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🐞 **Fixes calculation of election/vote turnout for intermediary results**

**`Bugfix`** | **[12805c2f2e](https://github.com/onegov/onegov-cloud/commit/12805c2f2e33e1c7d25719e7ae22cea39ea80f11)**

## Release `2020.7`

> released: **2020-01-20 10:40**<br>
> commits: **8 / [3f9d2afaac...e9160c5daa](https://github.com/OneGov/onegov-cloud/compare/3f9d2afaac^...e9160c5daa)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.7)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

✨ **Fixes some small text issues**

**`Other`** | **[FER-739](https://issues.seantis.ch/browse/FER-739)** | **[addae0f89e](https://github.com/onegov/onegov-cloud/commit/addae0f89ef18fb8206be2f24c74c89d8eaba47b)**

### Search

🐞 **Fixes search not working**

A new elasticsearch-py release broke our Elasticsearch integration. We
used a no longer valid API for a core functionality. We now switched to
a more modern (and faster) variant.

**`Bugfix`** | **[79d024f744](https://github.com/onegov/onegov-cloud/commit/79d024f744c04cbef962468832402044e0219ce3)**

## Release `2020.6`

> released: **2020-01-17 12:27**<br>
> commits: **7 / [cd726aa8df...06eadc5e75](https://github.com/OneGov/onegov-cloud/compare/cd726aa8df^...06eadc5e75)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.6)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds optional signups for occasion needs**

So far, all occasion needs were presented to volunteers. Now, only
selected ones are.

**`Feature`** | **[FER-739](https://issues.seantis.ch/browse/FER-739)** | **[802f4f0614](https://github.com/onegov/onegov-cloud/commit/802f4f06145f90d819e65e2a76c81ef7c1eeb395)**

### Org

🎉 **Adds new categories for events**

**`Feature`** | **[60918b0b94](https://github.com/onegov/onegov-cloud/commit/60918b0b9491c2df51afd557c2a40627e18f5f15)**

## Release `2020.5`

> released: **2020-01-16 12:14**<br>
> commits: **3 / [0e6ae7daf1...e305d77e8b](https://github.com/OneGov/onegov-cloud/compare/0e6ae7daf1^...e305d77e8b)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.5)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Adds event locking for subscriptions**

Only admins should be able add subscriptions for locked course events.
Adds property `locked_for_subscriptions` to `CourseEvent` and adapts form.
Introduces checks for reservation adding/editing in views.

**`Feature`** | **[FSI-6](https://kanton-zug.atlassian.net/browse/FSI-6)** | **[303612192e](https://github.com/onegov/onegov-cloud/commit/303612192ef9108a9e4e21ef5548904e702a8442)**

🐞 **Fixes editor subscription capabilities**

- Editor can place reservations for attendees from his departement (in permissions)
- Fixes links and Dropdown-Choices for editors
- Fixes Editor Message he cant see all the records

**`Bugfix`** | **[FSI-7](https://kanton-zug.atlassian.net/browse/FSI-7)** | **[0e6ae7daf1](https://github.com/onegov/onegov-cloud/commit/0e6ae7daf1a0bd93bd6c08b35f5fa3e749ce0f19)**

## Release `2020.4`

> released: **2020-01-15 16:29**<br>
> commits: **10 / [775357c4e7...16cf983b8d](https://github.com/OneGov/onegov-cloud/compare/775357c4e7^...16cf983b8d)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.4)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds organiser info to export**

**`Feature`** | **[FER-840](https://issues.seantis.ch/browse/FER-840)** | **[984467b933](https://github.com/onegov/onegov-cloud/commit/984467b933a3e5809cc18675d4697ef8e90ed98c)**

🐞 **Fixes some issues with booking after finalization**

**`Bugfix`** | **[FER-194](https://issues.seantis.ch/browse/FER-194)** | **[4e3898085c](https://github.com/onegov/onegov-cloud/commit/4e3898085ce5f94f79b0085f9708db4996b24738)**

🐞 **Fixes past periods shown**

The past periods on activities were shown to people that have no
interest in them. This fixes this issue.

**`Bugfix`** | **[FER-839](https://issues.seantis.ch/browse/FER-839)** | **[1edb5d87a6](https://github.com/onegov/onegov-cloud/commit/1edb5d87a640c181c1bc13bf7f00a11c19156ca4)**

🐞 **Fixes administrative costs display**

The administrative costs cannot be manipulated in all_inclusive periods.

**`Bugfix`** | **[FER-839](https://issues.seantis.ch/browse/FER-839)** | **[e7f80220cd](https://github.com/onegov/onegov-cloud/commit/e7f80220cd0278af0b5a26e53bced07c04c826cd)**

### Fsi

🎉 **Integrates search**

**`Feature`** | **[e591a29189](https://github.com/onegov/onegov-cloud/commit/e591a291892a92c252f173d9e8f10a5c1885ecf0)**

## Release `2020.3`

> released: **2020-01-15 09:36**<br>
> commits: **3 / [24b4600f0f...1f801129cd](https://github.com/OneGov/onegov-cloud/compare/24b4600f0f^...1f801129cd)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.3)](https://buildkite.com/seantis/onegov-cloud)

## Release `2020.2`

> released: **2020-01-15 09:10**<br>
> commits: **4 / [daf22a65f5...e5f6c436b8](https://github.com/OneGov/onegov-cloud/compare/daf22a65f5^...e5f6c436b8)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.2)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Adds pagination to reservation collection**

**`Feature`** | **[FSI-4](https://kanton-zug.atlassian.net/browse/FSI-4)** | **[daf22a65f5](https://github.com/onegov/onegov-cloud/commit/daf22a65f52329258ba9965f028df1321437be8e)**

🎉 **Adds IMS Import scripts**

Adds tested import script with cli integration for one-time import of old data base export. The documentation is withing the script.

**`Feature`** | **[FSI-3](https://kanton-zug.atlassian.net/browse/FSI-3)** | **[8870da91d8](https://github.com/onegov/onegov-cloud/commit/8870da91d85d63ae8e1a1e5d269dc119b8caf7f4)**

✨ **General application improvements**

- Fixes redicret to course collection after subscription
- Fixes choices translation on None
- Introduces separate form for placeholder subscription
- Hides email and shortcode if viewing own subscriptions
- Ensure editors and admin can add subscriptions
- Fixes editor can see his own subscriptions when seeing all
- other minor issues

**`Other`** | **[083ad03648](https://github.com/onegov/onegov-cloud/commit/083ad03648fbaa7c58657d59a3a77f7ca1a1c41a)**

## Release `2020.1`

> released: **2020-01-14 13:18**<br>
> commits: **10 / [28e219a921...af6edff0c7](https://github.com/OneGov/onegov-cloud/compare/28e219a921^...af6edff0c7)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2020.1)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

✨ **Updates tracking URLs**

**`Other`** | **[FER-838](https://issues.seantis.ch/browse/FER-838)** | **[a6732ad567](https://github.com/onegov/onegov-cloud/commit/a6732ad5674290e1bbde665503f441303f539516)**

### Fsi

🎉 **Improves login workflow**

**`Feature`** | **[FSI-1](https://kanton-zug.atlassian.net/browse/FSI-1)** | **[824b155b16](https://github.com/onegov/onegov-cloud/commit/824b155b169558f5d8c04259a5676d7b5344eaea)**

### Winterthur

🐞 **Fixes stale mission reports default year**

The deault year of mission reports would stay at the old year, when the
processe stayed alive over the new year. This was due to the current
year being set at the process startup.

**`Bugfix`** | **[FW-74](https://stadt-winterthur.atlassian.net/browse/FW-74)** | **[11affee714](https://github.com/onegov/onegov-cloud/commit/11affee714c61491322b9980af44b34edbc54049)**

### Wtfs

✨ **Updates confirmation e-mail wording**

**`Other`** | **[SA-52](https://stadt-winterthur.atlassian.net/browse/SA-52)** | **[c789eb70b0](https://github.com/onegov/onegov-cloud/commit/c789eb70b0365b65b43839d9a1cac3b9f543e001)**

## Release `2019.59`

> released: **2019-12-28 10:29**<br>
> commits: **5 / [8ca49480cf...c73c896e9f](https://github.com/OneGov/onegov-cloud/compare/8ca49480cf^...c73c896e9f)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.59)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds an unlucky attendees report**

The report contains all attendees that have a booking in the given
period, but no accepted one.

**`Feature`** | **[FER-763](https://issues.seantis.ch/browse/FER-763)** | **[63f593025d](https://github.com/onegov/onegov-cloud/commit/63f593025dad9a1ddabd15668c5c32e387584a1f)**

🐞 **Limit notifications for bookings**

Before, notifications would be sent to all individuals with bookings,
now only accepted bookings are considered.

**`Bugfix`** | **[FER-784](https://issues.seantis.ch/browse/FER-784)** | **[8ca49480cf](https://github.com/onegov/onegov-cloud/commit/8ca49480cf2759916f5b550c5ba73bfc74c3fc25)**

🐞 **Fixes some bills not showing up**

Only the current period's bill would show up in the my-bills view.

**`Bugfix`** | **[FER-835](https://issues.seantis.ch/browse/FER-835)** | **[54c7fc95eb](https://github.com/onegov/onegov-cloud/commit/54c7fc95eb42416cc5eeb5dca1fc2a0556771eab)**

### Org

✨ **Increases size of auth provider banners**

**`Other`** | **[a31556313b](https://github.com/onegov/onegov-cloud/commit/a31556313bcce58ef973f02bb1490782c007855a)**

## Release `2019.58`

> released: **2019-12-23 11:45**<br>
> commits: **3 / [f9c476f850...1ec81076c4](https://github.com/OneGov/onegov-cloud/compare/f9c476f850^...1ec81076c4)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.58)](https://buildkite.com/seantis/onegov-cloud)

## Release `2019.57`

> released: **2019-12-20 15:58**<br>
> commits: **2 / [692adda0c0...f18ebe02e4](https://github.com/OneGov/onegov-cloud/compare/692adda0c0^...f18ebe02e4)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.57)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds a way for volunteers to sign up**

Volunteers may now look at the needs of activites and select which needs
they would like to fulfill. The admin has the ability to check the
volunteer submissions and manage their statuses.

**`Feature`** | **[FER-739](https://issues.seantis.ch/browse/FER-739)** | **[692adda0c0](https://github.com/onegov/onegov-cloud/commit/692adda0c0a0ad5eac566c41b047e749e8d2ad55)**

## Release `2019.56`

> released: **2019-12-20 09:30**<br>
> commits: **3 / [92a10e053f...12b5595ce3](https://github.com/OneGov/onegov-cloud/compare/92a10e053f^...12b5595ce3)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.56)](https://buildkite.com/seantis/onegov-cloud)

## Release `2019.55`

> released: **2019-12-19 15:11**<br>
> commits: **2 / [c43a598fa2...b80fe144ff](https://github.com/OneGov/onegov-cloud/compare/c43a598fa2^...b80fe144ff)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.55)](https://buildkite.com/seantis/onegov-cloud)

### Fsi

🎉 **Adds teacher user import**

**`Feature`** | **[c43a598fa2](https://github.com/onegov/onegov-cloud/commit/c43a598fa25ed26644d898cdcb39984db3c8348a)**

## Release `2019.54`

> released: **2019-12-19 12:31**<br>
> commits: **9 / [89e5bbdbfa...95da9e95b5](https://github.com/OneGov/onegov-cloud/compare/89e5bbdbfa^...95da9e95b5)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.54)](https://buildkite.com/seantis/onegov-cloud)

### Swissvotes

🎉 **Adds Matomo tracking for swissvotes.ch**

**`Feature`** | **[89e5bbdbfa](https://github.com/onegov/onegov-cloud/commit/89e5bbdbfa58634b8f4f525c2bc71ab97ae1ea43)**

## Release `2019.53`

> released: **2019-12-17 13:57**<br>
> commits: **3 / [14d3d9de02...c62c828a51](https://github.com/OneGov/onegov-cloud/compare/14d3d9de02^...c62c828a51)**  
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
> commits: **2 / [c5f8710c60...c66dbd3a70](https://github.com/OneGov/onegov-cloud/compare/c5f8710c60^...c66dbd3a70)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.52)](https://buildkite.com/seantis/onegov-cloud)

### Swisvotes

🎉 **Adds static urls for vote details page**

**`Feature`** | **[c5f8710c60](https://github.com/onegov/onegov-cloud/commit/c5f8710c60a004f0c8a5a9170eb3b674116badb5)**

## Release `2019.51`

> released: **2019-12-15 23:06**<br>
> commits: **4 / [497c3d9581...286b2d3137](https://github.com/OneGov/onegov-cloud/compare/497c3d9581^...286b2d3137)**  
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
> commits: **9 / [c50857d184...2c694b27a9](https://github.com/OneGov/onegov-cloud/compare/c50857d184^...2c694b27a9)**  
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
> commits: **8 / [837d01d82e...f470ca3a09](https://github.com/OneGov/onegov-cloud/compare/837d01d82e^...f470ca3a09)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.49)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Adds the ability to book after finalization**

This allows normal users to create bookings after the bill has been
published. Before, this was reserved for administrators.

**`Feature`** | **[FER-194](https://issues.seantis.ch/browse/FER-194)** | **[9d4f242107](https://github.com/onegov/onegov-cloud/commit/9d4f24210762cba487c932b493026a0b5502de00)**

## Release `2019.48`

> released: **2019-12-11 14:10**<br>
> commits: **15 / [ead36cf8ec...11a07e9dcc](https://github.com/OneGov/onegov-cloud/compare/ead36cf8ec^...11a07e9dcc)**  
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
> commits: **2 / [fa96aac112...2ae5915c63](https://github.com/OneGov/onegov-cloud/compare/fa96aac112^...2ae5915c63)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.47)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Redesigns group code bookings**

The new UI solves a number of issues with the old approach,
streamlining common use-cases and offering more clarity.

**`Feature`** | **[FER-789](https://issues.seantis.ch/browse/FER-789)** | **[fa96aac112](https://github.com/onegov/onegov-cloud/commit/fa96aac11205c3ac29c00f333f0a7f0e54d6fedb)**

## Release `2019.46`

> released: **2019-12-04 11:52**<br>
> commits: **4 / [96e14a3688...4fa9647ea2](https://github.com/OneGov/onegov-cloud/compare/96e14a3688^...4fa9647ea2)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.46)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Fixes reservations not being shown after selecting them**

This is a regression introduced with the recent view settings change.
The accompanying javascript would generate invalid URLs.

**`Bugfix`** | **[96e14a3688](https://github.com/onegov/onegov-cloud/commit/96e14a36884617ca33ee1b90074cef9df9690d50)**

## Release `2019.45`

> released: **2019-12-03 18:13**<br>
> commits: **9 / [87138a72a5...4fd31b78b4](https://github.com/OneGov/onegov-cloud/compare/87138a72a5^...4fd31b78b4)**  
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
> commits: **3 / [d1e2208edb...d6c938c5f6](https://github.com/OneGov/onegov-cloud/compare/d1e2208edb^...d6c938c5f6)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.44)](https://buildkite.com/seantis/onegov-cloud)

### Agency

🎉 **Improves pdf rendering**

- hold titles together
- makes spacing after portrait consistent

**`Feature`** | **[3a37b55ec5](https://github.com/onegov/onegov-cloud/commit/3a37b55ec5edf88cfd7802c833f30ca68f36f6cc)**

## Release `2019.43`

> released: **2019-11-28 14:27**<br>
> commits: **3 / [9acc0a1abe...55b6c0d996](https://github.com/OneGov/onegov-cloud/compare/9acc0a1abe^...55b6c0d996)**  
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
> commits: **4 / [f4fbdf6818...616849323b](https://github.com/OneGov/onegov-cloud/compare/f4fbdf6818^...616849323b)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.42)](https://buildkite.com/seantis/onegov-cloud)

### User

✨ **Integrates on_login support**

This extends the on_login callback to all user handling applications and
brings it under the onegov.user umbrella, fixing a few bugs.

**`Other`** | **[10f6c5f33d](https://github.com/onegov/onegov-cloud/commit/10f6c5f33df348c578eab1d9aea0ab6ec5951265)**

## Release `2019.41`

> released: **2019-11-26 10:41**<br>
> commits: **2 / [1c5bad57b7...7b78ee1ad1](https://github.com/OneGov/onegov-cloud/compare/1c5bad57b7^...7b78ee1ad1)**  
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
> commits: **9 / [df42fa39b6...ba91f9cc07](https://github.com/OneGov/onegov-cloud/compare/df42fa39b6^...ba91f9cc07)**  
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
> commits: **256 / [4fa47c7b87...1986fcfd5b](https://github.com/OneGov/onegov-cloud/compare/4fa47c7b87^...1986fcfd5b)**  
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
> commits: **6 / [0658a7862b...176281bfe3](https://github.com/OneGov/onegov-cloud/compare/0658a7862b^...176281bfe3)**  
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
> commits: **3 / [847ec8204a...0e6469b6a6](https://github.com/OneGov/onegov-cloud/compare/847ec8204a^...0e6469b6a6)**  
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
> commits: **3 / [fc630b8095...18553040e2](https://github.com/OneGov/onegov-cloud/compare/fc630b8095^...18553040e2)**  
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
> commits: **4 / [889623375e...80349d6d9d](https://github.com/OneGov/onegov-cloud/compare/889623375e^...80349d6d9d)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.35)](https://buildkite.com/seantis/onegov-cloud)

### Core

✨ **Upgrade to Python 3.8**

OneGov Cloud now uses Python 3.8 instead of 3.7.

**`Other`** | **[195ccc2f23](https://github.com/onegov/onegov-cloud/commit/195ccc2f23ac0d9b8d2968dcf464bf75732ce496)**

## Release `2019.34`

> released: **2019-10-30 15:59**<br>
> commits: **2 / [123b198a00...32e0377e18](https://github.com/OneGov/onegov-cloud/compare/123b198a00^...32e0377e18)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.34)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Fixes news widget failing on certain sites.**

**`Bugfix`** | **[123b198a00](https://github.com/onegov/onegov-cloud/commit/123b198a00533299575e019f37429893a6b3f058)**

## Release `2019.33`

> released: **2019-10-30 09:56**<br>
> commits: **6 / [0dc5b8fc9f...ac06bc140a](https://github.com/OneGov/onegov-cloud/compare/0dc5b8fc9f^...ac06bc140a)**  
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
> commits: **5 / [5687e1683f...2ded9d9fd7](https://github.com/OneGov/onegov-cloud/compare/5687e1683f^...2ded9d9fd7)**  
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
> commits: **4 / [c898172a68...5949739a67](https://github.com/OneGov/onegov-cloud/compare/c898172a68^...5949739a67)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.31)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Improves SMS sending performance**

The main change is that we switch from requests to pycurl, which offers
much better performance.

**`Feature`** | **[c898172a68](https://github.com/onegov/onegov-cloud/commit/c898172a68938b12dea41f86b024cbc5f2d04d26)**

## Release `2019.30`

> released: **2019-10-23 10:39**<br>
> commits: **2 / [816a404e04...117b19eb79](https://github.com/OneGov/onegov-cloud/compare/816a404e04^...117b19eb79)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.30)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Adds support of yml configuration to hide certain graphics or views**

Adapts code to use configuration value to hide certain graphs and percentages according to the tenant's needs. This was implemented for views where a `skip_rendering` was introduced beforehand. Also adds a small fix for a sql window function expression.

**`Feature`** | **[816a404e04](https://github.com/onegov/onegov-cloud/commit/816a404e0498bc810863c22a116b109969944b4d)**

## Release `2019.29`

> released: **2019-10-23 10:16**<br>
> commits: **15 / [d19e1fa2c6...714bb1a7da](https://github.com/OneGov/onegov-cloud/compare/d19e1fa2c6^...714bb1a7da)**  
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
> commits: **3 / [af4ff8e167...67cc464e10](https://github.com/OneGov/onegov-cloud/compare/af4ff8e167^...67cc464e10)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.28)](https://buildkite.com/seantis/onegov-cloud)

### Core

🐞 **Fixes arrow week granularity translations for itialian and rumantsch**

**`Bugfix`** | **[f1da1d1f47](https://github.com/onegov/onegov-cloud/commit/f1da1d1f47ebb570529f423cdd255f54e8530538)**

## Release `2019.27`

> released: **2019-10-14 14:20**<br>
> commits: **3 / [cf141436da...2f96cfc593](https://github.com/OneGov/onegov-cloud/compare/cf141436da^...2f96cfc593)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.27)](https://buildkite.com/seantis/onegov-cloud)

### Feriennet

🎉 **Allows for booking and execution phases to overlap**

This also gets rid of the deadline date, which is now the booking
phase's end date.

**`Feature`** | **[FER-783](https://issues.seantis.ch/browse/FER-783)** | **[c7a310ef3a](https://github.com/onegov/onegov-cloud/commit/c7a310ef3a3404e2d358e6ec19c6f7c5e27dee08)**

## Release `2019.26`

> released: **2019-10-11 10:21**<br>
> commits: **5 / [54237533cc...7c8f1750e7](https://github.com/OneGov/onegov-cloud/compare/54237533cc^...7c8f1750e7)**  
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
> commits: **5 / [bfa6f6b0ff...453ac1ade7](https://github.com/OneGov/onegov-cloud/compare/bfa6f6b0ff^...453ac1ade7)**  
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
> commits: **2 / [33a3fe7881...cac0b1a82c](https://github.com/OneGov/onegov-cloud/compare/33a3fe7881^...cac0b1a82c)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.24)](https://buildkite.com/seantis/onegov-cloud)

### Org

🐞 **Fixes database upgrade failing on Postgres < 10**

The upgrade used a feature not available on 9.6.'

**`Bugfix`** | **[33a3fe7881](https://github.com/onegov/onegov-cloud/commit/33a3fe7881774c11129eeb93c7e264668b0feac4)**

## Release `2019.23`

> released: **2019-10-09 13:11**<br>
> commits: **6 / [7cdac038a6...3059a207ee](https://github.com/OneGov/onegov-cloud/compare/7cdac038a6^...3059a207ee)**  
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
> commits: **10 / [8636d6d3f5...3925017707](https://github.com/OneGov/onegov-cloud/compare/8636d6d3f5^...3925017707)**  
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
> commits: **14 / [729c079a33...d7e90e52ba](https://github.com/OneGov/onegov-cloud/compare/729c079a33^...d7e90e52ba)**  
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
> commits: **3 / [350f56de4b...8862d19fee](https://github.com/OneGov/onegov-cloud/compare/350f56de4b^...8862d19fee)**  
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
> commits: **5 / [75f6dd1a4c...bbe6bb9f78](https://github.com/OneGov/onegov-cloud/compare/75f6dd1a4c^...bbe6bb9f78)**  
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
> commits: **4 / [0b45b544e6...18a54e46fe](https://github.com/OneGov/onegov-cloud/compare/0b45b544e6^...18a54e46fe)**  
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
> commits: **11 / [d37cb83d40...c1168ff4c9](https://github.com/OneGov/onegov-cloud/compare/d37cb83d40^...c1168ff4c9)**  
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
> commits: **2 / [9ab37eddeb...a78362e65e](https://github.com/OneGov/onegov-cloud/compare/9ab37eddeb^...a78362e65e)**  
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
> commits: **3 / [7ee8f0b3ed...4b3c372d2e](https://github.com/OneGov/onegov-cloud/compare/7ee8f0b3ed^...4b3c372d2e)**  
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
> commits: **7 / [8bf89eafbb...12cd043598](https://github.com/OneGov/onegov-cloud/compare/8bf89eafbb^...12cd043598)**  
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
> commits: **6 / [226c3dd0ff...3646bae845](https://github.com/OneGov/onegov-cloud/compare/226c3dd0ff^...3646bae845)**  
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
> commits: **3 / [cc133b91bc...770c2a73dc](https://github.com/OneGov/onegov-cloud/compare/cc133b91bc^...770c2a73dc)**  
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
> commits: **5 / [b4ca9c0722...ef7ec74cd8](https://github.com/OneGov/onegov-cloud/compare/b4ca9c0722^...ef7ec74cd8)**  
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
> commits: **2 / [ac565ca225...ba85af9184](https://github.com/OneGov/onegov-cloud/compare/ac565ca225^...ba85af9184)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.10)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🎉 **Adds api endpoint with aggregated information for national council elections**

The endpoint is available under the url `/election/eample/data-aggregated-lists`.

**`Feature`** | **[ac565ca225](https://github.com/onegov/onegov-cloud/commit/ac565ca22590faf46e01f8325bd5f52833ff7a97)**

## Release `2019.9`

> released: **2019-09-06 15:09**<br>
> commits: **4 / [3e406aeb3c...3c9b101357](https://github.com/OneGov/onegov-cloud/compare/3e406aeb3c^...3c9b101357)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.9)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Adds app-specific role maps for LDAP**

Without this change all applications whould share the same role map,
which is too limiting for the general OneGov Cloud use.

**`Feature`** | **[3e406aeb3c](https://github.com/onegov/onegov-cloud/commit/3e406aeb3c59e258e309f260cc525d77cb508dcd)**

## Release `2019.8`

> released: **2019-09-06 12:43**<br>
> commits: **2 / [a728bf78f8...75d00e69fc](https://github.com/OneGov/onegov-cloud/compare/a728bf78f8^...75d00e69fc)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.8)](https://buildkite.com/seantis/onegov-cloud)

### Auth

🎉 **Integrates Kerberos/LDAP**

A new authentication provider provides LDAP authentication together with Kerberos. The request is authenticated by Kerberos (providing a username), the user authorised by LDAP.

**`Feature`** | **[a728bf78f8](https://github.com/onegov/onegov-cloud/commit/a728bf78f8a2025e3b63ff4db3fe2b7342ceed91)**

## Release `2019.7`

> released: **2019-09-05 17:40**<br>
> commits: **8 / [64c5f5bdfb...f48727bc88](https://github.com/OneGov/onegov-cloud/compare/64c5f5bdfb^...f48727bc88)**  
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
> commits: **2 / [0d57b12204...3d53d3b4b9](https://github.com/OneGov/onegov-cloud/compare/0d57b12204^...3d53d3b4b9)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.6)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

✨ **Hide intermediate results for elections and votes**

Hides clear statuses such as elected or number of mandates per list for proporz election if election is not final.

**`Other`** | **[0d57b12204](https://github.com/onegov/onegov-cloud/commit/0d57b122040a9e883735a56d40d891430bae3c10)**

## Release `2019.5`

> released: **2019-09-04 06:04**<br>
> commits: **14 / [326bab40a2...a8937ba123](https://github.com/OneGov/onegov-cloud/compare/326bab40a2^...a8937ba123)**  
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
> commits: **11 / [5c3adde749...282ed75f8e](https://github.com/OneGov/onegov-cloud/compare/5c3adde749^...282ed75f8e)**  
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
> commits: **5 / [36ebdbfa71...4633aeb348](https://github.com/OneGov/onegov-cloud/compare/36ebdbfa71^...4633aeb348)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.3)](https://buildkite.com/seantis/onegov-cloud)

### Core

🎉 **Adds `onegov.core.__version__`**

This version identifier always contains the current version of the
container. During development this information may be stale, as the
version is only updated during the release process.

**`Feature`** | **[b2f4f16f61](https://github.com/onegov/onegov-cloud/commit/b2f4f16f614ad690b8eb5c222b1881a677d1e323)**

## Release `2019.2`

> released: **2019-08-28 10:04**<br>
> commits: **6 / [69399e0e7a...50afe830eb](https://github.com/OneGov/onegov-cloud/compare/69399e0e7a^...50afe830eb)**  
> [![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg?branch=release-2019.2)](https://buildkite.com/seantis/onegov-cloud)

### Election-Day

🐞 **Fixes bug in validate_integer(line, 'stimmen') in wmkandidaten_gde**

**`Bugfix`** | **[75dcf68244](https://github.com/onegov/onegov-cloud/commit/75dcf68244b1cc836fee5a5f27303536819a5720)**

## Release `2019.1`

> released: **2019-08-27 14:22**<br>
> commits: **19 / [53849be4fe...cc3764630e](https://github.com/OneGov/onegov-cloud/compare/53849be4fe^...cc3764630e)**  
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

