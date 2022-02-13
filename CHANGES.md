# Changes

## 2022.13

`2022-02-13` | [b6ae0228ad...c3b82dda74](https://github.com/OneGov/onegov-cloud/compare/b6ae0228ad^...c3b82dda74)

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

## 2021.92

`2021-11-28` | [a1f9257561...67e7a90ec8](https://github.com/OneGov/onegov-cloud/compare/a1f9257561^...67e7a90ec8)

### Fsi

##### Filters course attendedees for editors when adding subscriptions for existing courses too.

`Bugfix` | [OGC-125](https://linear.app/onegovcloud/issue/OGC-125) | [cc228b7ca6](https://github.com/onegov/onegov-cloud/commit/cc228b7ca6b8bdcbdc4b5b3131978a70812f856f)

### Org

##### Allow to filter local users.

`Feature` | [2af8f8bad3](https://github.com/onegov/onegov-cloud/commit/2af8f8bad3e349b46f1fe921f8096eb90b50d0a9)

### Swissvotes

##### Fix upgrade step being executed on every upgrade.

`Bugifx` | [5d3ec47dbf](https://github.com/onegov/onegov-cloud/commit/5d3ec47dbf7db7070c3ca525be703f192d143fc0)

##### Update metadata file format.

`Other` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [e33cfa95cf](https://github.com/onegov/onegov-cloud/commit/e33cfa95cf100db19d65cdabe3b7e0fa24c80be1)

##### Update display format of brief description title.

`Other` | [SWI-17](https://linear.app/swissvotes/issue/SWI-17) | [621927d18a](https://github.com/onegov/onegov-cloud/commit/621927d18a500d316094994b23411addc2fc0704)

## 2021.91

`2021-11-18` | [cfd18ef3a0...b346914d99](https://github.com/OneGov/onegov-cloud/compare/cfd18ef3a0^...b346914d99)

### Org

##### Fix typo

`Other` | [OGC-126](https://linear.app/onegovcloud/issue/OGC-126) | [a5f96aa73b](https://github.com/onegov/onegov-cloud/commit/a5f96aa73b2c1cb6830c159b54dfc781b75fef0a)

### Swissvotes

##### Add additional campaign material.

`Feature` | [SWI-15](https://linear.app/swissvotes/issue/SWI-15) | [e64ae929a8](https://github.com/onegov/onegov-cloud/commit/e64ae929a80fbcead446273a2443b04b9ab75f75)

### Town6

##### Improve footer logo spacing.

`Other` | [OGC-124](https://linear.app/onegovcloud/issue/OGC-124) | [34e115b8ed](https://github.com/onegov/onegov-cloud/commit/34e115b8ed4ab11a0a30c4c285503ecd43c18c6f)

## 2021.90

`2021-11-16` | [f9d62e2108...0960f2c7a5](https://github.com/OneGov/onegov-cloud/compare/f9d62e2108^...0960f2c7a5)

### Core

##### Add generic CLI command for deleting an instance.

`Feature` | [SEA-524](https://linear.app/seantis/issue/SEA-524) | [f9d62e2108](https://github.com/onegov/onegov-cloud/commit/f9d62e2108855e2889b346a1f953304558d1532b)

##### Adds compatibility with latest fs version.

`Bugfix` | [SEA-524](https://linear.app/seantis/issue/SEA-524) | [59848b31d0](https://github.com/onegov/onegov-cloud/commit/59848b31d0a9501eff56e72ceb6d7e16f7607425)

### Feriennet

##### Update Italian Translations.

`Other` | [PRO-970](https://linear.app/projuventute/issue/PRO-970) | [1a96ac56d2](https://github.com/onegov/onegov-cloud/commit/1a96ac56d27038b5f82c4d9da5bc04e443330349)

##### Update Italian translations.

`Other` | [PRO-970](https://linear.app/projuventute/issue/PRO-970) | [afc4d45e2a](https://github.com/onegov/onegov-cloud/commit/afc4d45e2acc4c374e4e0f08567a6d72131e26ca)

### Swissvotes

##### Use separate encoding for tie-breakers.

`Feature` | [SWI-25](https://linear.app/swissvotes/issue/SWI-25) | [ac53ef0b3d](https://github.com/onegov/onegov-cloud/commit/ac53ef0b3d65a7ce1971968df83122a34bdfa197)

##### Adjust brief description link.

`Other` | [SWI-17](https://linear.app/swissvotes/issue/SWI-17) | [8e53278631](https://github.com/onegov/onegov-cloud/commit/8e5327863182748bb85ddb0750ed5fd7b79738b5)

## 2021.89

`2021-11-11` | [927e7222f1...b4ee607625](https://github.com/OneGov/onegov-cloud/compare/927e7222f1^...b4ee607625)

### Feriennet

##### Fix translation.

`Bugfix` | [PRO-945](https://linear.app/projuventute/issue/PRO-945) | [09c8777fbe](https://github.com/onegov/onegov-cloud/commit/09c8777fbe1f86a63c200ef75bae695e8d584fc1)

##### Fix Italian translations.

`Bugfix` | [PRO-970](https://linear.app/projuventute/issue/PRO-970) | [4591feb5e3](https://github.com/onegov/onegov-cloud/commit/4591feb5e3de3db567199f4991bdef587ed5ba1c)

### Ferriennet

##### Add translations for QR bills.

`Other` | [PRO-667](https://linear.app/projuventute/issue/PRO-667) | [ea9f02fccf](https://github.com/onegov/onegov-cloud/commit/ea9f02fccf4026d386daad32ab3bcbb1d6de1182)

### Org

##### Fix typo.

`Bugfix` | [OGC-126](https://linear.app/onegovcloud/issue/OGC-126) | [98b76b76bf](https://github.com/onegov/onegov-cloud/commit/98b76b76bf2328cbe952e47c1171400de499f7e4)

### Swissvotes

##### Add title column for brief description.

`Feature` | [SWI-17](https://linear.app/swissvotes/issue/SWI-17) | [4e9f0efd53](https://github.com/onegov/onegov-cloud/commit/4e9f0efd533f8943231783394b94c7ed95f16e7f)

##### Add additional links.

`Feature` | [0125ce4521](https://github.com/onegov/onegov-cloud/commit/0125ce4521461a44782def2c7cef723f1a830a8b)

##### Drop unused columns.

`Other` | [SWI-29](https://linear.app/swissvotes/issue/SWI-29) | [f9846c8cf0](https://github.com/onegov/onegov-cloud/commit/f9846c8cf0bfee70c6f499a0748f85697265d6a8)

### Town6

##### Remove slider controls for less than 2 images.

`Feature` | [OGC-118](https://linear.app/onegovcloud/issue/OGC-118) | [d455670454](https://github.com/onegov/onegov-cloud/commit/d45567045442bbdca53febb1756bfd78fd7f8452)

##### Add link on whole focus widget.

`Other` | [OGC-122](https://linear.app/onegovcloud/issue/OGC-122) | [896ee5bdf0](https://github.com/onegov/onegov-cloud/commit/896ee5bdf0d73e80ab4c731d0057d3321a3aab94)

## 2021.88

`2021-11-01` | [2cb5fe49f8...246345e7b7](https://github.com/OneGov/onegov-cloud/compare/2cb5fe49f8^...246345e7b7)

### Org

##### Fix event import date/time parsing.

`Bugfix` | [OGC_88](#OGC_88) | [dd73a9d6c6](https://github.com/onegov/onegov-cloud/commit/dd73a9d6c681fc73e6dd3d3b0217c2094b34d9aa)

### Swissvotes

##### Add post-vote poll dataset hint.

`Feature` | [SWI-19](https://linear.app/swissvotes/issue/SWI-19) | [2cb5fe49f8](https://github.com/onegov/onegov-cloud/commit/2cb5fe49f8f2be2e1d84c582b4c6cbf0900326aa)

##### Add blank lines between recommendations.

`Feature` | [SWI-19](https://linear.app/swissvotes/issue/SWI-19) | [04a03e5df1](https://github.com/onegov/onegov-cloud/commit/04a03e5df14c25b541933783e26be7e3eeed23ff)

## 2021.87

`2021-11-01` | [4a1d5d96e7...e9d1328651](https://github.com/OneGov/onegov-cloud/compare/4a1d5d96e7^...e9d1328651)

### Feriennet

##### Update Italian translations.

`Other` | [PRO-805](https://linear.app/projuventute/issue/PRO-805) | [4a1d5d96e7](https://github.com/onegov/onegov-cloud/commit/4a1d5d96e7bc4d4dd1b46dfeb246cd9a9fd3285f)

### Org

##### Add ticket pickup hint.

`Feature` | [OGC-103](https://linear.app/onegovcloud/issue/OGC-103) | [c0dbb1cedb](https://github.com/onegov/onegov-cloud/commit/c0dbb1cedb17848c0b44e90f5064e6f4923a8f2d)

##### Add import for events.

`Feature` | [OGC-88](https://linear.app/onegovcloud/issue/OGC-88) | [9fad3a64a1](https://github.com/onegov/onegov-cloud/commit/9fad3a64a1ced1292493e384637bd9aacd14a6e0)

### Town6

##### Improve focus widgets.

`Other` | [OGC-86](https://linear.app/onegovcloud/issue/OGC-86) | [a08eb1021c](https://github.com/onegov/onegov-cloud/commit/a08eb1021cf17a774e21163260c4ba0a30056a58)

##### Fix homepage tiles layout.

`Bugfix` | [OGC-115](https://linear.app/onegovcloud/issue/OGC-115) | [b82085deef](https://github.com/onegov/onegov-cloud/commit/b82085deefbd62ee7021063720564e39b5d09070)

## 2021.86

`2021-10-26` | [fdc1567f8b...3f171e8f67](https://github.com/OneGov/onegov-cloud/compare/fdc1567f8b^...3f171e8f67)

### Feriennet

##### Add experimental support for QR-bills.

`Feature` | [PRO-667](https://linear.app/projuventute/issue/PRO-667) | [fdc1567f8b](https://github.com/onegov/onegov-cloud/commit/fdc1567f8becdf25e65a2d3674b738b32782eea7)

## 2021.85

`2021-10-26` | [e5f5ab1c8b...7cc20c08b2](https://github.com/OneGov/onegov-cloud/compare/e5f5ab1c8b^...7cc20c08b2)

### Agency

##### Minor visual improvements.

* Add dividing line for memberships
* Make design of people in organizations prettier
* Make "..." in search suggestions clickable

`Other` | [OGC-27](https://linear.app/onegovcloud/issue/OGC-27) | [b6611d708e](https://github.com/onegov/onegov-cloud/commit/b6611d708ec14af109af1835d0ebbb1020fae1e3)

### Election Day

##### Change color of embed and SVG download links.

`Other` | [OGC-107](https://linear.app/onegovcloud/issue/OGC-107) | [bf0eb67a9e](https://github.com/onegov/onegov-cloud/commit/bf0eb67a9ed8d5617427dc8a7745d460cedfddf2)

### Feriennet

##### Update translations.

`Other` | [PRO-805](https://linear.app/projuventute/issue/PRO-805) | [1c53617f11](https://github.com/onegov/onegov-cloud/commit/1c53617f110b5a9fb0f6193bcd7314bd5f6dc70b)

### Org

##### Add Announcement Banner.

`Feature` | [OGC-106](https://linear.app/onegovcloud/issue/OGC-106) | [bcd3f7f7a1](https://github.com/onegov/onegov-cloud/commit/bcd3f7f7a1c8a3f7719bb4842eb0af09b1b7a637)

### Town6

##### Equalize size of partner images in footer.

`Other` | [SEA-471](https://linear.app/seantis/issue/SEA-471) | [acca4f5291](https://github.com/onegov/onegov-cloud/commit/acca4f52914f67d3b209010d1eec21b765fe0330)

##### Improve focus widgets.

`Other` | [OGC-86](https://linear.app/onegovcloud/issue/OGC-86) | [36019142bf](https://github.com/onegov/onegov-cloud/commit/36019142bfadf17f5ebff89988d5ed2783e5d3bc)

### Winterthur

##### Update address import URL.

`Other` | [FW-95](https://stadt-winterthur.atlassian.net/browse/FW-95) | [3044f0f510](https://github.com/onegov/onegov-cloud/commit/3044f0f510aee60ffa30975be14652e6bf5b8752)

## 2021.84

`2021-10-09` | [9f2b0880f1...a2b3a5bcbb](https://github.com/OneGov/onegov-cloud/compare/9f2b0880f1^...a2b3a5bcbb)

### Fsi

##### Update translations.

`Other` | [ZW-339](https://kanton-zug.atlassian.net/browse/ZW-339) | [217851ab6a](https://github.com/onegov/onegov-cloud/commit/217851ab6ad2f357e69700d0e6ec0aa1a217ec2e)

### Org

##### Also check the agency's portrait links with the link checker.

`Feature` | [82dbf59880](https://github.com/onegov/onegov-cloud/commit/82dbf59880c23f610f311c1ee2cc878c8f4168d6)

##### Add flag for marking files for publication.

`Feature` | [OGC-112](https://linear.app/onegovcloud/issue/OGC-112) | [280fac05e4](https://github.com/onegov/onegov-cloud/commit/280fac05e4476dc4ef4bbbc5a50fda84ff9b3afb)

### Town6

##### Adds missing styling.

`Bugfix` | [OGC-77](https://linear.app/onegovcloud/issue/OGC-77) | [bf1e6eb60b](https://github.com/onegov/onegov-cloud/commit/bf1e6eb60b0b44b35afd97bace215596750d1c5d)

##### Fix file details not visible.

`Bugfix` | [9b276379f1](https://github.com/onegov/onegov-cloud/commit/9b276379f1835fd92fcf14b7860d716e9dc73497)

## 2021.83

`2021-10-05` | [2694731697...de2d88d38e](https://github.com/OneGov/onegov-cloud/compare/2694731697^...de2d88d38e)

### Feriennet

##### Adds option to display full age callout on registration.

`Feature` | [PRO-945](https://linear.app/projuventute/issue/PRO-945) | [5e3550f46b](https://github.com/onegov/onegov-cloud/commit/5e3550f46bd4e9ce7a1d641746bbd3ff3732a676)

##### Update CS sponsor links.

`Other` | [PRO-952](https://linear.app/projuventute/issue/PRO-952) | [4033a93fbd](https://github.com/onegov/onegov-cloud/commit/4033a93fbd719624dcbfd6e55dbc766c25f2f6a7)

##### Update CS sponsor texts.

`Other` | [PRO-952](https://linear.app/projuventute/issue/PRO-952) | [6842579caf](https://github.com/onegov/onegov-cloud/commit/6842579caf3c01dfa3dece547c0845e98aecd3e2)

### Town6

##### Remove cursive tag form person function

`Other` | [OGC-100](https://linear.app/onegovcloud/issue/OGC-100) | [2694731697](https://github.com/onegov/onegov-cloud/commit/2694731697505a9db74e9060ea884a3ed6dd93df)

##### Fix drag and drop icon on navigation.

`Other` | [OGC-66](https://linear.app/onegovcloud/issue/OGC-66) | [6bbe0e49f3](https://github.com/onegov/onegov-cloud/commit/6bbe0e49f3e964d73ae49ffd3672e84098a64be8)

##### Add background to focus widget.

`Other` | [OGC-86](https://linear.app/onegovcloud/issue/OGC-86) | [2c40b88ea6](https://github.com/onegov/onegov-cloud/commit/2c40b88ea6571ee2234667474b4a8f00cdb6172c)

##### Fix event styling.

`Bugfix` | [OGC-79](https://linear.app/onegovcloud/issue/OGC-79) | [20f671c95a](https://github.com/onegov/onegov-cloud/commit/20f671c95ad7db33c44a0bed4e546d3b168b74c0)

##### Fix search icon on map.

`Bugfix` | [OGC-77](https://linear.app/onegovcloud/issue/OGC-77) | [8e3330b068](https://github.com/onegov/onegov-cloud/commit/8e3330b0684b67cd000f1fe94bd895728b6dca83)

## 2021.82

`2021-10-01` | [00040c2121...2808cfe924](https://github.com/OneGov/onegov-cloud/compare/00040c2121^...2808cfe924)

### Election Day

##### Add reply to mail address configuration option.

`Feature` | [OGC-105](https://linear.app/onegovcloud/issue/OGC-105) | [9b3b786cef](https://github.com/onegov/onegov-cloud/commit/9b3b786cefb74946e1fcb6c8a90082d6fc9e6523)

##### Add custom CSS configuration option.

`Feature` | [OGC-104](https://linear.app/onegovcloud/issue/OGC-104) | [be9c791a96](https://github.com/onegov/onegov-cloud/commit/be9c791a96f90c3c96e79820c087aa836d13b0c1)

### Feriennet

##### Adds privacy protection page.

`Feature` | [PRO-887](https://linear.app/projuventute/issue/PRO-887) | [9fa319962a](https://github.com/onegov/onegov-cloud/commit/9fa319962a46474f90146253543e583eaeb84671)

##### Changes banners.

`Other` | [PRO-952](https://linear.app/projuventute/issue/PRO-952) | [2c1c5f05ee](https://github.com/onegov/onegov-cloud/commit/2c1c5f05ee8959cfb3b4835c6a5797151452d977)

### Fsi

##### Link next subscription in audit view.

`Feature` | [ZW-332](https://kanton-zug.atlassian.net/browse/ZW-332) | [df95d7405d](https://github.com/onegov/onegov-cloud/commit/df95d7405d5a6514fb95cff6a8181e483e581f6f)

### Org

##### Add Italian.

`Feature` | [PRO-805](https://linear.app/projuventute/issue/PRO-805) | [00040c2121](https://github.com/onegov/onegov-cloud/commit/00040c212114090e548e823a81dcde75a45f913c)

## 2021.81

`2021-09-27` | [d52dfb0ec4...cd55d0249a](https://github.com/OneGov/onegov-cloud/compare/d52dfb0ec4^...cd55d0249a)

### Election Day

##### Add menu entry for updating archived results.

`Feature` | [d52dfb0ec4](https://github.com/onegov/onegov-cloud/commit/d52dfb0ec47c1dfd859cda56a1e81b5e9cf1ad1b)

##### Make pages cache expiration time configurable and add a menu entry for busting the cache.

`Feature` | [974c9b1bab](https://github.com/onegov/onegov-cloud/commit/974c9b1babdc48cabd758ed8bdba8750b7a7fa82)

##### Fix admin view permissions.

`Bugfix` | [6e96f971df](https://github.com/onegov/onegov-cloud/commit/6e96f971dfa653e4a4ad572c8a566a46877e3cfe)

##### Set a default value for CSP Connect Source.

`Bugfix` | [b5278a0cb2](https://github.com/onegov/onegov-cloud/commit/b5278a0cb2ded8f2eb1797aa1d92c137a1c0f45a)

### Form

##### Add a CSS field.

`Feature` | [288fa08778](https://github.com/onegov/onegov-cloud/commit/288fa087782056fb4afe990f2d436a2549cea1a8)

### User

##### Add change role CLI command.

`Feature` | [f5078d8d29](https://github.com/onegov/onegov-cloud/commit/f5078d8d2976c57fa6319735408b64c764dc733e)

## 2021.80

`2021-09-27` | [6886672d66...a5bbfb99ff](https://github.com/OneGov/onegov-cloud/compare/6886672d66^...a5bbfb99ff)

### Election Day

##### Add CSP Connect Source option for analytics.

`Feature` | [OGC-102](https://linear.app/onegovcloud/issue/OGC-102) | [b9f9df8a0a](https://github.com/onegov/onegov-cloud/commit/b9f9df8a0ad1d04abbf34370fa02cf6055c6932f)

##### Add CSP Script Source option for analytics.

`Feature` | [OGC-102](https://linear.app/onegovcloud/issue/OGC-102) | [deec0bc8c7](https://github.com/onegov/onegov-cloud/commit/deec0bc8c70eb1870b562e9e8b1347bc66e2d896)

### Fsi

##### Show next course subscription in the audit view.

`Feature` | [ZW-332](https://kanton-zug.atlassian.net/browse/ZW-332) | [e9b8eac575](https://github.com/onegov/onegov-cloud/commit/e9b8eac5751d68f4daa0a86bbb50b8b127e6e277)

### Org

##### Removes corona banner from event directory.

`Other` | [ZW-333](https://kanton-zug.atlassian.net/browse/ZW-333) | [f373b76021](https://github.com/onegov/onegov-cloud/commit/f373b76021cb33890d4d843f3681037c505db4d2)

### Town6

##### Allow custom icons for custom service panel links.

`Feature` | [OGC-99](https://linear.app/onegovcloud/issue/OGC-99) | [a39af439fa](https://github.com/onegov/onegov-cloud/commit/a39af439fae03502096de17577b9f8ccfbaa6d66)

##### Change color of news background and date.

`Other` | [OGC-78](https://linear.app/onegovcloud/issue/OGC-78) | [6886672d66](https://github.com/onegov/onegov-cloud/commit/6886672d66a5bf2cf44a2fbf62d60cfb2e349328)

## 2021.79

`2021-09-20` | [e866168c6f...3da2c725ff](https://github.com/OneGov/onegov-cloud/compare/e866168c6f^...3da2c725ff)

### Swissvotes

##### Group policy areas if possible.

`Feature` | [SWI-23](https://linear.app/swissvotes/issue/SWI-23) | [e866168c6f](https://github.com/onegov/onegov-cloud/commit/e866168c6fa0683fc8e0461f7a22b5589338529b)

## 2021.78

`2021-09-16` | [203549ce6f...42f73969e2](https://github.com/OneGov/onegov-cloud/compare/203549ce6f^...42f73969e2)

### Election Day

##### Uses the title of the elections in election compound as default.

`Bugfix` | [6311267e8e](https://github.com/onegov/onegov-cloud/commit/6311267e8e13739a4c63227e24c83ea0b476fd70)

##### Adjust header sizes.

`Other` | [OGC-35](https://linear.app/onegovcloud/issue/OGC-35) | [580100ef0c](https://github.com/onegov/onegov-cloud/commit/580100ef0cd054314f3123b455a7788aa6a033c9)

### Org

##### Fix ticket status view for archived tickets.

`Bugfix` | [d8d41b8e21](https://github.com/onegov/onegov-cloud/commit/d8d41b8e21172b2943cd4556875a031d39e69a5e)

### Pdf

##### Embed fonts.

`Other` | [OGC-81](https://linear.app/onegovcloud/issue/OGC-81) | [2ffa823bdd](https://github.com/onegov/onegov-cloud/commit/2ffa823bdd54fab2d4d2401fd06e17d4964f0b83)

### Swissvotes

##### Order first by selected column, then by BFS number.

`Feature` | [SWI-24](https://linear.app/swissvotes/issue/SWI-24) | [5e4b26da61](https://github.com/onegov/onegov-cloud/commit/5e4b26da61b89c74ed815894eedc0182593a489f)

##### Order policies area by number.

`Feature` | [SWI-23](https://linear.app/swissvotes/issue/SWI-23) | [b3df3df8d6](https://github.com/onegov/onegov-cloud/commit/b3df3df8d6d784e7d0cfaa027c84eca14ef7f1ea)

##### Show turnout in votes view by default.

`Feature` | [SWI-20](https://linear.app/swissvotes/issue/SWI-20) | [9778167650](https://github.com/onegov/onegov-cloud/commit/97781676501c5b332138c29aad99f95d66844a1d)

##### Change order of search filters.

`Feature` | [SWI-21](https://linear.app/swissvotes/issue/SWI-21) | [fd619826c8](https://github.com/onegov/onegov-cloud/commit/fd619826c89d5015830a9a66144722e43b58fc20)

##### Improve hyphenation.

`Other` | [SWI-20](https://linear.app/swissvotes/issue/SWI-20) | [766d08635f](https://github.com/onegov/onegov-cloud/commit/766d08635f4615215b74820a16f1548d2a113d22)

##### Order policy areas by descriptor number.

`Bugfix` | [SWI-23](https://linear.app/swissvotes/issue/SWI-23) | [657e96ee47](https://github.com/onegov/onegov-cloud/commit/657e96ee47f039b41e3636639285790a83a8975b)

## 2021.77

`2021-09-03` | [7cd8cedb85...7ffb765b1c](https://github.com/OneGov/onegov-cloud/compare/7cd8cedb85^...7ffb765b1c)

### Agency

##### Enable vCard export of people.

`Feature` | [ZW-328](https://kanton-zug.atlassian.net/browse/ZW-328) | [ec335a2d4d](https://github.com/onegov/onegov-cloud/commit/ec335a2d4d392bddff1a05e6e20386a03aa4d21f)

### Election Day

##### Fix static data of canton SZ for 2020.

This requires to re-upload results from 2020.

`Bugfix` | [OGC-41](https://linear.app/onegovcloud/issue/OGC-41) | [223001a3a8](https://github.com/onegov/onegov-cloud/commit/223001a3a82cd9873cc4fee68953dcfcd95d347d)

##### Fix archive search pagination.

`Bugfix` | [OGC-43](https://linear.app/onegovcloud/issue/OGC-43) | [893be82f16](https://github.com/onegov/onegov-cloud/commit/893be82f1622fd4fff1c88a50f81b3d2f0896a03)

### Org

##### Linkify directory leads.

`Feature` | [ZW-326](https://kanton-zug.atlassian.net/browse/ZW-326) | [0e8affad78](https://github.com/onegov/onegov-cloud/commit/0e8affad78831d6fc855de1f128fc365dbbb6be0)

##### Fixes creating a PDF of a reservation ticket throwing an error if the resource has been deleted.

`Bugfix` | [7cd8cedb85](https://github.com/onegov/onegov-cloud/commit/7cd8cedb8520020658e41613c90624b312bc12d0)

##### Fixes styling of sidepanel titles with links.

`Bugfix` | [FW-93](https://stadt-winterthur.atlassian.net/browse/FW-93) | [4b8c005c15](https://github.com/onegov/onegov-cloud/commit/4b8c005c15967cb638fcb458d104f38639464c1f)

### People

##### Fix vCard export of organizations.

`Bugfix` | [678963bf06](https://github.com/onegov/onegov-cloud/commit/678963bf06106e43a20994278520a8457e6bd4c5)

### Swissvotes

##### Adds favicon.

`Feature` | [SWI-22](https://linear.app/swissvotes/issue/SWI-22) | [5632c37fd4](https://github.com/onegov/onegov-cloud/commit/5632c37fd4bb4a773fe10427405724857aa65b3e)

## 2021.76

`2021-08-31` | [ba603604f7...a87288c7de](https://github.com/OneGov/onegov-cloud/compare/ba603604f7^...a87288c7de)

### Town6

##### Allow adding custom service links.

`Feature` | [OGC-67](https://linear.app/onegovcloud/issue/OGC-67) | [ba603604f7](https://github.com/onegov/onegov-cloud/commit/ba603604f7012c26d29d03c88a4616ecb5f315e1)

## 2021.75

`2021-08-31` | [77256a0752...748908aa6c](https://github.com/OneGov/onegov-cloud/compare/77256a0752^...748908aa6c)

### Agency

##### Enable topics (without sidebar).

`Feature` | [OGC-26](https://linear.app/onegovcloud/issue/OGC-26) | [77256a0752](https://github.com/onegov/onegov-cloud/commit/77256a075296b6e3fddc7f5c03ee71c4ae5d663b)

## 2021.74

`2021-08-30` | [6ed7b747d4...d79ede1b6f](https://github.com/OneGov/onegov-cloud/compare/6ed7b747d4^...d79ede1b6f)

### Core

##### Replace namespace parameter of transfer command with schema parameter.

`Feature` | [9493b3f02d](https://github.com/onegov/onegov-cloud/commit/9493b3f02dd55f1c105fd0f442e7bc31ddde170f)

### Election Day

##### Add map data for 2004-2012.

`Feature` | [OGC-71](https://linear.app/onegovcloud/issue/OGC-71) | [6ed7b747d4](https://github.com/onegov/onegov-cloud/commit/6ed7b747d4168e6c25098fd434db062fcd6e0485)

##### Add subscriber export.

`Feature` | [OGC-59](https://linear.app/onegovcloud/issue/OGC-59) | [c5760bbc35](https://github.com/onegov/onegov-cloud/commit/c5760bbc3541dc146ce973de224a9419bcfe130f)

##### Make logo position configurable.

`Feature` | [OGC-32](https://linear.app/onegovcloud/issue/OGC-32) | [9e83c9ed1b](https://github.com/onegov/onegov-cloud/commit/9e83c9ed1bdf749eeee23f1b32d49da06007187f)

## 2021.73

`2021-08-19` | [75541aaa4f...121a1c22f7](https://github.com/OneGov/onegov-cloud/compare/75541aaa4f^...121a1c22f7)

### Core

##### Add namespace parameter to transfer command.

`Feature` | [9dd82a4809](https://github.com/onegov/onegov-cloud/commit/9dd82a48096256c0ccfba09c35320424a9c95c66)

### Election Day

##### Log exceptions when creating media rather than failing.

`Bugfix` | [48cc67dbc8](https://github.com/onegov/onegov-cloud/commit/48cc67dbc8707fd92655b67978d3c9bb6c075432)

### Org

##### Fixes ticket view throwing an error for tickets with no users.

`Bugfix` | [84fe7d58b3](https://github.com/onegov/onegov-cloud/commit/84fe7d58b36f0aae88a94d91a6253b3b85cd1a1f)

### Translatordirectory

##### Don't create FSI course attendees when importing from the ldap.

`Bugfix` | [OGC-24](https://linear.app/onegovcloud/issue/OGC-24) | [75541aaa4f](https://github.com/onegov/onegov-cloud/commit/75541aaa4f53ec93663321d67da4daeeff6798ab)

## 2021.72

`2021-08-17` | [5daf5fdef3...11ed322b63](https://github.com/OneGov/onegov-cloud/compare/5daf5fdef3^...11ed322b63)

### All

##### Disable ticket deletion.

`Bugfix` | [e7bae3e990](https://github.com/onegov/onegov-cloud/commit/e7bae3e9905c99d0fcf5db3ba1b8d60129989015)

### Org

##### Validate recurrence dates in event submission form.

`Bugfix` | [0814cbe033](https://github.com/onegov/onegov-cloud/commit/0814cbe03395c9746e90a496200e8cff5444082e)

##### Show ticket state of archived tickets.

`Bugfix` | [2eafdc83d5](https://github.com/onegov/onegov-cloud/commit/2eafdc83d540846677dc2aaaa025fc555533a5f2)

##### Fixes link migration labels.

`Bugfix` | [SEA-357](https://linear.app/seantis/issue/SEA-357) | [33e0bdd6ec](https://github.com/onegov/onegov-cloud/commit/33e0bdd6ecf158a2f91ebffd807291362cb2fc68)

## 2021.71

`2021-07-28` | [7698b0add9...cda5a59e55](https://github.com/OneGov/onegov-cloud/compare/7698b0add9^...cda5a59e55)

### Foundation6

##### Updates jquery to version 3.6

- Introduces browser console inspection in tests
- Minor fixes in javascripts
- Rework of foundation update cli command

`Other` | [SEA-469](https://linear.app/seantis/issue/SEA-469) | [48209df535](https://github.com/onegov/onegov-cloud/commit/48209df535b842f0daa2e52540b261897ff003df)

### Town6

##### Adds color darkgray for <row-wide> homepage widget

`Other` | [SEA_467](#SEA_467) | [2acce24eba](https://github.com/onegov/onegov-cloud/commit/2acce24eba094322714c4d08e375692fbfe0f266)

## 2021.70

`2021-07-26` | [0301017794...900d210a51](https://github.com/OneGov/onegov-cloud/compare/0301017794^...900d210a51)

### Org

##### Adds Ticket Archive

- Adds batch archving to /tickets
- Enable Deletion of tickets in /ticket-archive
- Adds Ticket Archive to management links
- Migrates archived state to ticket.state

`Feature` | [SEA-378](https://linear.app/seantis/issue/SEA-378) | [f208f1530e](https://github.com/onegov/onegov-cloud/commit/f208f1530e8c3b409a902216ef4b328aea75fa7c)

##### Adds deletion of form definitions

Makes deleting of forms definitions with submission, files and registration window possible.
Tickets are snapshotted before object is deleted.

`Feature` | [SEA_392](#SEA_392) | [ca5893a81b](https://github.com/onegov/onegov-cloud/commit/ca5893a81b3f3d731d8d6f98c4215c21e38ee383)

### Ticket

##### Adapt TicketCollection for archived

- return ticket count filtered by archived
- Adds TicketsArchive collection

`Other` | [16599a2e51](https://github.com/onegov/onegov-cloud/commit/16599a2e5101ca6d96b33d740665100da1414a18)

### Town6

##### Adds deletion of forms with submissions

- Adds check of a form definition with submissions is deletable
- Changes delete button on town6 /form/{name} accordingly
- Use safeguard for forms without registration windows: All tickets must be closed
Deleting forms submissions that have a registration window only possible when:
- no tickets of any submissions are open. In that case, the user is supposed to cancel the window first.
- there are no undecided submission
Before deleting the submission, a ticket snapshot is made and all tickets of any submissions are closed.

`Feature` | [SEA-392](https://linear.app/seantis/issue/SEA-392) | [2616c517bb](https://github.com/onegov/onegov-cloud/commit/2616c517bb29d185ad97508fe3e7cd96b6e76798)

## 2021.69

`2021-07-21` | [ce47e0802a...25cd05cfa7](https://github.com/OneGov/onegov-cloud/compare/ce47e0802a^...25cd05cfa7)

### Agency

##### Add publication windows to people, agencies and memberships.

Agency: Add publication windows to people, agencies and memberships.

`Feature` | [STAKABS-32](https://kt-bs.atlassian.net/browse/STAKABS-32) | [8b59fe2a9e](https://github.com/onegov/onegov-cloud/commit/8b59fe2a9e52b2e68d1076c54a7d4727a511b453)

### Org

##### Enable sensible defaults for ticket deletion

- Restrict ticket on tickets here data has been removed and are closed
- Tickets can not be closed when still requiering a decision
- Fix error on registration window view if ticket to submission is missing

`Bugfix` | [SEA-378](https://linear.app/seantis/issue/SEA-378) | [7ea2a293a1](https://github.com/onegov/onegov-cloud/commit/7ea2a293a1c7bcb6fec15a2d839038c0a2d8759d)

## 2021.68

`2021-07-20` | [f9a40771a4...9c0b161b06](https://github.com/OneGov/onegov-cloud/compare/f9a40771a4^...9c0b161b06)

### Onboarding

##### Change to town6

`Other` | [SEA-265](https://linear.app/seantis/issue/SEA-265) | [554a65007e](https://github.com/onegov/onegov-cloud/commit/554a65007e75e763e39a0c5085bb5c3c48d9b8b9)

## 2021.67

`2021-07-17` | [a20fdb76e6...1cc14ad7ec](https://github.com/OneGov/onegov-cloud/compare/a20fdb76e6^...1cc14ad7ec)

### Agency

##### Improves mutations

Users can directly propose changes to fields of agencies and people. Redactors can select, which changes they want to apply.

`Feature` | [STAKABS-34](https://kt-bs.atlassian.net/browse/STAKABS-34) | [ed6fa6b812](https://github.com/onegov/onegov-cloud/commit/ed6fa6b812f8b43f89851899cb3233355f6b6a97)

### Org

##### Adds activity log for ticket assignment.

`Feature` | [STAKABS-25](https://kt-bs.atlassian.net/browse/STAKABS-25) | [a20fdb76e6](https://github.com/onegov/onegov-cloud/commit/a20fdb76e68acda358e714c61651d68383c00e7c)

##### Send an email when assigning a ticket.

`Feature` | [STAKABS-25](https://kt-bs.atlassian.net/browse/STAKABS-25) | [aad2eb2293](https://github.com/onegov/onegov-cloud/commit/aad2eb2293e56264be4c52009bb67a8e0966ddc9)

## 2021.66

`2021-07-14` | [a9b7ec37d4...4fbfdfc306](https://github.com/OneGov/onegov-cloud/compare/a9b7ec37d4^...4fbfdfc306)

### Org

##### Prevents server error on directory export if files are missing

Will redirect the user to the broken directory entry with missing file hint

`Bugfix` | [FW-92](https://stadt-winterthur.atlassian.net/browse/FW-92) | [a9b7ec37d4](https://github.com/onegov/onegov-cloud/commit/a9b7ec37d43944c4b61f3faba30ccc8b9aa7ef6f)

##### Show pagerefs only for logged in users

- change default to hide the pagerefs
- Update settings explanation

`Other` | [a8bd9f916b](https://github.com/onegov/onegov-cloud/commit/a8bd9f916bfb73e646d8d13d52a67aca902cd205)

### Town6

##### Adds QrCode link to town6

- Adds Qr Edit Bar Link to /form/{name}

`Feature` | [SEA-380](https://linear.app/seantis/issue/SEA-380) | [aef24f862b](https://github.com/onegov/onegov-cloud/commit/aef24f862b20fdbcdf9b772d9303f704ab03a83e)

##### Improve form styling

- center checkboxes and labels vertical axis
- Fix long field help indentation for checkboxes

`Other` | [570166bc4d](https://github.com/onegov/onegov-cloud/commit/570166bc4d7cb4905bb249112ecbb9174fbc702f)

## 2021.65

`2021-07-12` | [fd3d3fef03...cc2737b26a](https://github.com/OneGov/onegov-cloud/compare/fd3d3fef03^...cc2737b26a)

### Agency

##### Add direct phone number to search index.

There are two new settings to enable direct phone numbers in the search 
index. Direct phone numbers are simply the last n digits of the phone or 
direct phone number. Direct phone numbers are suggest when searching.

`Feature` | [STAKABS-33](https://kt-bs.atlassian.net/browse/STAKABS-33) | [7db6e64a97](https://github.com/onegov/onegov-cloud/commit/7db6e64a97a0413bca3a91cf1c01b65c046a4627)

### Org

##### Add ticket inbox and ticket assignments.

Adds a 'My Tickets' views where all pending and open tickets of the 
currently logged-in user are displayed. Furthermore, it's now possible 
to assign a ticket to another user.

`Feature` | [STAKABS-25](https://kt-bs.atlassian.net/browse/STAKABS-25) | [fd3d3fef03](https://github.com/onegov/onegov-cloud/commit/fd3d3fef031741b56bf2927de212ffbd5f8f7082)

##### Adds modal for message form on ticket status page

`Feature` | [SEA-429](https://linear.app/seantis/issue/SEA-429) | [76df37e465](https://github.com/onegov/onegov-cloud/commit/76df37e46506821da8c992246b2b54fcac967476)

##### Adds copy links for page references

- adds page reference settings to /link-settings
- enbales '#' copy links on /forms and /resources if grouped
- applies for town6 as well

`Feature` | [SEA-446](https://linear.app/seantis/issue/SEA-446) | [9f82d1df5d](https://github.com/onegov/onegov-cloud/commit/9f82d1df5d6483e9dae84abd117e2de58ce99da3)

##### Adds change-url form to /form/{form-name} to change name of the form

`Feature` | [SEA-381](https://linear.app/seantis/issue/SEA-381) | [4934115701](https://github.com/onegov/onegov-cloud/commit/49341157014507b03b90eedf389f1da138157591)

