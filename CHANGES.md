# Changes

## 2023.23

`2023-05-26` | [29781ded8d...2b39d886b8](https://github.com/OneGov/onegov-cloud/compare/29781ded8d^...2b39d886b8)

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

## 2022.47

`2022-09-11` | [73cba7eba1...655cc2fe97](https://github.com/OneGov/onegov-cloud/compare/73cba7eba1^...655cc2fe97)

## 2022.46

`2022-09-11` | [e6857e75b0...c697cabe7a](https://github.com/OneGov/onegov-cloud/compare/e6857e75b0^...c697cabe7a)

### Agency

##### Use secure requests for map integration.

`Bugfix` | [OGC-241](https://linear.app/onegovcloud/issue/OGC-241) | [0ca196bb00](https://github.com/onegov/onegov-cloud/commit/0ca196bb0058b21c481ab51fec2e000e17151cd4)

### Core

##### Fixes documentation not being built.

Also cleanup the documentation.

`Bugfix` | [OGC-481](https://linear.app/onegovcloud/issue/OGC-481) | [46007815bd](https://github.com/onegov/onegov-cloud/commit/46007815bdfebf778546cae8be659374aa75f204)

##### Removes obsolete package from documentation.

`Bugfix` | [OGC-589](https://linear.app/onegovcloud/issue/OGC-589) | [fb904c42d3](https://github.com/onegov/onegov-cloud/commit/fb904c42d33f08f8212215819a666912523f4260)

### Core 

##### Use autoapi for documentation.

`Feature` | [OGC-589](https://linear.app/onegovcloud/issue/OGC-589) | [1a886c594a](https://github.com/onegov/onegov-cloud/commit/1a886c594af0d61883e3316704cb6302d1552b15)

### Feriennet

##### Clarify labels and error messages for QR bill settings.

`Feature` | [PRO-1003](https://linear.app/projuventute/issue/PRO-1003) | [3ec3340d35](https://github.com/onegov/onegov-cloud/commit/3ec3340d3551c0af88ee697c8898b60ba3f9b233)

##### Check if news item is in siblings list

`Bugfix` | [e67d91c886](https://github.com/onegov/onegov-cloud/commit/e67d91c886ed3e25f2d601b0d8269d41e4ec2068)

##### Fixes occasion choices in notification template not being rendered as HTML.

`Bugfix` | [PRO-1079](https://linear.app/projuventute/issue/PRO-1079) | [87ec196dbe](https://github.com/onegov/onegov-cloud/commit/87ec196dbe841c4e70f85bedd24dc200f03ca74e)

##### Make test less flaky.

`Bugfix` | [OGC-587](https://linear.app/onegovcloud/issue/OGC-587) | [72fb109fcd](https://github.com/onegov/onegov-cloud/commit/72fb109fcd5522df35b68f99d5cfc57eddd87e76)

### Pay

##### Allow disabling payment providers.

`Feature` | [PRO-1026](https://linear.app/projuventute/issue/PRO-1026) | [0489204323](https://github.com/onegov/onegov-cloud/commit/0489204323ee2f1759c7ad75d09ae986cfb18108)

### Town

##### Display absolute date instead of relative.

`Feature` | [OGC-576](https://linear.app/onegovcloud/issue/OGC-576) | [baf5c7696c](https://github.com/onegov/onegov-cloud/commit/baf5c7696ce4c7162c0230e39880e2f68ef6d7ef)

##### Remove town package.

`Other` | [OGC-594](https://linear.app/onegovcloud/issue/OGC-594) | [625c802b6a](https://github.com/onegov/onegov-cloud/commit/625c802b6a81051876624f7bad25058c4cd4b348)

### User

##### Revert back to using a string field instead of an email field for logins.

`Bugfix` | [OGC-591](https://linear.app/onegovcloud/issue/OGC-591) | [b4dd0109aa](https://github.com/onegov/onegov-cloud/commit/b4dd0109aa48154f3290e22cf66e7640b023ea57)

## 2022.45

`2022-09-04` | [bdb747639b...711063ad8c](https://github.com/OneGov/onegov-cloud/compare/bdb747639b^...711063ad8c)

### Pdf

##### Remove whitespaces from PDF extracts.

`Feature` | [f523c8c174](https://github.com/onegov/onegov-cloud/commit/f523c8c1749e571c701fc1c7c0f80c1fef567544)

##### Allow to remove additional characters from PDF extracts.

`Feature` | [5cdddf291e](https://github.com/onegov/onegov-cloud/commit/5cdddf291e40f8463dcbb32e50d69f9ff5ac7c55)

### People

##### Fix agency upgrade step.

`Bugfix` | [f09e155b1f](https://github.com/onegov/onegov-cloud/commit/f09e155b1fd0026f17cfd1732ba75a34e27a246a)

## 2022.44

`2022-09-03` | [563b896390...a3ae3af9e9](https://github.com/OneGov/onegov-cloud/compare/563b896390^...a3ae3af9e9)

### Core

##### Add add-admins flag to transfer command.

`Feature` | [89ed4bbbec](https://github.com/onegov/onegov-cloud/commit/89ed4bbbecffb119de3d7be51795fe24335f3863)

##### Switch to python 3.10.

`Feature` | [OGC-578](https://linear.app/onegovcloud/issue/OGC-578) | [63a6f19e9a](https://github.com/onegov/onegov-cloud/commit/63a6f19e9a8cf8d0d3914a553f6175e2aae835b2)

## 2022.43

`2022-09-02` | [560eca5cfb...9892b57ca2](https://github.com/OneGov/onegov-cloud/compare/560eca5cfb^...9892b57ca2)

### Activity

##### Improve compatibility with Postgres 14.

`Feature` | [OGC-83](https://linear.app/onegovcloud/issue/OGC-83) | [5f5c8a04d4](https://github.com/onegov/onegov-cloud/commit/5f5c8a04d4af2b18bdf68750c374b5809b7ba6f0)

##### Fixes wrong default polymorphic type of activities.

`Bugfix` | [5eda430c2a](https://github.com/onegov/onegov-cloud/commit/5eda430c2ab553692319b3e94b068c18e0915375)

##### Cleanup unused aggregate function.

The signature of array_cat has changed with Postgres 14 from anyarray to  anycompatiblearray.

`Other` | [OGC-83](https://linear.app/onegovcloud/issue/OGC-83) | [08146274d9](https://github.com/onegov/onegov-cloud/commit/08146274d9f32e8deca7957e73185842ea07a653)

### Agency

##### Add API.

`Feature` | [OGC-535](https://linear.app/onegovcloud/issue/OGC-535) | [5a6f78d374](https://github.com/onegov/onegov-cloud/commit/5a6f78d374e29efb32b2c50e8586a230ff68a02f)

##### Add Map for Agencies

`Feature` | [OGC-241](https://linear.app/onegovcloud/issue/OGC-241) | [692cc0f48e](https://github.com/onegov/onegov-cloud/commit/692cc0f48ed359e000434032383af3789d7d3172)

### Async Http

##### Improve compatibility with python 3.10.

`Feature` | [5d1bc287dd](https://github.com/onegov/onegov-cloud/commit/5d1bc287dde0e4ade44dbacc41b9bd106691bfa2)

### Core

##### Resolve python 3.10 deprecation warning.

`Feature` | [91ed2ce94e](https://github.com/onegov/onegov-cloud/commit/91ed2ce94e809e501ac37e12323e2c63e274775d)

##### Add option for transfering databases from postgres <14 to >=13.

`Feature` | [OGC-83](https://linear.app/onegovcloud/issue/OGC-83) | [95532c97fb](https://github.com/onegov/onegov-cloud/commit/95532c97fbc40c152d624489f0924833e1d5c264)

##### Make HTML sanitizer a little bit more robust.

`Feature` | [1c4a38199a](https://github.com/onegov/onegov-cloud/commit/1c4a38199a8e3572c8cc5257a70807f296ae978a)

### Election Day

##### Optimize forms for screen readers.

`Feature` | [OGC-544](https://linear.app/onegovcloud/issue/OGC-544) | [e78d55ba7f](https://github.com/onegov/onegov-cloud/commit/e78d55ba7f6ec983e61c349b1931caf4eaee6c9b)

##### Give screen readers a hint about missing title translations.

`Feature` | [OGC-546](https://linear.app/onegovcloud/issue/OGC-546) | [8808b4006b](https://github.com/onegov/onegov-cloud/commit/8808b4006b170b68d8ef4c3f1f68b3106351a55a)

##### Add sitemap.

`Feature` | [OGC-543](https://linear.app/onegovcloud/issue/OGC-543) | [60f639bd40](https://github.com/onegov/onegov-cloud/commit/60f639bd4057ad31bb3ee5e26692ca245f4d9d39)

##### Specify titles for archive and archive-search

`Feature` | [OGC-559](https://linear.app/onegovcloud/issue/OGC-559) | [27c6bda146](https://github.com/onegov/onegov-cloud/commit/27c6bda146c809ca384b280dc713a71bb154765e)

##### Make pagination more accesible

`Feature` | [OGC-550](https://linear.app/onegovcloud/issue/OGC-550) | [d285fb5773](https://github.com/onegov/onegov-cloud/commit/d285fb577323da1dd205d3d687fd2162b90393b4)

##### Set focus to first invalid field

`Feature` | [OGC-561](https://linear.app/onegovcloud/issue/OGC-561) | [5de9b0b0bf](https://github.com/onegov/onegov-cloud/commit/5de9b0b0bf45c9b62cfed85fbfdd9c671768fb71)

##### Add hidden links for accessiblity

`Feature` | [OGC-558](https://linear.app/onegovcloud/issue/OGC-558) | [39021506df](https://github.com/onegov/onegov-cloud/commit/39021506df270d0af0de5fcfb46a466841e34cee)

##### Fix table layout

`Bugfix` | [OGC-282](https://linear.app/onegovcloud/issue/OGC-282) | [120739bfd6](https://github.com/onegov/onegov-cloud/commit/120739bfd61c430f3c44161cf5ee7401d0351c12)

##### Adjust title-tag for screen reader

`Bugfix` | [OGC-264](https://linear.app/onegovcloud/issue/OGC-264) | [a3ac94c878](https://github.com/onegov/onegov-cloud/commit/a3ac94c87880d2408f12e76c213da6d6c99db7e6)

##### Merge list elements in one list

`Bugfix` | [OGC-553](https://linear.app/onegovcloud/issue/OGC-553) | [d37010337d](https://github.com/onegov/onegov-cloud/commit/d37010337d4c45c0920ac0176e3bab6e066fd154)

##### Add principal name to alt-description

`Bugfix` | [OGC-540](https://linear.app/onegovcloud/issue/OGC-540) | [e8f7587865](https://github.com/onegov/onegov-cloud/commit/e8f758786596d0d978ac578d529cba476479fc9a)

##### Add p-tags for text

`Bugfix` | [OGC-542](https://linear.app/onegovcloud/issue/OGC-542) | [60108babe7](https://github.com/onegov/onegov-cloud/commit/60108babe7e280a860f28a8e1258fc74402ba640)

##### Change first columns to table headers

`Bugfix` | [OGC-555](https://linear.app/onegovcloud/issue/OGC-555) | [e5742acc88](https://github.com/onegov/onegov-cloud/commit/e5742acc8816b48f0091dcc265cd00b142ed3844)

##### Fix order of title-tags

`Bugfix` | [OGC-551](https://linear.app/onegovcloud/issue/OGC-551) | [960c9eb5fd](https://github.com/onegov/onegov-cloud/commit/960c9eb5fdbd42d5502d3a9a91efd6d9f05f8522)

##### Add hidden text of tooltip for screenreaders

`Bugfix` | [OGC-549](https://linear.app/onegovcloud/issue/OGC-549) | [ef437909b9](https://github.com/onegov/onegov-cloud/commit/ef437909b923abb9b6b014189d5c6359850d6872)

### Feriennet

##### Trims QR bill debtor addresses to 70 characters.

`Feature` | [PRO-1011](https://linear.app/projuventute/issue/PRO-1011) | [bd710558fd](https://github.com/onegov/onegov-cloud/commit/bd710558fd0927efe5e2beea3f3a7d26dc7d9264)

##### Clarify payment labels.

`Feature` | [PRO-1003](https://linear.app/projuventute/issue/PRO-1003) | [96c4d4842f](https://github.com/onegov/onegov-cloud/commit/96c4d4842fd4480c813b42e57fdef06ccb5a4388)

### Org

##### Add custom CSS.

`Feature` | [OGC-567](https://linear.app/onegovcloud/issue/OGC-567) | [a8efc4a4ee](https://github.com/onegov/onegov-cloud/commit/a8efc4a4eec45754f95b98239db7d97d0fa1b668)

##### Removes duplicate macro. (#467)

`Bugfix` | [560eca5cfb](https://github.com/onegov/onegov-cloud/commit/560eca5cfb43585e938c06707804c6ef6c6c45d0)

##### Fixes typos.

`Bugfix` | [16724c0b8d](https://github.com/onegov/onegov-cloud/commit/16724c0b8d6460dbc71e5cd854a3af0ed44c24ba)

##### Specify titles for archive and archive-search

`Bugfix` | [OGC-559](https://linear.app/onegovcloud/issue/OGC-559) | [ec55f569b5](https://github.com/onegov/onegov-cloud/commit/ec55f569b5cba0fef39b00602dc6228cfdae5acc)

##### Put back code for find-your-spot link

`Bugfix` | [OGC-569](https://linear.app/onegovcloud/issue/OGC-569) | [53d5dbd7d9](https://github.com/onegov/onegov-cloud/commit/53d5dbd7d95c4f024c11876943cae4e5dae40359)

##### Abort if duplicate directory entries are inserted.

`Bugfix` | [OGC-425](https://linear.app/onegovcloud/issue/OGC-425) | [6332646360](https://github.com/onegov/onegov-cloud/commit/63326463601f85350d7a9a829a4bfa2a704cffed)

### Search

##### Resolve ES deprecation warning.

`Feature` | [40f5bbdd44](https://github.com/onegov/onegov-cloud/commit/40f5bbdd447f44963fa50632093381d052a28613)

### Town

##### Display find-your-spot link as icon

`Feature` | [OGC-569](https://linear.app/onegovcloud/issue/OGC-569) | [a436c0ec4d](https://github.com/onegov/onegov-cloud/commit/a436c0ec4d0bf81ec67c650fc44a179ea5202cf2)

### Town6

##### Add video widget for homepage

`Feature` | [OGC-527](https://linear.app/onegovcloud/issue/OGC-527) | [55dbb506eb](https://github.com/onegov/onegov-cloud/commit/55dbb506eb5ae9fb6ec5be678cc869fea479dc9b)

##### Add more news on news detail page

`Feature` | [OGC-201](https://linear.app/onegovcloud/issue/OGC-201) | [50badb9e0c](https://github.com/onegov/onegov-cloud/commit/50badb9e0c1c7b618526566bd5e700a904ec6446)

##### Add definite color to button for safari

`Bugfix` | [OGC-570](https://linear.app/onegovcloud/issue/OGC-570) | [d69d953413](https://github.com/onegov/onegov-cloud/commit/d69d95341386d20d24a2eb739da5160509f9b110)

### User

##### Ensures local logout always happens before external logout

`Bugfix` | [OGC-430](https://linear.app/onegovcloud/issue/OGC-430) | [f27307c838](https://github.com/onegov/onegov-cloud/commit/f27307c838820376e7f895e7bccd1d76f253f77f)

### Wtfs

##### Make tests less flaky.

`Bugfix` | [57b932904b](https://github.com/onegov/onegov-cloud/commit/57b932904b92b7cd9e72a057ae7039b06af72f5d)

## 2022.42

`2022-08-20` | [716b38ea1c...e33267cd5b](https://github.com/OneGov/onegov-cloud/compare/716b38ea1c^...e33267cd5b)

### Agency

##### Allow to change URLs of agencies.

`Feature` | [OGC-109](https://linear.app/onegovcloud/issue/OGC-109) | [c8646e20da](https://github.com/onegov/onegov-cloud/commit/c8646e20daf4141e55db8ab79d90d6fd4ab527c3)

##### Fixes sort template being overwritten.

Also adjusts the appearance of the two templates to each other.

`Bugfix` | [7bfca0ee4b](https://github.com/onegov/onegov-cloud/commit/7bfca0ee4b2c2639ede05fc035fc6aef64098c0e)

### Core

##### Update chameleon to 3.10.

`Other` | [OGC-19](https://linear.app/onegovcloud/issue/OGC-19) | [e8e0acf684](https://github.com/onegov/onegov-cloud/commit/e8e0acf684b653ba1ca5ae84dda5375d4c321c19)

### Election Day

##### Display expats per entity.

`Feature` | [OGC-384](https://linear.app/onegovcloud/issue/OGC-384) | [716b38ea1c](https://github.com/onegov/onegov-cloud/commit/716b38ea1cfdadc72b35fd8686a323bfb38c95ed)

##### Add more information to the election compound districts map and make it clickable.

`Feature` | [OGC-491](https://linear.app/onegovcloud/issue/OGC-491) | [54c863be71](https://github.com/onegov/onegov-cloud/commit/54c863be71d528753eff5f7d6118abc71f035fcd)

##### Add testdata set for GR regional election compound.

`Feature` | [OGC-377](https://linear.app/onegovcloud/issue/OGC-377) | [e7ab3ec763](https://github.com/onegov/onegov-cloud/commit/e7ab3ec763de9565c732c297d90bbd729c78c0e7)

##### Add mapdata for 2022.

`Feature` | [OGC-224](https://linear.app/onegovcloud/issue/OGC-224) | [0d1ebe3c4e](https://github.com/onegov/onegov-cloud/commit/0d1ebe3c4e26edc39ce730f6d5d2163cef98e541)

##### Update translations.

`Feature` | [6369d54af5](https://github.com/onegov/onegov-cloud/commit/6369d54af58df545bbd0e3beeed5a053274c70b0)

##### Fixes open data download text for votes.

`Bugfix` | [OGC-534](https://linear.app/onegovcloud/issue/OGC-534) | [83264fecef](https://github.com/onegov/onegov-cloud/commit/83264fecefce9204b542180e343531b9f3331cfc)

### Feriennet

##### Update Banner.

`Feature` | [PRO-1077](https://linear.app/projuventute/issue/PRO-1077) | [46947418f3](https://github.com/onegov/onegov-cloud/commit/46947418f3321e128fc85d842085dcef96a67c17)

##### Update Banner URL.

`Other` | [PRO-1077](https://linear.app/projuventute/issue/PRO-1077) | [abcc396c36](https://github.com/onegov/onegov-cloud/commit/abcc396c36e13ee74724e9acb9536f43ff4113f5)

### Form

##### Add aria-required attribute.

`Feature` | [OGC-374](https://linear.app/onegovcloud/issue/OGC-374) | [fa0dfe6d2c](https://github.com/onegov/onegov-cloud/commit/fa0dfe6d2c8612203266c93b466f64323c467de6)

##### Allow UploadField to optionally resend the last uploaded file in case of errors.

Also, avoid using forms raw_data directly.

`Feature` | [OGC-429](https://linear.app/onegovcloud/issue/OGC-429) | [4f4097413a](https://github.com/onegov/onegov-cloud/commit/4f4097413a11a47821d2a0001e98b9230be80380)

##### Remove decpracted HTMLString.

`Other` | [OGC-22](https://linear.app/onegovcloud/issue/OGC-22) | [a01797694f](https://github.com/onegov/onegov-cloud/commit/a01797694f5d26344e817dbb0f19ff92332efee2)

##### Update wtforms to 2.3.

`Other` | [OGC-22](https://linear.app/onegovcloud/issue/OGC-22) | [5b31194f64](https://github.com/onegov/onegov-cloud/commit/5b31194f641fd3fe4491c67d137d6b09a48feefe)

##### Update wtforms to 3.

`Other` | [OGC-22](https://linear.app/onegovcloud/issue/OGC-22) | [1c6820cad0](https://github.com/onegov/onegov-cloud/commit/1c6820cad0a0860a86e9fbe7db87d4c65394cae6)

### Fsi

##### Correct typo

`Bugfix` | [11d5ce1a08](https://github.com/onegov/onegov-cloud/commit/11d5ce1a08fc4c5a9e3ce019c14f8e54552fc2a7)

### Org

##### Fixes news date filter.

`Bugfix` | [OGC-260](https://linear.app/onegovcloud/issue/OGC-260) | [6069424543](https://github.com/onegov/onegov-cloud/commit/6069424543ff53bc368a8dab6a9342e65bb452fe)

##### Adjust upload file size limit to 5 MB

`Bugfix` | [OGC-498](https://linear.app/onegovcloud/issue/OGC-498) | [d59474c882](https://github.com/onegov/onegov-cloud/commit/d59474c8828f85567218eb5f8b46b9f3d7090c41)

### Town6

##### Add animations for homepage widgets

`Feature` | [OGC-189](https://linear.app/onegovcloud/issue/OGC-189) | [37cea33c95](https://github.com/onegov/onegov-cloud/commit/37cea33c953f36fb1bf5848767074686c116feb1)

### User

##### Removes trailing '/' from name_id in SAML2 client.

`Bugfix` | [3d0b81c15b](https://github.com/onegov/onegov-cloud/commit/3d0b81c15b531b26f774bb4c2a3ca581ccd8af82)

## 2022.41

`2022-08-10` | [ad737f8401...d1172ef864](https://github.com/OneGov/onegov-cloud/compare/ad737f8401^...d1172ef864)

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

