# Changes

## 2026.11

`2026-02-27` | [f5feeeea66...6730b8d860](https://github.com/OneGov/onegov-cloud/compare/f5feeeea66^...6730b8d860)

### Feriennet

##### Show error if file cannot be displayed in photo album

`Feature` | [OGC-2976](https://linear.app/onegovcloud/issue/OGC-2976) | [6730b8d860](https://github.com/onegov/onegov-cloud/commit/6730b8d860436c2d1ebfeea74f43ea2c0b95ae8e)

##### Fix period info

Show wishlist info not only when wishlist phase is active

`Bugfix` | [PRO-1487](https://linear.app/projuventute/issue/PRO-1487) | [33fe463c48](https://github.com/onegov/onegov-cloud/commit/33fe463c48b1ccfef78a3d9520414e6365ad02ac)

##### Prevent photoalbum and photoalbum overview from crashing due to missing size attribute (e.g. video)

This is just an intermediate step. We may need to handle different file types in albums differently

`Bugfix` | [OGC-2976](https://linear.app/onegovcloud/issue/OGC-2976) | [31a6fed7c2](https://github.com/onegov/onegov-cloud/commit/31a6fed7c27933281242b1bc0490da68a6bf695d)

### Org

##### Adds a change username function for admins

Changing usernames is only allowed for users that are not sourced from
an external login provider and if the current admin user has either a
Yubikey or TOTP second factor configured (mTAN is not yet supported).

This also adds a CLI command to change usernames, which can be utilized
in all applications, not just Org.

`Feature` | [OGC-2532](https://linear.app/onegovcloud/issue/OGC-2532) | [4b4467c068](https://github.com/onegov/onegov-cloud/commit/4b4467c068fe9add20957ecde58e2443a941ba87)

##### Makes `OrgRequest.current_user` more robust

With SQLAlchemy 2.0 it is possible for the `User` object to become
detached, which can result in errors if we try to access a deferred
attribute later on.

`Bugfix` | [47bf5c3bd0](https://github.com/onegov/onegov-cloud/commit/47bf5c3bd0cf87baa1bcf1f9b57c8e7f86616421)

##### Fixes inverted condition in allocation display

`Bugfix` | [OGC-2984](https://linear.app/onegovcloud/issue/OGC-2984) | [17e9addabd](https://github.com/onegov/onegov-cloud/commit/17e9addabde93d74f60661976585c15f3e067cd7)

### Pas

##### Fixes an issue with comma in filename on windows.

`Bugfix` | [NONE](#NONE) | [64908b60ac](https://github.com/onegov/onegov-cloud/commit/64908b60ac0b0ef184d62d8181a096c378aef130)

##### Make sure address fits in letter.

`Bugfix` | [NONE](#NONE) | [0d478902be](https://github.com/onegov/onegov-cloud/commit/0d478902beda550c5cd7f8c9e4d11acfbcd31b57)

##### Display the true value for plenary session.

`Bugfix` | [NONE](#NONE) | [7fac7accd6](https://github.com/onegov/onegov-cloud/commit/7fac7accd61a164d84ad6ae71f6129d9b327eec2)

##### Round to two decimal places.

`Bugfix` | [74859ffcc8](https://github.com/onegov/onegov-cloud/commit/74859ffcc85a968c0d6df2fcca99222bbf82863d)

### Town6

##### Remove searchbar in empty slider

Don't display the searchbar if there are no images in the slider

`Other` | [f5feeeea66](https://github.com/onegov/onegov-cloud/commit/f5feeeea66ccc9ff407fc3008f434afbde8eabb5)

### Wab

##### Handle invalid polling day date

`Feature` | [OGC-2785](https://linear.app/onegovcloud/issue/OGC-2785) | [3d0b3fe3d4](https://github.com/onegov/onegov-cloud/commit/3d0b3fe3d4c4a1e5db126e8122a64214260c8393)

##### Prevent cli update archived results for development and staging

As `official_host` is not set for development and staging, cli `upload-archived-results` may cause duplicates when uploading new results due to different urls.

`Feature` | [OGC-2978](https://linear.app/onegovcloud/issue/OGC-2978) | [34820b252c](https://github.com/onegov/onegov-cloud/commit/34820b252c306342d9defa6f2f38bbf4d3fcdb48)

## ui

`2026-02-23` | [dd502dc069...997bc59a4a](https://github.com/OneGov/onegov-cloud/compare/dd502dc069^...997bc59a4a)

## 2026.10

`2026-02-20` | [673622456d...007adfdc2d](https://github.com/OneGov/onegov-cloud/compare/673622456d^...007adfdc2d)

### Wab

##### Improve error handling for xml file upload

`Bugfix` | [OGC-2785](https://linear.app/onegovcloud/issue/OGC-2785) | [673622456d](https://github.com/onegov/onegov-cloud/commit/673622456dfe01f640bab2527068fa659acae899)

## ui

`2026-02-20` | [dd502dc069...a7ce12aa8e](https://github.com/OneGov/onegov-cloud/compare/dd502dc069^...a7ce12aa8e)

### Feriennet

##### Add contact form, photoalbums and volunteer to main menu

Add link to the first form in form colleciton, link to photoalbums and link to volunteer activity list to the navigation.

`Feature` | [PRO-1468](https://linear.app/projuventute/issue/PRO-1468) | [0388161dc8](https://github.com/onegov/onegov-cloud/commit/0388161dc8e346c12a8c350c7ca9d16b5601d5ac)

### Org

##### Ensure mime type validation on file upload fields in form code

`Feature` | [OGC-2738](https://linear.app/onegovcloud/issue/OGC-2738) | [ff77bff6b9](https://github.com/onegov/onegov-cloud/commit/ff77bff6b96074d7c5ce5a85d7a50c818287176f)

## 2026.9

`2026-02-19` | [01dce7374a...3042c5af71](https://github.com/OneGov/onegov-cloud/compare/01dce7374a^...3042c5af71)

### Core

##### Upgrades to SQLAlchemy 2.0

`Feature` | [OGC-2945](https://linear.app/onegovcloud/issue/OGC-2945) | [dea56b3a58](https://github.com/onegov/onegov-cloud/commit/dea56b3a588dcccaada62728638773f5bdfb967b)

### Feriennet

##### Update homepage template

`Feature` | [65a5d96515](https://github.com/onegov/onegov-cloud/commit/65a5d965159661bea145f415ffdbc3cd6639206d)

##### Fix problem with selecting user for manual booking

- The dropdown for the users now pre-selects the correct user again.
- The users are now displayed correctly again and can be selected

`Bugfix` | [PRO-1481](https://linear.app/projuventute/issue/PRO-1481) | [574e4844b6](https://github.com/onegov/onegov-cloud/commit/574e4844b6e79a980688a40b82bbafedebaf89ff)

##### Fix problem with volunteer list

Newly loaded activity needs could not be added to the volunteers list

`Bugfix` | [PRO-1480](https://linear.app/projuventute/issue/PRO-1480) | [8a1f72e2ac](https://github.com/onegov/onegov-cloud/commit/8a1f72e2ac3ab1476626427ce186b2479be65af9)

### Pas

##### Add bulk operations for shortest meeting.

`Feature` | [OGC-2941](https://linear.app/onegovcloud/issue/OGC-2941) | [3b7d41a6c8](https://github.com/onegov/onegov-cloud/commit/3b7d41a6c85dc095915d6f7659e6099ad2a6a7c7)

##### Granular improvements based on feedback.

`Feature` | [OGC-2941](https://linear.app/onegovcloud/issue/OGC-2941) | [51ed0825eb](https://github.com/onegov/onegov-cloud/commit/51ed0825eb506b72922902e286a2e08a95b7f7a8)

### Town 6

##### Fix form size when files are attached

`Bugfix` | [OGC-2908](https://linear.app/onegovcloud/issue/OGC-2908) | [01dce7374a](https://github.com/onegov/onegov-cloud/commit/01dce7374a84d28bce8f9950164d14c6c7f295da)

## 2026.8

`2026-02-17` | [56a0169055...e39ad8b3da](https://github.com/OneGov/onegov-cloud/compare/56a0169055^...e39ad8b3da)

## 2026.7

`2026-02-17` | [f20e7fc393...2189bbd8f8](https://github.com/OneGov/onegov-cloud/compare/f20e7fc393^...2189bbd8f8)

### Feriennet

##### Resolves n+1 queries for homepage

Sentry examples:

    https://seantis-gmbh.sentry.io/issues/trace/0c49d7a3f0314d11acec7a2859f47232/
    https://seantis-gmbh.sentry.io/issues/trace/72578e382105402aac1ef2a6c37e056b/

`Performance` | [NONE](#NONE) | [f20e7fc393](https://github.com/onegov/onegov-cloud/commit/f20e7fc393a11557e862c93cb95e64486c43d04d)

## 2026.6

`2026-02-16` | [8101345cbe...f7481046ca](https://github.com/OneGov/onegov-cloud/compare/8101345cbe^...f7481046ca)

### Directories

##### Improves description for map configuration

Replaces word `coordinate` with `map` to explain what really happens.

`Feature` | [OGC-2883](https://linear.app/onegovcloud/issue/OGC-2883) | [cde5e5f3f8](https://github.com/onegov/onegov-cloud/commit/cde5e5f3f87be6fd77b1a1a85afd909d0d42f51a)

### Electionday

##### Improve layout for proposal, counterproposal and tie-breaker

`Feature` | [OGC-2850](https://linear.app/onegovcloud/issue/OGC-2850) | [872c94297d](https://github.com/onegov/onegov-cloud/commit/872c94297df645929aa115ff019ff7216a04da44)

##### Fix missing indent if no results for complex vote

`Bugfix` | [OGC-2850](https://linear.app/onegovcloud/issue/OGC-2850) | [d10d4b7cd6](https://github.com/onegov/onegov-cloud/commit/d10d4b7cd6604edb9110e8c4fa3bcf27e4287462)

### Org

##### Adds icon to vat settings menu

`Bugfix` | [OGC-2917](https://linear.app/onegovcloud/issue/OGC-2917) | [11aaf9700b](https://github.com/onegov/onegov-cloud/commit/11aaf9700b6f45ad7c791ca37d536827172ce5d5)

### Town6

##### Fix Dashboard in case of unavailable web statistics

`Bugfix` | [NONE](#NONE) | [d48491fc95](https://github.com/onegov/onegov-cloud/commit/d48491fc9579ef5336d7553261e0ddc1dce23ff2)

## test

`2026-02-11` | [dd502dc069...b8306cab4c](https://github.com/OneGov/onegov-cloud/compare/dd502dc069^...b8306cab4c)

### Town6

##### Fix bug in datetime selection

`Bugfix` | [PRO-1478](https://linear.app/projuventute/issue/PRO-1478) | [0a4012edd8](https://github.com/onegov/onegov-cloud/commit/0a4012edd806ba1f1cb46d471f460484984e8368)

## 2026.5

`2026-02-10` | [7178b5005b...c93df57ee5](https://github.com/OneGov/onegov-cloud/compare/7178b5005b^...c93df57ee5)

**Upgrade hints**
- onegov-election-day --select /onegov_election_day/gr update-archived-results
### Core

##### Prepares for SQLAlchemy 2.0 upgrade

`Feature` | [OGC-2944](https://linear.app/onegovcloud/issue/OGC-2944) | [ea2ef0eb7f](https://github.com/onegov/onegov-cloud/commit/ea2ef0eb7ff6e9162e3b935ae7fcaf98c736e2eb)

### Feriennet

##### Period display bugfix

`Bugfix` | [OGC-1467](https://linear.app/onegovcloud/issue/OGC-1467) | [111eac326b](https://github.com/onegov/onegov-cloud/commit/111eac326b77d44da6c0d757c66c78fab9c0e3b0)

### Landsgemeinde

##### Allows refining search results with a date range

All relevant content types now use the assembly date as their reference
date in the search index.

`Feature` | [OGC-2909](https://linear.app/onegovcloud/issue/OGC-2909) | [65746148d2](https://github.com/onegov/onegov-cloud/commit/65746148d202c25738e79cc3c53d3b5505fad893)

### Org

##### Avoids confusion by sometimes hiding the availability text

Allocations that are in the past or no longer/not yet available
because they're outside the registration window would previously
sometimes say that they're available, or partly available, even
though they can't be reserved. Since the reason for why they're
currently unavailable can be a bit contrived, it's better to not
display anything at all. Customers will still get a clear explanation
when they try to reserve these slots.

`Feature` | [OGC-2334](https://linear.app/onegovcloud/issue/OGC-2334) | [0e575db9cc](https://github.com/onegov/onegov-cloud/commit/0e575db9cc7662715f58093221e2e277638d1119)

##### Fixes CSP for Stripe/Datatrans payments

`Bugfix` | [OGC-2948](https://linear.app/onegovcloud/issue/OGC-2948) | [ccf901324f](https://github.com/onegov/onegov-cloud/commit/ccf901324faef9bf73bb66b4fc3021108fa34513)

##### Fixes blocker created with no reason being set to `null`

`Bugfix` | [OGC-2954](https://linear.app/onegovcloud/issue/OGC-2954) | [28fb8697dc](https://github.com/onegov/onegov-cloud/commit/28fb8697dccb64c642a3529803f04c2578d90f6e)

##### Fixes regression in `send_ticket_mail`

`Bugfix` | [OGC-2960](https://linear.app/onegovcloud/issue/OGC-2960) | [d983f55617](https://github.com/onegov/onegov-cloud/commit/d983f556171c49d87100825928628af424d2cd8a)

### Town 6

##### Searchbar on homepage slider and video

`Feature` | [OGC-2790](https://linear.app/onegovcloud/issue/OGC-2790) | [5fa5d7056e](https://github.com/onegov/onegov-cloud/commit/5fa5d7056e2a0d9c74cf9dfd57e3f274f3494dc8)

### Town6

##### Fix display bug of images

`Bugfix` | [OGC-2901](https://linear.app/onegovcloud/issue/OGC-2901) | [93b61635fa](https://github.com/onegov/onegov-cloud/commit/93b61635fad07090fb0195ff74312b0c52be0c2d)

### Wab

##### Show proposal, counterproposal and tie-breaker results separately for complex votes

`Feature` | [OGC-2850](https://linear.app/onegovcloud/issue/OGC-2850) | [435dbf9ae8](https://github.com/onegov/onegov-cloud/commit/435dbf9ae8c85197e60d213591ce0a11b90fa5d4)

## 2026.4

`2026-01-30` | [574f21d1c1...195a697ab3](https://github.com/OneGov/onegov-cloud/compare/574f21d1c1^...195a697ab3)

### Directory

##### Fix directory migration crash when renaming option labels

`Bugfix` | [OGC-2353](https://linear.app/onegovcloud/issue/OGC-2353) | [6bbe21e2a0](https://github.com/onegov/onegov-cloud/commit/6bbe21e2a0647bcbb428908d5aee663a9dc8a7b2)

### Org

##### Replaces data-attributes that triggered a call of `eval`

This means we no longer have any views where we have to add a narrow
`unsafe-eval` exception to the CSP, in order to make things work.

`Feature` | [OGC-2916](https://linear.app/onegovcloud/issue/OGC-2916) | [24b52c862e](https://github.com/onegov/onegov-cloud/commit/24b52c862e06d2097c85848194445f5ec8304ad2)

### Page

##### Improve iframe domain validation to for configured domains.

Right split trailing slashes from configured domains prior comparison

`Feature` | [OGC-2940](https://linear.app/onegovcloud/issue/OGC-2940) | [005ce6fc34](https://github.com/onegov/onegov-cloud/commit/005ce6fc34f25b27cfaaa05d14cc8e4c736dc48a)

### Pas

##### Validate attendance to be within a settlement run.

`Bugfix` | [OGC-2848](https://linear.app/onegovcloud/issue/OGC-2848) | [9762773489](https://github.com/onegov/onegov-cloud/commit/97627734897050e2435e9a2d0622a3e66af017d0)

##### Ensure finalized attendance for commission.

`Bugfix` | [OGC-2845](https://linear.app/onegovcloud/issue/OGC-2845) | [58d94c5689](https://github.com/onegov/onegov-cloud/commit/58d94c568988d3748aa184372b1ee755ac0c858a)

## 2026.3

`2026-01-29` | [e17f907a3b...742db7bad0](https://github.com/OneGov/onegov-cloud/compare/e17f907a3b^...742db7bad0)

### Feriennet

##### Banner

`Feature` | [PRO-1474](https://linear.app/projuventute/issue/PRO-1474) | [09587de5de](https://github.com/onegov/onegov-cloud/commit/09587de5dec6f8da0f64717cc926937b4a535983)

### Org

##### Adds a resource switcher to the occupancy view

`Feature` | [OGC-2873](https://linear.app/onegovcloud/issue/OGC-2873) | [3943814f00](https://github.com/onegov/onegov-cloud/commit/3943814f00d40378b65be76af3100f4f9ec34114)

##### Adds an utilization stats button to the occupancy view

`Feature` | [OGC-2062](https://linear.app/onegovcloud/issue/OGC-2062) | [0baff1be97](https://github.com/onegov/onegov-cloud/commit/0baff1be97f0105c4f9fb3fdb37c292a93e91350)

##### Adds missing access hints in boardlets

`Bugfix` | [cd3d24431a](https://github.com/onegov/onegov-cloud/commit/cd3d24431a59ab8edde4049e50eb5b8ba5decb51)

##### Resolve fixme for TagField

`Bugfix` | [92b85f250f](https://github.com/onegov/onegov-cloud/commit/92b85f250f0f9cd3d0101ed082ff9d057c3a43bf)

##### Fixes reservation blockers for non-partly available allocations

`Bugfix` | [OGC-2937](https://linear.app/onegovcloud/issue/OGC-2937) | [92064770d5](https://github.com/onegov/onegov-cloud/commit/92064770d54e48997a5d471a859def6ab336f022)

### Search

##### Adds it_ch to used locales for Org and Town6

`Feature` | [OGC-2931](https://linear.app/onegovcloud/issue/OGC-2931) | [138cf9df78](https://github.com/onegov/onegov-cloud/commit/138cf9df78942706cddb5c1f7a55cb373d3cb59e)

### Town6

##### Allow to copy newsletter.

`Feature` | [OGC-1663](https://linear.app/onegovcloud/issue/OGC-1663) | [9af1fd1d74](https://github.com/onegov/onegov-cloud/commit/9af1fd1d74a7297f6314e7c093b0363220e399fc)

## 2026.2

`2026-01-23` | [7fe7cf163c...2f191d9543](https://github.com/OneGov/onegov-cloud/compare/7fe7cf163c^...2f191d9543)

### Core

##### Upgrades SQLAlchemy to version 1.4

`Feature` | [OGC-15](https://linear.app/onegovcloud/issue/OGC-15) | [7fe7cf163c](https://github.com/onegov/onegov-cloud/commit/7fe7cf163c340b75a7d5d99b18a07cd6ecd74dd1)

### Town6

##### Change background-size from cover to contain for image display.

`Bugfix` | [OGC-2867](https://linear.app/onegovcloud/issue/OGC-2867) | [8687186243](https://github.com/onegov/onegov-cloud/commit/86871862437fff784be55c4d0b4e607d45f8ff3a)

##### Increases robustness if underlying pdf of form doesn't exist.

`Bugfix` | [OGC-2922](https://linear.app/onegovcloud/issue/OGC-2922) | [1314f1bdf8](https://github.com/onegov/onegov-cloud/commit/1314f1bdf83b0fa65528bc9a2b5ed1e8436047e0)

## 2026.1

`2026-01-16` | [93d40ac5bd...b829bbf934](https://github.com/OneGov/onegov-cloud/compare/93d40ac5bd^...b829bbf934)

### Api

##### Extends standard Collection+JSON with a couple of meta properties

This provides additional context to users of the API, what each endpoint
contains.

`Feature` | [OGC-2912](https://linear.app/onegovcloud/issue/OGC-2912) | [68dd72486c](https://github.com/onegov/onegov-cloud/commit/68dd72486ccec8fa57adf9dd42036be7fb0bda62)

### Core

##### Replaces free-text analytics code with configurable providers

`Feature` | [OGC-2865](https://linear.app/onegovcloud/issue/OGC-2865) | [232119d51a](https://github.com/onegov/onegov-cloud/commit/232119d51a51b820c0603b4d35583e30b47825c5)

##### Makes default Content-Security-Policy more strict

Core: Makes default Content-Security-Policy more strict

This also updates foundation6 to the latest version as well as various
JS components, so they comply with the more strict CSP

`Feature` | [OGC-2740](https://linear.app/onegovcloud/issue/OGC-2740) | [231ad17b91](https://github.com/onegov/onegov-cloud/commit/231ad17b916e951909a0889f570f7b3eb1407aba)

##### Fix duplicate Message-ID header causing email queue failures.

`Bugfix` | [60ff3e03a5](https://github.com/onegov/onegov-cloud/commit/60ff3e03a5e2ae09e2a1823dc6d21f9a1dd01504)

##### Fix transfer command to use DSN connection parameters.

The transfer command was using `sudo -u postgres psql` which connects
to the system postgres user's default instance instead of respecting
the `onegov.yml` DSN configuration. This commit allows to use ports other 
than 5432 locally.

`Bugfix` | [6fc268cab6](https://github.com/onegov/onegov-cloud/commit/6fc268cab6d70a7c6269888acdc82f03bf69d4c8)

### Directory

##### Rename sidebar contact field

`Feature` | [OGC-2829](https://linear.app/onegovcloud/issue/OGC-2829) | [65fbf10196](https://github.com/onegov/onegov-cloud/commit/65fbf101961336bc24ee04e1546fc92e47851f75)

### Electionday

##### Adds map data and municipalities for 2026

`Feature` | [OGC-2906](https://linear.app/onegovcloud/issue/OGC-2906) | [6e8051b97d](https://github.com/onegov/onegov-cloud/commit/6e8051b97dc7a07636b0c126968bdc125de94208)

##### Fixes municipality and quarter data for 2026

`Bugfix` | [OGC-2906](https://linear.app/onegovcloud/issue/OGC-2906) | [57b7f49a21](https://github.com/onegov/onegov-cloud/commit/57b7f49a21c54e6aa46e505b46164d5b9c3eb2ff)

### Feriennet

##### Removes inline event handlers from templates

`Feature` | [OGC-2863](https://linear.app/onegovcloud/issue/OGC-2863) | [e357dd701e](https://github.com/onegov/onegov-cloud/commit/e357dd701e6d8c17285bdc0cabbfd61fb0fbb3a4)

##### Add narrow banners for email

`Bugfix` | [OGC-1460](https://linear.app/onegovcloud/issue/OGC-1460) | [170eea5533](https://github.com/onegov/onegov-cloud/commit/170eea5533674c7a238a58a872519df26c0ac12e)

##### Order of activities in activity widget

`Bugfix` | [PRO-1456](https://linear.app/projuventute/issue/PRO-1456) | [a854f104f1](https://github.com/onegov/onegov-cloud/commit/a854f104f1681c20fd148a74462b2d50ddadce84)

##### Filter "show more" bugfix

`Bugfix` | [PRO-1452](https://linear.app/projuventute/issue/PRO-1452) | [dc02194d72](https://github.com/onegov/onegov-cloud/commit/dc02194d72ba7962a451c6639f35de9d6803dc1b)

### Org

##### Improves e-mail threading for customer-facing ticket e-mails

We achieve this by setting (and remembering) the `Message-ID` and
setting the corresponding `In-Reply-To` and `References` headers.

`Feature` | [OGC-2869](https://linear.app/onegovcloud/issue/OGC-2869) | [6d761226e2](https://github.com/onegov/onegov-cloud/commit/6d761226e224ec32a71a493c7088f50fb28105a8)

##### Allows accepted reservations to be adjusted by managers

`Feature` | [OGC-2887](https://linear.app/onegovcloud/issue/OGC-2887) | [8ec0519afb](https://github.com/onegov/onegov-cloud/commit/8ec0519afbdcfd2fe9f6a7f457ba6398b1bf9454)

##### Adds administrative reservation blockers in the occupancy calendar

`Feature` | [OGC-2780](https://linear.app/onegovcloud/issue/OGC-2780) | [fbf6bf5cda](https://github.com/onegov/onegov-cloud/commit/fbf6bf5cdaeae102ce2817e39e37d6064d863ddb)

##### Fixes crash in invoice export for a large number of ticket groups

`Bugfix` | [OGC-2902](https://linear.app/onegovcloud/issue/OGC-2902) | [f928399ca0](https://github.com/onegov/onegov-cloud/commit/f928399ca0c9a0e717c02b751329cf6ba2ded498)

### Pas

##### Extend kub api call timeouts

As we found various sentry issues related to kub api timeouts

`Feature` | [NONE](#NONE) | [b8de6b01e5](https://github.com/onegov/onegov-cloud/commit/b8de6b01e5abf0aa0f5991f17a03a533e835058e)

##### Fixes N+1 query.

`Bugfix` | [c84cbe7755](https://github.com/onegov/onegov-cloud/commit/c84cbe775507cb4999547e5e69961c3f10be5df1)

### Resource

##### On resource deletion, handle archived tickets' date fields that may contain "[redacted]" instead of a datetime object.

`Feature` | [OGC-2793](https://linear.app/onegovcloud/issue/OGC-2793) | [409a5a323d](https://github.com/onegov/onegov-cloud/commit/409a5a323df27de407c5b986460a987530c50a40)

### Town6

##### Sidebar navigation closing

`Bugfix` | [OGC-2871](https://linear.app/onegovcloud/issue/OGC-2871) | [93d40ac5bd](https://github.com/onegov/onegov-cloud/commit/93d40ac5bd7d98654fe1c915d91bd465c8f29688)

##### Fixes some link elements crashing during rendering

`Bugfix` | [03fc0ce134](https://github.com/onegov/onegov-cloud/commit/03fc0ce13437d7756b61bc72c99045ffc20b6baf)

##### Fix image selection bug

`Bugfix` | [OGC-2901](https://linear.app/onegovcloud/issue/OGC-2901) | [86f2a7b2b6](https://github.com/onegov/onegov-cloud/commit/86f2a7b2b69a570dc7f5451fc9b6bde70daf4757)

### User

##### Adds explicit `last_login` column.

`Feature` | [OGC-2454](https://linear.app/onegovcloud/issue/OGC-2454) | [790bad6a9a](https://github.com/onegov/onegov-cloud/commit/790bad6a9ac0ceb3e8515021e92eb8b571f174a7)

## 2025.71

`2025-12-29` | [23c7322afb...cadf75d90c](https://github.com/OneGov/onegov-cloud/compare/23c7322afb^...cadf75d90c)

### Feriennet

##### Hide RSS Feed

`Feature` | [PRO-1458](https://linear.app/projuventute/issue/PRO-1458) | [8cbd225102](https://github.com/onegov/onegov-cloud/commit/8cbd225102b2207d1959b782cb99021f9399801a)

##### "Delete user" button

Deletion of a user in feriennet is now possible under the following conditions:
-    Has no attendees with bookings in the currently active period
-    Has no unpaid invoices in any period
-    Is not an organizer of any activities
-    Is not an admin

`Feature` | [PRO-987](https://linear.app/projuventute/issue/PRO-987) | [c4a775e09e](https://github.com/onegov/onegov-cloud/commit/c4a775e09e935f39e452ffc7bad4b70be72151ba)

##### Delete attendees

`Feature` | [PRO-1436](https://linear.app/projuventute/issue/PRO-1436) | [1fb8ee16a1](https://github.com/onegov/onegov-cloud/commit/1fb8ee16a18b3b3f2ec81cdf2a4135243226fe4c)

### Pas

##### Gets rid of inline event handler.

`Bugfix` | [OGC-2860](https://linear.app/onegovcloud/issue/OGC-2860) | [dde589d60e](https://github.com/onegov/onegov-cloud/commit/dde589d60eb6c1d7105886234b4f1789545127b9)

## 2025.70

`2025-12-19` | [7e83cff80c...2bf159789f](https://github.com/OneGov/onegov-cloud/compare/7e83cff80c^...2bf159789f)

### Form

##### Adds select all/deselect all buttons for multi checkbox fields

The buttons only get displayed if there are at least five options to
choose from. This also fixes a small bug with form resets when
there is a treeselect field present.

`Feature` | [OGC-2369](https://linear.app/onegovcloud/issue/OGC-2369) | [388a69d422](https://github.com/onegov/onegov-cloud/commit/388a69d422f66e76d9d3995bf5c0ba53d7c62560)

##### Identify wrongly indented identifier

But prevent wrongly indentation when loading a form

`Feature` | [OGC-2370](https://linear.app/onegovcloud/issue/OGC-2370) | [2cb04a6c3a](https://github.com/onegov/onegov-cloud/commit/2cb04a6c3a1e04ded187c1b576a506bd9824fbed)

### Org

##### Specify hint for notifications about ticket messages

`Feature` | [OGC-2672](https://linear.app/onegovcloud/issue/OGC-2672) | [7e83cff80c](https://github.com/onegov/onegov-cloud/commit/7e83cff80ce90a15888bd6eb2a0f05028be7be62)

##### Adds additional ways discounts in reservations can be calculated

Previously discounts always applied to the price per item/hour and
ignored any prices defined through extra fields. Now you can choose
to apply the discounts to just the extras, or everything at the end
as well.

`Feature` | [OGC-2263](https://linear.app/onegovcloud/issue/OGC-2263) | [4225ae51ba](https://github.com/onegov/onegov-cloud/commit/4225ae51baa8acd18930c3fb078c7fa11dd3f372)

##### Add o'clock in events time display.

`Feature` | [OGC-2763](https://linear.app/onegovcloud/issue/OGC-2763) | [4fd9547d95](https://github.com/onegov/onegov-cloud/commit/4fd9547d95085f281ce8abf0c4225d1c3902353a)

##### Improves search ranking for records that match with their title

`Feature` | [OGC-2789](https://linear.app/onegovcloud/issue/OGC-2789) | [98151c54a2](https://github.com/onegov/onegov-cloud/commit/98151c54a25327cbd9cdd6973d08051954b44477)

##### Produces smaller query strings for large ticket group filters

This improves compatibility with nginx proxies without having to resort
to very large buffer sizes.

`Bugfix` | [OGC-2824](https://linear.app/onegovcloud/issue/OGC-2824) | [93858c4997](https://github.com/onegov/onegov-cloud/commit/93858c499716ad86e5eaf8ce7bd5c33dd64b4f52)

### Pas

##### Disable YubiKey.

The two-factor authentication will be handled via a different
method; therefore, we do not want to use a YubiKey for this
namespace.

`Bugfix` | [0e6bb6554b](https://github.com/onegov/onegov-cloud/commit/0e6bb6554b7ced8701765630ab50c1c3223e2f6f)

### Ris

##### Fix N+1 Query for Parliamentarian view

`Performance` | [OGC-2876](https://linear.app/onegovcloud/issue/OGC-2876) | [af8e5530c0](https://github.com/onegov/onegov-cloud/commit/af8e5530c051365a1a1eefa152b92dbd601c635a)

### Search

##### Adds basic search result highlighting

This also moves string normalization from the client to the Postgres
server. This involves a little bit of additional setup on the server
but provides a better result highlighting experience.

`Feature` | [OGC-2881](https://linear.app/onegovcloud/issue/OGC-2881) | [e3b9d7d410](https://github.com/onegov/onegov-cloud/commit/e3b9d7d410f3dbd277e4c31b430adbb06df2a85c)

### Town6

##### Fix wrong event tag translation for Parties

`Bugfix` | [OGC-2890](https://linear.app/onegovcloud/issue/OGC-2890) | [d5b58c8026](https://github.com/onegov/onegov-cloud/commit/d5b58c8026fc8ec4e3dbbb659c27e8efabeaf8e9)

### Wil

##### Adds cli command to rename meeting files before July 2025

`Feature` | [OGC-2815](https://linear.app/onegovcloud/issue/OGC-2815) | [63e3cca045](https://github.com/onegov/onegov-cloud/commit/63e3cca0457180d30000ae758831faf6c691bcc4)

##### Event import failed due to missing location data

Some events recently do not provide location data which made the nightly import fail.

`Bugfix` | [OGC-2875](https://linear.app/onegovcloud/issue/OGC-2875) | [5506bfbb42](https://github.com/onegov/onegov-cloud/commit/5506bfbb42f53212db20977d198cd231758ca637)

### Winterthur

##### Gets rid of inline JavaScript in templates

`Feature` | [OGC-2859](https://linear.app/onegovcloud/issue/OGC-2859) | [e5df575d22](https://github.com/onegov/onegov-cloud/commit/e5df575d226662fe81a522c3f03e47284788de88)

## 2025.69

`2025-12-09` | [b39432183e...68810065f9](https://github.com/OneGov/onegov-cloud/compare/b39432183e^...68810065f9)

### Directory

##### Accordion mode now reflects the content fields hide labels from configuration

`Feature` | [OGC-2832](https://linear.app/onegovcloud/issue/OGC-2832) | [546a3bd918](https://github.com/onegov/onegov-cloud/commit/546a3bd9188472ab90d1a8088eb5ba11ac52ab3b)

### Feriennet

##### Remove privacy option in general settings and add in export

`Feature` | [OGC-1454](https://linear.app/onegovcloud/issue/OGC-1454) | [4246ff777d](https://github.com/onegov/onegov-cloud/commit/4246ff777d51667de2dac8f11243b136d1943390)

## 2025.68

`2025-12-05` | [5440ea7e83...979b8b8912](https://github.com/OneGov/onegov-cloud/compare/5440ea7e83^...979b8b8912)

### Core

##### Applies a more strict `Cache-Control` setting for logged in users

`Feature` | [OGC-2753](https://linear.app/onegovcloud/issue/OGC-2753) | [7e72534569](https://github.com/onegov/onegov-cloud/commit/7e72534569b7dfbbc2f3245cf3ffe1c9dab3d67b)

### Form

##### Improve error message for comment field indentation errors

`Feature` | [OGC-2311](https://linear.app/onegovcloud/issue/OGC-2311) | [36912ab924](https://github.com/onegov/onegov-cloud/commit/36912ab924f9bad4f3bc88bc39c8a602741e51fb)

### Landsgemeinde

##### Move print button

`Feature` | [OGC-2830](https://linear.app/onegovcloud/issue/OGC-2830) | [7a527a7780](https://github.com/onegov/onegov-cloud/commit/7a527a7780289f3887f582348ce3b37c4569aa18)

##### Removes inline javascript from templates

`Feature` | [OGC-2861](https://linear.app/onegovcloud/issue/OGC-2861) | [34b4446c7b](https://github.com/onegov/onegov-cloud/commit/34b4446c7b856e3c8874176263f64b8288c31ba7)

### Org

##### Allows extra fields to be displayed in occupancy view

Also slightly changes the order of values in the occupancy view so the
most important information is least likely to be visually cut off.

`Feature` | [OGC-2843](https://linear.app/onegovcloud/issue/OGC-2843) | [e8f1bfd8bf](https://github.com/onegov/onegov-cloud/commit/e8f1bfd8bf58a2eb10c71935a0b38d7605233789)

##### Makes reservation date filtering on payments/invoices more flexible

`Feature` | [OGC-2600](https://linear.app/onegovcloud/issue/OGC-2600) | [3e6cba29b6](https://github.com/onegov/onegov-cloud/commit/3e6cba29b64673c3c0b6d87d0ebf3776c9f0fc04)

##### Allows related tickets to be muted/unmuted from any related ticket

`Feature` | [OGC-2844](https://linear.app/onegovcloud/issue/OGC-2844) | [e2ea34a04b](https://github.com/onegov/onegov-cloud/commit/e2ea34a04b26f1c4f07dbbf862cc0ab1acb965ee)

##### Adds a tree select filter widget for payment/invoices

`Feature` | [OGC-2824](https://linear.app/onegovcloud/issue/OGC-2824) | [0ac1805858](https://github.com/onegov/onegov-cloud/commit/0ac1805858df97dcda18dcbf54c117cb36d3c357)

##### Allows allocations to define their own pricing

This serves use-cases like charging more for reservations on a weekend

`Feature` | [OGC-2768](https://linear.app/onegovcloud/issue/OGC-2768) | [1e50067e5d](https://github.com/onegov/onegov-cloud/commit/1e50067e5d3de845c84b4bd54ef4696d73930d27)

##### Removes inline javascript from the templates

This is preparation work for tightening up our Content-Security-Policy

`Feature` | [OGC-2864](https://linear.app/onegovcloud/issue/OGC-2864) | [ec68f8a057](https://github.com/onegov/onegov-cloud/commit/ec68f8a0570b0e143480bfb502b5f3e1be160574)

##### Video iFrame error

`Bugfix` | [OGC-2837](https://linear.app/onegovcloud/issue/OGC-2837) | [ae0da86876](https://github.com/onegov/onegov-cloud/commit/ae0da86876e95009f8369c9f9da2d3cad8ab71f5)

##### Fix bad redirect when rejecting reservation with comment

`Bugfix` | [OGC-2786](https://linear.app/onegovcloud/issue/OGC-2786) | [b54f36cf36](https://github.com/onegov/onegov-cloud/commit/b54f36cf360dffdcb2ba7ab23d89e3140460c285)

### Pas

##### Fixes by-effect of RIS refactoring on PAS.

Fixes commission edit form not having a save button.

`Bugfix` | [OGC-2847](https://linear.app/onegovcloud/issue/OGC-2847) | [9e98b030b6](https://github.com/onegov/onegov-cloud/commit/9e98b030b60ef9b73e39566b72a71302c80a186a)

##### Fixes dropdown syncing for commission presidents.

`Bugfix` | [OGC-2846](https://linear.app/onegovcloud/issue/OGC-2846) | [a42fd32358](https://github.com/onegov/onegov-cloud/commit/a42fd3235844b39968b570b84394b0faa9004274)

##### Fixes dropdown syncing for parliamentarians.

`Bugfix` | [OGC-2846](https://linear.app/onegovcloud/issue/OGC-2846) | [fc831a5829](https://github.com/onegov/onegov-cloud/commit/fc831a582977276ab99894fb9cbc59a13bae25c4)

### Ris

##### Multiple parliamentary groups can now be linked to a political business

`Feature` | [OGC-2816](https://linear.app/onegovcloud/issue/OGC-2816) | [fffb5c21b2](https://github.com/onegov/onegov-cloud/commit/fffb5c21b2c5a6324ca9e56b46c6a92603b46e4a)

##### Improve filename extraction, extension and file icon determination

`Bugfix` | [OGC-2813](https://linear.app/onegovcloud/issue/OGC-2813) | [eb0b0a9942](https://github.com/onegov/onegov-cloud/commit/eb0b0a9942992ccb8f7501360db3101ca90ed078)

### Town6

##### Adds a search field to the list of political businesses

`Feature` | [OGC-2836](https://linear.app/onegovcloud/issue/OGC-2836) | [5440ea7e83](https://github.com/onegov/onegov-cloud/commit/5440ea7e83618533c8380c394e55b98c0f85c980)

## 2025.67

`2025-11-27` | [98c33a124a...c4d2fbf0ed](https://github.com/OneGov/onegov-cloud/compare/98c33a124a^...c4d2fbf0ed)

### Feriennet

##### Make occasion location multi line

`Feature` | [OGC-1451](https://linear.app/onegovcloud/issue/OGC-1451) | [c1ca601070](https://github.com/onegov/onegov-cloud/commit/c1ca601070445ae1818150219988d8f331a72933)

##### Organizer text if username is not set

Resolves sentry issue https://seantis-gmbh.sentry.io/issues/7025105745/

`Bugfix` | [NONE](#NONE) | [98c33a124a](https://github.com/onegov/onegov-cloud/commit/98c33a124a0fede9464dc53de04a6324fd5a76e2)

### Org

##### Add option to add imagesets to resources

`Feature` | [OGC-2276](https://linear.app/onegovcloud/issue/OGC-2276) | [f858a0cd87](https://github.com/onegov/onegov-cloud/commit/f858a0cd87aa6694458b1433126f677febf17c0a)

##### Adds a content type filter to the search

`Feature` | [OGC-2834](https://linear.app/onegovcloud/issue/OGC-2834) | [9a52069202](https://github.com/onegov/onegov-cloud/commit/9a52069202b758b474e7c005b78d7c0a7578bc65)

##### Avoids crash in search for malicious queries

`Bugfix` | [ce796dcc24](https://github.com/onegov/onegov-cloud/commit/ce796dcc246fa317e17b9f352a8faf93d7e3dbcb)

##### Changes ticket link in occupancy view for all logged in members

`Bugfix` | [OGC-2781](https://linear.app/onegovcloud/issue/OGC-2781) | [3c83cc09e0](https://github.com/onegov/onegov-cloud/commit/3c83cc09e0e0f92e2d5bee3207f39e5fb4fb984f)

### Pas

##### Fixes a bug in plenary session attendance.

`Feature` | [OGC-2787](https://linear.app/onegovcloud/issue/OGC-2787) | [5ea0bf004c](https://github.com/onegov/onegov-cloud/commit/5ea0bf004cdf3af1f846f49f37709923b233eacd)

### Ris

##### Remove political business number from overview

`Feature` | [OGC-2818](https://linear.app/onegovcloud/issue/OGC-2818) | [fa559658b3](https://github.com/onegov/onegov-cloud/commit/fa559658b36a5dc0e9a2ea40bda83ecc33178f38)

### Search

##### Makes parliamentarians available in search results

Makes parliamentarians, commissions and parliamentary groups documents independent of its age

`Feature` | [OGC-2788](https://linear.app/onegovcloud/issue/OGC-2788) | [bef509a57d](https://github.com/onegov/onegov-cloud/commit/bef509a57d2d484fac4a21783cd01d4611c90584)

### Town6

##### Adds a search field to the tickets and tickets archive

`Feature` | [OGC-2460](https://linear.app/onegovcloud/issue/OGC-2460) | [5e0b58d6b8](https://github.com/onegov/onegov-cloud/commit/5e0b58d6b8dff7d1f0f84eb2b82259a38c5e2cef)

##### Display allocation rule title below actions

`Bugfix` | [OGC-2819](https://linear.app/onegovcloud/issue/OGC-2819) | [e64567c7cc](https://github.com/onegov/onegov-cloud/commit/e64567c7ccb31c561bd2c7e3c4e09b779ea12b9f)

### User

##### Avoids crash for some second factor authentication failures

`Bugfix` | [3f9a6e6d03](https://github.com/onegov/onegov-cloud/commit/3f9a6e6d035a14cf371f9e7e1bced913cc381018)

## 2025.66

`2025-11-21` | [c001eb871d...df97031e21](https://github.com/OneGov/onegov-cloud/compare/c001eb871d^...df97031e21)

### Feriennet

##### Banners

`Feature` | [PRO-1443](https://linear.app/projuventute/issue/PRO-1443) | [7a37fb75df](https://github.com/onegov/onegov-cloud/commit/7a37fb75dffcd7d2dade97583b942b7ffd6dec0d)

##### New Privacy Settings

Users can now decide themselves if their contact data is shown to other attendees of the same course.

`Feature` | [OGC-1415](https://linear.app/onegovcloud/issue/OGC-1415) | [eef7415188](https://github.com/onegov/onegov-cloud/commit/eef7415188972d4a4cd2db48b4e011fca4e18116)

##### Line break for occasion description

`Bugfix` | [PRO-1449](https://linear.app/projuventute/issue/PRO-1449) | [6b98614db6](https://github.com/onegov/onegov-cloud/commit/6b98614db64d05f52a27be967d2e86aea4084d6e)

### Org

##### Adds cli command to list resources

`Feature` | [OGC-2335](https://linear.app/onegovcloud/issue/OGC-2335) | [0a935fd78c](https://github.com/onegov/onegov-cloud/commit/0a935fd78c5a5dd9ce733daf82ef96d680f6e85b)

##### Reservation button

`Feature` | [OGC-2441](https://linear.app/onegovcloud/issue/OGC-2441) | [3ed6fa2867](https://github.com/onegov/onegov-cloud/commit/3ed6fa286762b50f4be78115192a0680425c59ad)

##### Change editbar_links for allocation settings

`Bugfix` | [OGC-2368](https://linear.app/onegovcloud/issue/OGC-2368) | [d3040df735](https://github.com/onegov/onegov-cloud/commit/d3040df7353081b8e97489f8c0283afe0c6721e2)

### Search

##### Index parliamentarians, commissions and parliamentary groups

`Feature` | [OGC-2788](https://linear.app/onegovcloud/issue/OGC-2788) | [352d6a93c2](https://github.com/onegov/onegov-cloud/commit/352d6a93c232c15ed6d6e80590b7466737fcda8f)

### Swissvotes

##### News labels

Some text changes

`Feature` | [SWI-64](https://linear.app/swissvotes/issue/SWI-64) | [411fedc985](https://github.com/onegov/onegov-cloud/commit/411fedc98549ff46cc9727127010f1ef27b14ba4)

### Town6

##### Unlink Resource from payment and invoice before deleting it

`Bugfix` | [OGC-2719](https://linear.app/onegovcloud/issue/OGC-2719) | [eeb3e22489](https://github.com/onegov/onegov-cloud/commit/eeb3e224891e292ac5805cea8e8b12a330b355d9)

##### Anchor distance

`Bugfix` | [OGC-2777](https://linear.app/onegovcloud/issue/OGC-2777) | [042ef0f258](https://github.com/onegov/onegov-cloud/commit/042ef0f2587811300bdb7389ea574c917ac5bb27)

## 2025.65

`2025-11-16` | [cb11e65b71...a53b5d5f13](https://github.com/OneGov/onegov-cloud/compare/cb11e65b71^...a53b5d5f13)

### Town

##### Fix file details not shown

`Bugfix` | [OGC-2784](https://linear.app/onegovcloud/issue/OGC-2784) | [1bf4dda93d](https://github.com/onegov/onegov-cloud/commit/1bf4dda93d8bb51a69b8b5dd3501a3332c6e2ad9)

### Town6

##### Fixes footer contact and opening hours label for feriennet

`Bugfix` | [OGC-2424](https://linear.app/onegovcloud/issue/OGC-2424) | [0acc673b40](https://github.com/onegov/onegov-cloud/commit/0acc673b40084bd897acd5b2d5d15657c5260d9a)

## 2025.64

`2025-11-13` | [12f9839782...af0f368d08](https://github.com/OneGov/onegov-cloud/compare/12f9839782^...af0f368d08)

### Assembly

##### Add print icons

`Feature` | [OGC-2711](https://linear.app/onegovcloud/issue/OGC-2711) | [e39e916367](https://github.com/onegov/onegov-cloud/commit/e39e91636775b844eee510ea495412e5dcb07b7b)

### Feriennet

##### Volunteer activities

Only show activities needing more volunteers

`Feature` | [OGC-1417](https://linear.app/onegovcloud/issue/OGC-1417) | [d65cc9be8b](https://github.com/onegov/onegov-cloud/commit/d65cc9be8bfc29ae557f7c1e0fccc59c8069746a)

### Landsgemeinde

##### Links in Sidebar for assembly items

`Feature` | [OGC-2714](https://linear.app/onegovcloud/issue/OGC-2714) | [ab1f6d31f6](https://github.com/onegov/onegov-cloud/commit/ab1f6d31f6cfa14139d553f0f6f2015e227f2ca9)

### Org

##### More specific error message

`Feature` | [OGC-2722](https://linear.app/onegovcloud/issue/OGC-2722) | [12f9839782](https://github.com/onegov/onegov-cloud/commit/12f98397820d5f5d81eb55b2865d2fd264178fbd)

##### Link ticket instead of reservation

`Bugfix` | [OGC-2779](https://linear.app/onegovcloud/issue/OGC-2779) | [90f21c0159](https://github.com/onegov/onegov-cloud/commit/90f21c015946526a5b833449c736cf1c7fa716c2)

### Pas

##### Prevents a bug in user synchronization with admins.

Admins can add themselves to commissions for testing purposes.
This would result in them having their account permissions
downgraded to parliamentarian or president, if we didn't add this.

`Bugfix` | [OGC-2783](https://linear.app/onegovcloud/issue/OGC-2783) | [8a97c24954](https://github.com/onegov/onegov-cloud/commit/8a97c24954e7acc4e66602e73c8d2ccb6d53c12f)

### Town6

##### Makes link label for contact information and opening hours configurable

The footer settings allow to configure the link labels

`Feature` | [OGC-2424](https://linear.app/onegovcloud/issue/OGC-2424) | [4f303b0cdc](https://github.com/onegov/onegov-cloud/commit/4f303b0cdcdd5111b7c16385936fae308d0c2d11)

## 2025.63

`2025-11-10` | [6a3efb41f9...bf9c16100d](https://github.com/OneGov/onegov-cloud/compare/6a3efb41f9^...bf9c16100d)

## 2025.62

`2025-11-07` | [d90bbc51b7...c296944343](https://github.com/OneGov/onegov-cloud/compare/d90bbc51b7^...c296944343)

### Core

##### Clears browser cache on user logout

This provides a small extra layer of protection, in case any sensitive
content accidentally ended up in the browser's cache.

`Feature` | [OGC-2745](https://linear.app/onegovcloud/issue/OGC-2745) | [93be9cbff0](https://github.com/onegov/onegov-cloud/commit/93be9cbff0a4f72cf0399a358fbb7b47982575a4)

### Feriennet

##### Display wishphase if it's not in the past

`Bugfix` | [OGC-1444](https://linear.app/onegovcloud/issue/OGC-1444) | [ff53601345](https://github.com/onegov/onegov-cloud/commit/ff536013458acfad310e10d511d935c3f98c97dc)

### Landsgemeinde

##### Additional Documents for assembly

`Feature` | [OGC-2699](https://linear.app/onegovcloud/issue/OGC-2699) | [0f94d3a43a](https://github.com/onegov/onegov-cloud/commit/0f94d3a43afb228ef5b41ed8cda5264e7fb6a734)

##### Assembly item creation Bugfix

`Bugfix` | [OGC-2696](https://linear.app/onegovcloud/issue/OGC-2696) | [8b5bfd1595](https://github.com/onegov/onegov-cloud/commit/8b5bfd15954a3d55511747be9cbcc678ea5d240d)

### Org

##### Lowers refresh interval for resource iCal to 30 minutes

`Feature` | [OGC-2548](https://linear.app/onegovcloud/issue/OGC-2548) | [d90bbc51b7](https://github.com/onegov/onegov-cloud/commit/d90bbc51b7be17b447275cfd9147a2fa379aa971)

##### Adds another ticket PDF option which includes related tickets

`Feature` | [OGC-2708](https://linear.app/onegovcloud/issue/OGC-2708) | [1609c54ef6](https://github.com/onegov/onegov-cloud/commit/1609c54ef6c684c3d3cbf277f372850d6453efdc)

##### Add subsubsubtitle and h5

`Feature` | [bdc5e9b5de](https://github.com/onegov/onegov-cloud/commit/bdc5e9b5de017f305b36bb80cab70e79a264e99a)

##### Newsletter just show lead

Add option to just show the lead text of the news items in the newsletters.

`Feature` | [OGC-2343](https://linear.app/onegovcloud/issue/OGC-2343) | [ffba57f239](https://github.com/onegov/onegov-cloud/commit/ffba57f2399fdd6ffe8cc9d54ae9d94597ea0679)

##### Content Sidepanel

Option to define how many levels are displayed in the TOC-Sidepanel.

`Feature` | [OGC-2715](https://linear.app/onegovcloud/issue/OGC-2715) | [698fb15f40](https://github.com/onegov/onegov-cloud/commit/698fb15f405b5e04003c93ab9d51e1a6e05b208b)

##### Rename dashboard to overview

`Feature` | [OGC-2728](https://linear.app/onegovcloud/issue/OGC-2728) | [348e70a641](https://github.com/onegov/onegov-cloud/commit/348e70a641b744a3f9090497c1a873d93baff6e3)

##### Attaches reservations summary PDF to reservation acceptance mail

`Feature` | [OGC-2765](https://linear.app/onegovcloud/issue/OGC-2765) | [5d75b5d66b](https://github.com/onegov/onegov-cloud/commit/5d75b5d66be40defac0e5632516600d30dea8b4a)

##### Fixes reservation dates not being linked for migrated invoices

`Bugfix` | [OGC-2767](https://linear.app/onegovcloud/issue/OGC-2767) | [0d9d4c8ee2](https://github.com/onegov/onegov-cloud/commit/0d9d4c8ee2b68fd074acafd2d6c3750b99c057fa)

### Pas

##### Adds cronjob to sync parliamentarians and `User` accounts.

`Feature` | [OGC-2725](https://linear.app/onegovcloud/issue/OGC-2725) | [38ef00156a](https://github.com/onegov/onegov-cloud/commit/38ef00156a2734a2f3b9559f08f4b40bc38469a5)

### Ris

##### Properly handle interest ties for new parliamentarians

`Feature` | [OGC-2766](https://linear.app/onegovcloud/issue/OGC-2766) | [f5b2b91246](https://github.com/onegov/onegov-cloud/commit/f5b2b912462299ac037fbe7a5926d717a8ec5b25)

##### Cleanup unused relationships

They got replaced with relationships to meeting items

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [d2f1272a27](https://github.com/onegov/onegov-cloud/commit/d2f1272a27a23963b2724c12cda7b17ded5706c2)

### Town6

##### Adds unit tests for political businesses views

`Feature` | [OGC-2481](https://linear.app/onegovcloud/issue/OGC-2481) | [5471bbd824](https://github.com/onegov/onegov-cloud/commit/5471bbd8248f71f568ef0e769353e0543655ea4c)

##### Adds unit tests for parliamentarian views including parliamentary group and commission

`Feature` | [OGC-2381](https://linear.app/onegovcloud/issue/OGC-2381) | [fce241c9be](https://github.com/onegov/onegov-cloud/commit/fce241c9bef6d43496d20c6f176851f657366e73)

##### Prefer `reply_to` in template over general email.

`Feature` | [OGC-2671](https://linear.app/onegovcloud/issue/OGC-2671) | [4637af1a54](https://github.com/onegov/onegov-cloud/commit/4637af1a540e574e93597f1b0de4cb52def750bf)

### User

##### Adds validation against a list of commonly used passwords

`Feature` | [OGC-2737](https://linear.app/onegovcloud/issue/OGC-2737) | [a048ece0af](https://github.com/onegov/onegov-cloud/commit/a048ece0afad0cffeb90d246c6a33c9733361e75)

## 2025.61

`2025-11-03` | [93a5f5203e...c79c709d87](https://github.com/OneGov/onegov-cloud/compare/93a5f5203e^...c79c709d87)

### Feriennet

##### Update banners.

`Feature` | [PRO-1437](https://linear.app/projuventute/issue/PRO-1437) | [ec5e2ff043](https://github.com/onegov/onegov-cloud/commit/ec5e2ff043644e0577e03e764e3c3c5dec59c03e)

### File

##### Adds `X-Content-Type-Options: nosniff` header to uploaded files

`Feature` | [OGC-2750](https://linear.app/onegovcloud/issue/OGC-2750) | [44b9456cba](https://github.com/onegov/onegov-cloud/commit/44b9456cbac23dc726941fcaf1c13485f238acf7)

##### Switches to `Content-Disposition: attachment` for most uploads

There's only really a small list of content types we want to serve
inline, such as images, videos and PDF files, we continue to serve
them inline and serve everything else as attachments.

`Bugfix` | [OGC-2733](https://linear.app/onegovcloud/issue/OGC-2733) | [8eb56af3c1](https://github.com/onegov/onegov-cloud/commit/8eb56af3c1b2642a30a499dd04ecf27bae752960)

### Org

##### Adds a my reservations PDF to the ticket list for RSV tickets

`Feature` | [OGC-2756](https://linear.app/onegovcloud/issue/OGC-2756) | [5ac8e0bd32](https://github.com/onegov/onegov-cloud/commit/5ac8e0bd323f51be7e3a970472562d9ce2fb8a7e)

##### Invalidates related TANs after authentication

This also decreases the validity period of mTANs used as a second factor

`Bugfix` | [OGC-2749](https://linear.app/onegovcloud/issue/OGC-2749) | [bb3782adb9](https://github.com/onegov/onegov-cloud/commit/bb3782adb99a2af293213e2cc1ebc7e5a32e710c)

##### Fixes crash in `file-links` template macro

`Bugfix` | [54e794bac3](https://github.com/onegov/onegov-cloud/commit/54e794bac36555d9adc1ba36e971a814984f2b06)

##### Uses a more sensible column as the `fts_id` for `ExternalLink`

`Bugfix` | [e7210a3096](https://github.com/onegov/onegov-cloud/commit/e7210a309647df9fade4e4ea8269b27b7befb2af)

##### Fixes invisible partitions in reservation calendar

`Bugfix` | [OGC-2764](https://linear.app/onegovcloud/issue/OGC-2764) | [c07ac95a1d](https://github.com/onegov/onegov-cloud/commit/c07ac95a1ddfb6a2eaa1be97a79bcbdde362635f)

### Search

##### Integrates indexer into transaction workflow with a data manager

This also refactors some code that relied on the old indexer behavior

`Feature` | [OGC-2759](https://linear.app/onegovcloud/issue/OGC-2759) | [24b68fba31](https://github.com/onegov/onegov-cloud/commit/24b68fba316962aa50edfb6870599eaa48efa6e4)

### Town6

##### Fixes empty links still rendered due to `populate_obj`.

`Bugfix` | [OGC-2761](https://linear.app/onegovcloud/issue/OGC-2761) | [835976629e](https://github.com/onegov/onegov-cloud/commit/835976629e8bebedf5fb67493e164e1b6b306a1c)

### User

##### Raises minimum password length from 8 to 10

`Feature` | [OGC-2736](https://linear.app/onegovcloud/issue/OGC-2736) | [2948b7da2e](https://github.com/onegov/onegov-cloud/commit/2948b7da2eb63a367f541cd38dd075f83e6d535d)

## 2025.60

`2025-10-24` | [7136036d60...4b63568190](https://github.com/OneGov/onegov-cloud/compare/7136036d60^...4b63568190)

### Search

##### Only processes indexer queue on the main thread

`Bugfix` | [7136036d60](https://github.com/onegov/onegov-cloud/commit/7136036d60d622f20ab80d98d309bc81481d45e3)

## 2025.59

`2025-10-24` | [bcafc9a898...ca05b98a32](https://github.com/OneGov/onegov-cloud/compare/bcafc9a898^...ca05b98a32)

### Search

##### Avoids potentially leaking connections within the indexer

`Bugfix` | [bcafc9a898](https://github.com/onegov/onegov-cloud/commit/bcafc9a89878970d7a6f4c173081ee0702a763b2)

##### Also disposes the indexer engine at the end just to be sure.

`Bugfix` | [98bce20025](https://github.com/onegov/onegov-cloud/commit/98bce200258276f06ad7068d33c1c16fedb7648c)

## 2025.58

`2025-10-24` | [3a7d6284d7...bca98ed899](https://github.com/OneGov/onegov-cloud/compare/3a7d6284d7^...bca98ed899)

## 2025.57

`2025-10-24` | [a92f06950b...d1e1b4df2c](https://github.com/OneGov/onegov-cloud/compare/a92f06950b^...d1e1b4df2c)

### Core

##### Changes default for `email_validator.CHECK_DELIVERABILITY`

We both use this validator directly and indirectly through WTForms.
However WTForms uses its own defaults for `check_deliverability` which
is different from `email_validator.CHECK_DELIVERABILITY`. This change
harmonizes the two defaults and avoids unnecessary I/O overhead.

`Bugfix` | [OGC-2494](https://linear.app/onegovcloud/issue/OGC-2494) | [91f31d08fb](https://github.com/onegov/onegov-cloud/commit/91f31d08fb4e5aeadeb428b64883dc38cb49f238)

### Landsgemeinde

##### Fix InDesign Import

`Bugfix` | [OGC-2683](https://linear.app/onegovcloud/issue/OGC-2683) | [ff0f061aaf](https://github.com/onegov/onegov-cloud/commit/ff0f061aafd591e035c559881efe966e7b4a8bdf)

##### Improves search results and suggestions

`Bugfix` | [OGC-2695](https://linear.app/onegovcloud/issue/OGC-2695) | [6bb53b3ee3](https://github.com/onegov/onegov-cloud/commit/6bb53b3ee310aff30dea160f6bcfac09031925e6)

##### Add content-sidebar for assembly items

`Bugfix` | [OGC-2698](https://linear.app/onegovcloud/issue/OGC-2698) | [87a1e60828](https://github.com/onegov/onegov-cloud/commit/87a1e608282e5177daced0611764765b100e00fb)

### Org

##### Increases batch size for invoice and ticket paginations

`Feature` | [OGC-2687](https://linear.app/onegovcloud/issue/OGC-2687) | [89218d1ad8](https://github.com/onegov/onegov-cloud/commit/89218d1ad8f8a9cef626d87f20820aadad942fc7)

##### Allows multiple ticket categories for filtering invoices/payments

`Feature` | [OGC-2703](https://linear.app/onegovcloud/issue/OGC-2703) | [bcc780577b](https://github.com/onegov/onegov-cloud/commit/bcc780577be5e40062a8b87df41ae32ff28ff03b)

##### Only considers last reservation in date filter in payments/invoices

This allows a cleaner separation of invoicing periods, since every
invoice / payment will have one reference date, instead of a range which
could partially overlap and cause it to show up in multiple periods.

`Feature` | [OGC-2704](https://linear.app/onegovcloud/issue/OGC-2704) | [b68c68c85c](https://github.com/onegov/onegov-cloud/commit/b68c68c85c0afdd1ab37e8a756821f9bb78fc95a)

##### Change internal link to use a searchable dropdown in editor.

`Feature` | [OGC-2351](https://linear.app/onegovcloud/issue/OGC-2351) | [58ef8b671b](https://github.com/onegov/onegov-cloud/commit/58ef8b671ba1a9c9e8c531317aa4c79ee915b611)

##### Displays selected filters in ticket invoice pdf export

`Feature` | [OGC-2702](https://linear.app/onegovcloud/issue/OGC-2702) | [648f6d15ba](https://github.com/onegov/onegov-cloud/commit/648f6d15ba3496138a55fa03d7f74b3665bda885)

##### Adds a filter for invoices with positive net amounts

`Feature` | [OGC-2701](https://linear.app/onegovcloud/issue/OGC-2701) | [3ed6d5c5fb](https://github.com/onegov/onegov-cloud/commit/3ed6d5c5fb0eeea2a5331633729f81ed274cf9a2)

##### Removes some of the now redundant payment list functionality

This functionality should be better served by the invoice list

`Feature` | [OGC-2705](https://linear.app/onegovcloud/issue/OGC-2705) | [bc9461cc57](https://github.com/onegov/onegov-cloud/commit/bc9461cc57c7253beef5d2e5c2ea98708a6673da)

##### Shows related tickets that were created as part of the same order

`Feature` | [OGC-2691](https://linear.app/onegovcloud/issue/OGC-2691) | [29e9a1c295](https://github.com/onegov/onegov-cloud/commit/29e9a1c2958cf5fa1f9b93604771a77d989a118c)

##### Increases visible date range for resource iCal

`Feature` | [OGC-2710](https://linear.app/onegovcloud/issue/OGC-2710) | [bd4a7865ee](https://github.com/onegov/onegov-cloud/commit/bd4a7865ee589065f679500e7eb06ca0f264cba3)

##### Adds a PDF export to my reservations with customizable date range

`Feature` | [OGC-2157](https://linear.app/onegovcloud/issue/OGC-2157) | [1b8001843d](https://github.com/onegov/onegov-cloud/commit/1b8001843dc92cadcf6a928ac57f2cc5f4337cd4)

##### Option to hide submitter email

`Feature` | [OGC-2654](https://linear.app/onegovcloud/issue/OGC-2654) | [a490f6c9c5](https://github.com/onegov/onegov-cloud/commit/a490f6c9c515604ca73f533792909f51a1f259f7)

##### Avoids sending empty daily newsletters

`Bugfix` | [OGC-2706](https://linear.app/onegovcloud/issue/OGC-2706) | [72aa08883f](https://github.com/onegov/onegov-cloud/commit/72aa08883f4a695e252943486f4fedfb66f0564c)

### Pas

##### Adds option in cli to sync just one user account.

`Feature` | [d498e1f823](https://github.com/onegov/onegov-cloud/commit/d498e1f823228037957130b35ca846be7123dda9)

##### Fixes translation.

`Bugfix` | [aa378ebfc0](https://github.com/onegov/onegov-cloud/commit/aa378ebfc0278b721b2bcd9564a0258fdb84a9f7)

##### Fixes issue where parliamentarian choices were not limited.

`Bugfix` | [eeb492a63f](https://github.com/onegov/onegov-cloud/commit/eeb492a63fc68d773c77919d181638833292f2e9)

##### Log 404 errors as warnings instead of errors in Kub api.

In sync, test users legitimately hit 404 response, triggering
Sentry alerts — these shouldn't be treated as errors requiring
investigation.

`Bugfix` | [96db52c8f5](https://github.com/onegov/onegov-cloud/commit/96db52c8f5bd7546b247d47bca0553c7b0060b94)

##### Log API check failures as warnings instead of errors

When the KUB API is temporarily unavailable during cronjob imports,
the API accessibility check raises RuntimeError, triggering Sentry
alerts

Builds on 96db52c8 which handled 404 errors for individual records.

`Bugfix` | [9ee85b6542](https://github.com/onegov/onegov-cloud/commit/9ee85b6542379cda7239a56784586cae9001d327)

### Search

##### Removes ElasticSearch integration

`Feature` | [OGC-1017](https://linear.app/onegovcloud/issue/OGC-1017) | [1f53cc147d](https://github.com/onegov/onegov-cloud/commit/1f53cc147d8ac35408d1580c8c825241724559eb)

##### Makes upgrade task more robust

`Bugfix` | [20bf43aeb7](https://github.com/onegov/onegov-cloud/commit/20bf43aeb7b7bf96adb3636ceecdfce25d3d6313)

### Ticket

##### Be a bit more robust in upgrade task.

This is a classic upgrade task ordering problem where
the ORM model has been updated but the database schema
hasn't been migrated yet. Only happened locally:

`sqlalchemy.exc.ProgrammingError:
(psycopg2.errors.UndefinedColumn) column tickets.closed_on
does not exist`

`Other` | [f8955ffa68](https://github.com/onegov/onegov-cloud/commit/f8955ffa68901cb150624cf24bcac858292211f0)

### Town6

##### Automatically subscribe new parliamentarians to newsletters

`Feature` | [OGC-2621](https://linear.app/onegovcloud/issue/OGC-2621) | [f82516e3f9](https://github.com/onegov/onegov-cloud/commit/f82516e3f9adb484388ec2c33ccb240a949cd306)

##### Lead text for iFrames

`Feature` | [OGC-2367](https://linear.app/onegovcloud/issue/OGC-2367) | [2c32002bfc](https://github.com/onegov/onegov-cloud/commit/2c32002bfc009fc56b9407bbeef5cad00376bcc2)

##### Custom text above footer for Form mails

`Feature` | [OGC-2467](https://linear.app/onegovcloud/issue/OGC-2467) | [e6a9cc4f24](https://github.com/onegov/onegov-cloud/commit/e6a9cc4f245ab73db00703bc713b19d01929dc3c)

##### Reservation Quota

`Bugfix` | [OGC-2681](https://linear.app/onegovcloud/issue/OGC-2681) | [a92f06950b](https://github.com/onegov/onegov-cloud/commit/a92f06950bcb8d9e12ba93d993a3c8378508ec48)

##### Only show dropdown if there is any public resource

`Bugfix` | [OGC-2680](https://linear.app/onegovcloud/issue/OGC-2680) | [15d32ef710](https://github.com/onegov/onegov-cloud/commit/15d32ef71049fa67be063a43a6ad672611309574)

##### Avoids including non-public directory entries in API

`Bugfix` | [OGC-2723](https://linear.app/onegovcloud/issue/OGC-2723) | [a4e9e415c1](https://github.com/onegov/onegov-cloud/commit/a4e9e415c13f5ff9ec21732596d3889286f0ca6d)

## 2025.56

`2025-10-08` | [613f9d83db...461edfdff1](https://github.com/OneGov/onegov-cloud/compare/613f9d83db^...461edfdff1)

### Gazette

##### Deletes `onegov.gazette` and `onegov.notice`

Gazette has been decommissioned, so these packages are no longer needed

`Feature` | [OGC-2678](https://linear.app/onegovcloud/issue/OGC-2678) | [2bbc479c71](https://github.com/onegov/onegov-cloud/commit/2bbc479c71bddf08aaf4f71e7d835c7f1c3ae487)

### Landsgemeinde

##### Political Business Styling

`Feature` | [OGC-2471](https://linear.app/onegovcloud/issue/OGC-2471) | [8204b85ef2](https://github.com/onegov/onegov-cloud/commit/8204b85ef2def53ddfdf431b0376c1c9ec7f520a)

##### Assembly name

`Bugfix` | [OGC-2674](https://linear.app/onegovcloud/issue/OGC-2674) | [ed7ebd0174](https://github.com/onegov/onegov-cloud/commit/ed7ebd0174086870c83eb629e4a6991b0682a90e)

### Org

##### Automatically complete incomplete URLs for Events

`Feature` | [OGC-2622](https://linear.app/onegovcloud/issue/OGC-2622) | [869fc78799](https://github.com/onegov/onegov-cloud/commit/869fc787991fa72f0484445aa4215babc4b77d07)

### Pas

##### Minor fixes.

`Bugfix` | [d744470a3a](https://github.com/onegov/onegov-cloud/commit/d744470a3a30860ee9fde5b6ec6b74a4c6f15742)

##### Minor fixes and refactoring.

Fixes a bug where default argument `import_type` (fallback
value) would be incorrectly applied.

`Bugfix` | [2bb86fe8d4](https://github.com/onegov/onegov-cloud/commit/2bb86fe8d48cef343438ee8db3f56665e3b49c0d)

### Pay

##### Upgrades to Stripe v13.0.0

`Feature` | [OGC-2658](https://linear.app/onegovcloud/issue/OGC-2658) | [2f4594a845](https://github.com/onegov/onegov-cloud/commit/2f4594a845912a461ddeb474dbc2cd4a8df2403b)

### Pdf

##### Removes lxml version pin

`Feature` | [OGC-2363](https://linear.app/onegovcloud/issue/OGC-2363) | [bb0d23ad7f](https://github.com/onegov/onegov-cloud/commit/bb0d23ad7fa62968b3f4f4dd5490829ec23e7a28)

### Search

##### Improves relevancy of search results in Postgres search

`Feature` | [OGC-1161](https://linear.app/onegovcloud/issue/OGC-1161) | [24c88cc69b](https://github.com/onegov/onegov-cloud/commit/24c88cc69bb51d0452259ec5e723fc847f18474a)

##### Fixes broken tests due to improper SQLAlchemy metadata isolation

`Bugfix` | [6950a3f9b0](https://github.com/onegov/onegov-cloud/commit/6950a3f9b0c89ffe039c45f036f7b83199cfea5d)

##### Improves result loading of Postgres search results

`Performance` | [OGC-508](https://linear.app/onegovcloud/issue/OGC-508) | [613f9d83db](https://github.com/onegov/onegov-cloud/commit/613f9d83dbafe81d09a310807fe837bd0b20a720)

### Town6

##### Add edit note as a format option

`Feature` | [OGC-2274](https://linear.app/onegovcloud/issue/OGC-2274) | [d9276e56ef](https://github.com/onegov/onegov-cloud/commit/d9276e56ef5969e1d4cf38ec35f570424ed732c4)

##### Option for custom daily newsletter name

`Feature` | [OGC-2344](https://linear.app/onegovcloud/issue/OGC-2344) | [71e0027835](https://github.com/onegov/onegov-cloud/commit/71e0027835a8c133db5b9ea5aa15cb113d44b22f)

##### Integration for external Chat links

`Feature` | [OGC-2470](https://linear.app/onegovcloud/issue/OGC-2470) | [a460e8939d](https://github.com/onegov/onegov-cloud/commit/a460e8939d176ee44455b9f75f32da5aa41baf01)

##### Fix order of political businesses

`Bugfix` | [OGC-2657](https://linear.app/onegovcloud/issue/OGC-2657) | [9390dcac1e](https://github.com/onegov/onegov-cloud/commit/9390dcac1ebe3faef3848341fa5be229780ec1c6)

##### Fix Typo

`Bugfix` | [OGC-2673](https://linear.app/onegovcloud/issue/OGC-2673) | [2d7b6c670c](https://github.com/onegov/onegov-cloud/commit/2d7b6c670cef0defc146454352c3f958576d2f8c)

##### Fix not being able to make reservation

`Bugfix` | [OGC-2681](https://linear.app/onegovcloud/issue/OGC-2681) | [9068a7980c](https://github.com/onegov/onegov-cloud/commit/9068a7980cb53197495d5dd211313d98be2ac905)

## 2025.55

`2025-09-30` | [3a7211c7b1...0c1abb0734](https://github.com/OneGov/onegov-cloud/compare/3a7211c7b1^...0c1abb0734)

### Api

##### Add Directories to API endpoints

`Feature` | [OGC-2628](https://linear.app/onegovcloud/issue/OGC-2628) | [3acba4b816](https://github.com/onegov/onegov-cloud/commit/3acba4b81657ace78851185eeedc82eb2fe6833b)

### Landsgemeinde

##### Add assembly redirect

`Feature` | [735e0caaa3](https://github.com/onegov/onegov-cloud/commit/735e0caaa3a9c26112e71f6554547d4ac8c0868e)

### Town6

##### Tag translation

No automatic translation for custom tags

`Bugfix` | [OGC-2646](https://linear.app/onegovcloud/issue/OGC-2646) | [87b7579b78](https://github.com/onegov/onegov-cloud/commit/87b7579b78461abd9a18faea6a0d9d6451d869ff)

## 2025.54

`2025-09-30` | [71f05ef6f4...c64c9d7060](https://github.com/OneGov/onegov-cloud/compare/71f05ef6f4^...c64c9d7060)

## 2025.53

`2025-09-30` | [bfc3672deb...34dd4cdab5](https://github.com/OneGov/onegov-cloud/compare/bfc3672deb^...34dd4cdab5)

### Pas

##### Adds custom user management and minor fixes.

`Feature` | [8166891e79](https://github.com/onegov/onegov-cloud/commit/8166891e79beea53a496a6a91c860b385312a26b)

## 2025.52

`2025-09-26` | [9548576332...dbe3704f11](https://github.com/OneGov/onegov-cloud/compare/9548576332^...dbe3704f11)

### Landsgemeinde

##### Import assembly as zip file

`Feature` | [OGC-2272](https://linear.app/onegovcloud/issue/OGC-2272) | [26390a491f](https://github.com/onegov/onegov-cloud/commit/26390a491fff68634612e364a7f3cbc4e7400c5c)

### Org

##### Adds invoicing parties and cost objects to invoices

`Feature` | [OGC-2643](https://linear.app/onegovcloud/issue/OGC-2643) | [392e16754b](https://github.com/onegov/onegov-cloud/commit/392e16754be0c5010bf127e654a9485c1f02cc29)

##### Fixes crash when an expired transient reservation contains files

`Bugfix` | [OGC-2645](https://linear.app/onegovcloud/issue/OGC-2645) | [9548576332](https://github.com/onegov/onegov-cloud/commit/9548576332d26e560807b37d65585898676e4103)

##### Avoids crashes in `parse_fullcalendar_request` for invalid dates

Instead we raise `HTTPBadRequest` which returns a 400 response

`Bugfix` | [SEA-1855](https://linear.app/seantis/issue/SEA-1855) | [21487f788e](https://github.com/onegov/onegov-cloud/commit/21487f788eaa392ad83263cbdaba8a6eb23857bf)

### Pas

##### Improve log overview with client side filtering, simplify.

`Feature` | [5addd8e640](https://github.com/onegov/onegov-cloud/commit/5addd8e640b298ed0e17744cf236afcd1ca4daa7)

##### Add permission system and user accounts for parliamentarians.

This is similar to 4f8e72cda44115127614b6184b35af45f5f53e06.

`Feature` | [OGC-2573](https://linear.app/onegovcloud/issue/OGC-2573) | [da76354d61](https://github.com/onegov/onegov-cloud/commit/da76354d61e778c70d3be841ac793c4a3a34025d)

##### Create ability to close settlement run.

`Feature` | [OGC-2586](https://linear.app/onegovcloud/issue/OGC-2586) | [a688f56b33](https://github.com/onegov/onegov-cloud/commit/a688f56b335fe13374808749fcf684e93f3adc48)

##### Fixes `KeyError` in `/import_logs` download

`Bugfix` | [OGC-2652](https://linear.app/onegovcloud/issue/OGC-2652) | [030cbbea8a](https://github.com/onegov/onegov-cloud/commit/030cbbea8a3ec157007d801af584ec29bb6ced98)

##### Fixes a couple of minor issues.

`Bugfix` | [fee7408fcf](https://github.com/onegov/onegov-cloud/commit/fee7408fcf487e7579a8d20b401328e39d29b171)

## 2025.51

`2025-09-23` | [b9c65577c5...2315af674a](https://github.com/OneGov/onegov-cloud/compare/b9c65577c5^...2315af674a)

### Cronjob

##### Fix missing translation in daily newsletter

`Bugfix` | [OGC-2590](https://linear.app/onegovcloud/issue/OGC-2590) | [2c2f4b9485](https://github.com/onegov/onegov-cloud/commit/2c2f4b94855c90f180a9cf82d07fb58348162cd2)

### Landsgemeinde

##### Multiple Name Options

Add setting for different names for assemblies

`Feature` | [OGC-2265](https://linear.app/onegovcloud/issue/OGC-2265) | [c0be3d5bdc](https://github.com/onegov/onegov-cloud/commit/c0be3d5bdc2e3455aaf7981194999329ac4e6ebb)

### Org

##### Fixes resource iCal no longer filtering to the resource

`Bugfix` | [OGC-2640](https://linear.app/onegovcloud/issue/OGC-2640) | [35eee6e387](https://github.com/onegov/onegov-cloud/commit/35eee6e3875867844049d77913e52a8852d31514)

### Pas

##### Refactors the import and fixes some issues.

- Prepares the import to be easily usable in cronjob.
- Use strategy pattern for logging, we potentially want 
  to have better debugging ability and show some logging
  in a view, to see what was imported.
- Get address of parliamentarian by calling `/people/{id}`
  endpoint directly. This we need to do anyhow for `customFields`.

`Feature` | [OGC-2021](https://linear.app/onegovcloud/issue/OGC-2021) | [23bdba011d](https://github.com/onegov/onegov-cloud/commit/23bdba011d705fac16b0a1bc69806efb365916da)

##### Add cronjob for import plus manual trigger.

`Feature` | [OGC-2091](https://linear.app/onegovcloud/issue/OGC-2091) | [8056ea8204](https://github.com/onegov/onegov-cloud/commit/8056ea82046d36d1090ab7d23f41ea9877f928da)

##### Dynamic hostname replacement for pagination URLs.

Fix a pagination issue where Kub API returns URLs with
different hostnames than the one used for initial requests.
Now dynamically replaces hostname in 'next' URLs with
the correct bridge.

`Bugfix` | [OGC-2091](https://linear.app/onegovcloud/issue/OGC-2091) | [f04c0584bc](https://github.com/onegov/onegov-cloud/commit/f04c0584bcedf641f8fa63eb98ad6b610480a1e2)

##### Mark commission attendance complete for bulk as well.

`Bugfix` | [OGC-2585](https://linear.app/onegovcloud/issue/OGC-2585) | [a7047e1268](https://github.com/onegov/onegov-cloud/commit/a7047e1268f75fee6c5fc1177000883ff8f151f8)

##### Show JSON import source in overview

`Bugfix` | [a4b56c35c9](https://github.com/onegov/onegov-cloud/commit/a4b56c35c96e6b93599397746d5d252aaee5366c)

##### Speed up api calls and make some corrections.

- Warn for parliamentarians without external IDs
- Log warnings for parliamentarians that won't be synchronized

`Other` | [a96bc88bee](https://github.com/onegov/onegov-cloud/commit/a96bc88beeb09aa6edfa056a47f0044c37a74241)

### Pay

##### Adds cronjob to cancel stale Worldline Saferpay transactions

This only applies to new transactions initiated after this change.

`Bugfix` | [OGC-2609](https://linear.app/onegovcloud/issue/OGC-2609) | [b9c65577c5](https://github.com/onegov/onegov-cloud/commit/b9c65577c595499f30d17409a69bf8971211ea19)

### Resources

##### Adds general information to resource view and resource settings

`Feature` | [OGC-2632](https://linear.app/onegovcloud/issue/OGC-2632) | [3c99c6d901](https://github.com/onegov/onegov-cloud/commit/3c99c6d9017730e4aee1cfe7f07ff40fac378446)

### Town6

##### Style links

`Feature` | [OGC-2398](https://linear.app/onegovcloud/issue/OGC-2398) | [1bae607dda](https://github.com/onegov/onegov-cloud/commit/1bae607dda2f67fec5154e79afb77b8a54fe74ab)

##### Adds impressum link to footer

`Feature` | [OGC-2448](https://linear.app/onegovcloud/issue/OGC-2448) | [8354caed88](https://github.com/onegov/onegov-cloud/commit/8354caed887fff1db0511dda87f17ca862ca790c)

##### More-list styling

`Bugfix` | [d9677ce4a7](https://github.com/onegov/onegov-cloud/commit/d9677ce4a779140f09165d830a71aa078c722cd3)

## 2025.50

`2025-09-16` | [01fda37130...f31113771d](https://github.com/OneGov/onegov-cloud/compare/01fda37130^...f31113771d)

**Upgrade hints**
- onegov-org --select /onegov_town6/wil wil-event-tags-to-german-as-we-use-custom-event-tags
### Core

##### Fixes making ElasticSearch unavailable in all CLI commands

This adds a new context specific setting `skip_es_client` which allows
skipping initializing ElasticSearch for commands that don't need it.

`Bugfix` | [2b4c28235d](https://github.com/onegov/onegov-cloud/commit/2b4c28235da9c3ec60a69df5f652108bda08ad77)

### Org

##### Xlsxwriter to specify worksheet title on creation call, fixes mypy issues

`Feature` | [NONE](#NONE) | [3a63298f53](https://github.com/onegov/onegov-cloud/commit/3a63298f5327248a639e4855d3158a0696519257)

### Pas

##### Resolve PDF download failures from invalid filenames.

Chromium Content-Disposition header broke
on filenames with commas.

`Feature` | [OGC-2620](https://linear.app/onegovcloud/issue/OGC-2620) | [74b5f88ba3](https://github.com/onegov/onegov-cloud/commit/74b5f88ba3821f21e86316c1cf44bdbd8422c89b)

##### Bidirectional sync of attendance choices.

`Feature` | [OGC-2607](https://linear.app/onegovcloud/issue/OGC-2607) | [0724604c9d](https://github.com/onegov/onegov-cloud/commit/0724604c9dfb60903a53578537e9346de367292f)

##### Adds the remaining three exports.

`Feature` | [OGC-1878](https://linear.app/onegovcloud/issue/OGC-1878) | [2be81c42f0](https://github.com/onegov/onegov-cloud/commit/2be81c42f09073f945ae98c00cf834a7384d6f79)

##### Add CLI for data import via API.

`Feature` | [OGC-2091](https://linear.app/onegovcloud/issue/OGC-2091) | [ef0df66086](https://github.com/onegov/onegov-cloud/commit/ef0df660868228481e65ef323033b8dd2f8619e3)

##### Allow parliamentarians to mark attendance complete per commission.

We're not closing commissions themselves. We're allowing
parliamentarians mark their attendance submission
as closed for a specific commission within a settlement run.

`Feature` | [OGC-2585](https://linear.app/onegovcloud/issue/OGC-2585) | [b5a72f0193](https://github.com/onegov/onegov-cloud/commit/b5a72f0193ff3ee55682688d7d1de488610907cc)

##### Fixes president query.

`Bugfix` | [OGC-2512](https://linear.app/onegovcloud/issue/OGC-2512) | [64a2d5d9b3](https://github.com/onegov/onegov-cloud/commit/64a2d5d9b3a7c388fe04c736551068c358b7c8bb)

### People

##### Fix yaml representation in text field

`Bugfix` | [NONE](#NONE) | [e4fc70350e](https://github.com/onegov/onegov-cloud/commit/e4fc70350e64ac7348ce9bfcba7c7794be5b735a)

### Ris

##### Switch back to round parliamentarian image

`Feature` | [OGC-2635](https://linear.app/onegovcloud/issue/OGC-2635) | [512498b575](https://github.com/onegov/onegov-cloud/commit/512498b57572aa2a6b3f9cfc94d222501b60515e)

### Wil

##### Event import: Switch to event categories from minasa and prevent duplicates in tag list

`Feature` | [OGC-2635](https://linear.app/onegovcloud/issue/OGC-2635) | [94c567a63a](https://github.com/onegov/onegov-cloud/commit/94c567a63af31d4354979df65dcbdb1e2ae11f9b)

## 2025.49

`2025-09-12` | [5231bc06ae...6aa4133c66](https://github.com/OneGov/onegov-cloud/compare/5231bc06ae^...6aa4133c66)

### Cronjob

##### Adds an offset of 2 days prior deletion of occurrences and events

Also removes the usage of future_occurrences that lead to early event deletions

`Feature` | [OGC-2562](https://linear.app/onegovcloud/issue/OGC-2562) | [871408b800](https://github.com/onegov/onegov-cloud/commit/871408b800246657b2beb6ba5f71e5a0d6c39c16)

### Org

##### Allows extra fields to be included in the iCal event description

`Feature` | [OGC-2592](https://linear.app/onegovcloud/issue/OGC-2592) | [5231bc06ae](https://github.com/onegov/onegov-cloud/commit/5231bc06ae2e72a84e1f5955984cf6dee2aebf8c)

##### Allows specifying a custom reservation confirmation text

This text will be included in reservation confirmation and summary
e-mails as well as on the ticket status page, after the reservation(s)
have been confirmed.

`Feature` | [OGC-2589](https://linear.app/onegovcloud/issue/OGC-2589) | [ea461c5724](https://github.com/onegov/onegov-cloud/commit/ea461c5724de7fa85b087e9fe47f6314c8092b63)

##### Adds customer message notifications to resource recipients

`Feature` | [OGC-2497](https://linear.app/onegovcloud/issue/OGC-2497) | [c15be87c26](https://github.com/onegov/onegov-cloud/commit/c15be87c26a6258136fc136d16a976ef0ee59ba3)

##### Adds an optional lead time to resources for public reservations

`Feature` | [OGC-2610](https://linear.app/onegovcloud/issue/OGC-2610) | [bc459fc602](https://github.com/onegov/onegov-cloud/commit/bc459fc602f57fab9b6d17d82bcb13a5eb82f730)

##### Includes more information in reservation notifications

`Feature` | [OGC-2588](https://linear.app/onegovcloud/issue/OGC-2588) | [7f088a0cbd](https://github.com/onegov/onegov-cloud/commit/7f088a0cbdc1f31f1710083340792cb03ef5ea97)

##### Allows changes to access in allocation rules to always propagate

Previously, if the existing allocation had one or more reservations, it
could not be deleted, so there was no new allocation with the new access
level for that date.

Now we allow existing future allocations to have their access modified.

`Feature` | [OGC-2629](https://linear.app/onegovcloud/issue/OGC-2629) | [ace3a5b84e](https://github.com/onegov/onegov-cloud/commit/ace3a5b84ecbefb3f907fd33208763202e2c6aab)

### Pas

##### Attendences edit and delete bulk edits.

`Feature` | [OGC-2594](https://linear.app/onegovcloud/issue/OGC-2594) | [81ec08f9a7](https://github.com/onegov/onegov-cloud/commit/81ec08f9a74986469e11bd7aa0f9f89c50dc4dab)

### Ris

##### Adds settings for predefined interest ties categories

`Feature` | [OGC-2507](https://linear.app/onegovcloud/issue/OGC-2507) | [1a384642b0](https://github.com/onegov/onegov-cloud/commit/1a384642b0b4b6736502abab38ac69053b8deb9d)

##### Remove unused type columns for RIS models

These models are only used in RIS not in PAS or elsewhere

`Feature` | [OGC-2445](https://linear.app/onegovcloud/issue/OGC-2445) | [8340cc5676](https://github.com/onegov/onegov-cloud/commit/8340cc5676d1314a0323e2a9e8e65941b7598149)

### Wil Event Import

##### Increase default event time to 2h

`Feature` | [OGC-2447](https://linear.app/onegovcloud/issue/OGC-2447) | [44533c7b5d](https://github.com/onegov/onegov-cloud/commit/44533c7b5d81297f71d3211bf08d36e9efa92a73)

## 2025.48

`2025-09-09` | [a9c8d96e8c...7cad8502c1](https://github.com/OneGov/onegov-cloud/compare/a9c8d96e8c^...7cad8502c1)

### Core

##### Ensures commands that create a new schema run `morepath.autoscan`

This way the SQLAlchemy table metadata is guaranteed to be complete
and matches what it looks like when we run the server.

`Bugfix` | [OGC-2583](https://linear.app/onegovcloud/issue/OGC-2583) | [91030ec372](https://github.com/onegov/onegov-cloud/commit/91030ec3725b6d4292b17b6eea75771374829afc)

### Landsgemeinde

##### Videoframes

Videoframes for videos in agenda-items

`Feature` | [OGC-2266](https://linear.app/onegovcloud/issue/OGC-2266) | [9c60344edf](https://github.com/onegov/onegov-cloud/commit/9c60344edf47900084edd4db964cee952cbaae51)

### Meeting

##### Adds unit tests for meeting views

`Feature` | [OGC-2381](https://linear.app/onegovcloud/issue/OGC-2381) | [c5d1dc0fbd](https://github.com/onegov/onegov-cloud/commit/c5d1dc0fbdee953ae2f2e6c10dce53bf00c402b3)

### Org

##### Adds a view for looking at all of the invoices

`Feature` | [OGC-2569](https://linear.app/onegovcloud/issue/OGC-2569) | [99d6e11c44](https://github.com/onegov/onegov-cloud/commit/99d6e11c44543f89baa11ca36850c6b4d1104ed3)

##### Adds a ticket category filter to invoices/payments

`Feature` | [OGC-2569](https://linear.app/onegovcloud/issue/OGC-2569) | [b801dfbd84](https://github.com/onegov/onegov-cloud/commit/b801dfbd849adc26d142e3bb087e4066e68dd47a)

##### Drops time portion from payment/invoice filter forms

`Feature` | [OGC-2598](https://linear.app/onegovcloud/issue/OGC-2598) | [b5dac86e24](https://github.com/onegov/onegov-cloud/commit/b5dac86e2459088abefcab9552a7a84ccedb705a)

##### Fix cronjob deletes unpublished events prior its end date

`Bugfix` | [OGC-2562](https://linear.app/onegovcloud/issue/OGC-2562) | [0e16554c3d](https://github.com/onegov/onegov-cloud/commit/0e16554c3db0377df29a2e9e4d6c3c9ccecef14c)

##### Makes the e-mail address for citizen login case-insensitive

Even though the local part can be treated case-sensitively by SMTP
servers, in reality no-one really does that. The host is also case-
insensitive. So treating the entire address as case-insensitive is
most pragmatic. Otherwise people will end up needing multiple logins
if their address has been spelled in multiple different ways.

`Bugfix` | [OGC-2601](https://linear.app/onegovcloud/issue/OGC-2601) | [d08bc704ad](https://github.com/onegov/onegov-cloud/commit/d08bc704ad50736f9948537eb867a696ef8ada50)

##### Fixes reservation errors sometimes not being displayed

For allocations that could be reserved with a single click, only the
first click would result in a visible error if it was not possible to
reserve the allocation.

`Bugfix` | [OGC-2578](https://linear.app/onegovcloud/issue/OGC-2578) | [352eb36dd7](https://github.com/onegov/onegov-cloud/commit/352eb36dd78d7402c9370de1d8cb240eca4ad591)

### Par

##### Fix inconsistencies in par and pas tables

`Bugfix` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [b391276802](https://github.com/onegov/onegov-cloud/commit/b391276802c06078b17f076a061cb1436cd0e4a6)

### Pas

##### Add attendences to settings.

`Feature` | [OGC-2605](https://linear.app/onegovcloud/issue/OGC-2605) | [1eda07e345](https://github.com/onegov/onegov-cloud/commit/1eda07e3453c54ebad00e674fe4473adf5b50587)

### Ris

##### Enable eager loading to reduce N + 1 query issues

`Feature` | [OGC-2595](https://linear.app/onegovcloud/issue/OGC-2595) | [a9c8d96e8c](https://github.com/onegov/onegov-cloud/commit/a9c8d96e8c1d9a99c54e76980f98a42cb353956f)

##### Remove all pas tables from db

`Feature` | [OGC-2604](https://linear.app/onegovcloud/issue/OGC-2604) | [1aaa9b7ea6](https://github.com/onegov/onegov-cloud/commit/1aaa9b7ea6e2b50251ec8e49648d98111f9a8a2e)

##### Create new meeting using form method

`Bugfix` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [46fa5e87ef](https://github.com/onegov/onegov-cloud/commit/46fa5e87efdcd3b8bd5ff23c6e54bbb2d463ce2d)

## 2025.47

`2025-09-04` | [acdb4252ef...e22d88493c](https://github.com/OneGov/onegov-cloud/compare/acdb4252ef^...e22d88493c)

### Org

##### Improves robustness of Kaba key revocation

Previously it was possible for a `KeyError` to be emitted, which would
have been caught by the views, since they do a `clients[site_id]`, even
though it definitely should not have been caught.

`Bugfix` | [OGC-2579](https://linear.app/onegovcloud/issue/OGC-2579) | [acdb4252ef](https://github.com/onegov/onegov-cloud/commit/acdb4252efccdbaab6351f2818a527a2fea5cffb)

### Pas

##### Adds default start date for commission.

`Feature` | [OGC-2591](https://linear.app/onegovcloud/issue/OGC-2591) | [20a477612e](https://github.com/onegov/onegov-cloud/commit/20a477612e4bb5b7f302e9479824c7e355036e1d)

### Town6

##### Table

Add scroll to tables wider than the content, remove margin from p in table

`Feature` | [OGC-2270](https://linear.app/onegovcloud/issue/OGC-2270) | [f5a9883bd0](https://github.com/onegov/onegov-cloud/commit/f5a9883bd0dc47a2e7ed0567e4070d9f64d01850)

##### Content-sidebar

Only show content sidebar if there are more than 2 subtitles

`Feature` | [1398ba2dd0](https://github.com/onegov/onegov-cloud/commit/1398ba2dd07d466d7b069392547befef62b342e0)

##### Agenda item files

File upload for additional files

`Feature` | [OGC-2269](https://linear.app/onegovcloud/issue/OGC-2269) | [850949b51c](https://github.com/onegov/onegov-cloud/commit/850949b51cd78b467d6eab82acc6431b25c631c5)

## 2025.46

`2025-09-02` | [c01adb76b6...57240da96f](https://github.com/OneGov/onegov-cloud/compare/c01adb76b6^...57240da96f)

**Upgrade hints**
- onegov-org --select /onegov_town6/wil ris-wil-meetings-fix-audio-links
### Pas

##### Bulk add commission attendances.

`Feature` | [OGC-2489](https://linear.app/onegovcloud/issue/OGC-2489) | [56a3fe9f49](https://github.com/onegov/onegov-cloud/commit/56a3fe9f49731e4a40f94aa2cd616a90793357de)

### Ris

##### Show audio and video links for meetings

`Feature` | [OGC-2522](https://linear.app/onegovcloud/issue/OGC-2522) | [c01adb76b6](https://github.com/onegov/onegov-cloud/commit/c01adb76b6336ff441bfa0621fd00ffb07ea671a)

##### Adds export view to meeting in order to download related meeting item documents

`Feature` | [OGC-2297](https://linear.app/onegovcloud/issue/OGC-2297) | [d2a37ed20f](https://github.com/onegov/onegov-cloud/commit/d2a37ed20f4732e4ec37f0a9a85b2f7c88ccab15)

### Town6

##### Fix more-list

`Feature` | [015b897a87](https://github.com/onegov/onegov-cloud/commit/015b897a87ca1986f20770c27c1b2ec153b34518)

##### List Corrections

`Feature` | [aaf293052b](https://github.com/onegov/onegov-cloud/commit/aaf293052bf8ea579dfc70970eb728d873af653c)

##### Anchor links

Add anchor links to headings in main content

`Feature` | [OGC-2267](https://linear.app/onegovcloud/issue/OGC-2267) | [e35d58b11f](https://github.com/onegov/onegov-cloud/commit/e35d58b11f2caff4ad33732dbd1e00cae98ae7de)

## 2025.45

`2025-09-01` | [313087dab3...6fc92791b8](https://github.com/OneGov/onegov-cloud/compare/313087dab3^...6fc92791b8)

**Upgrade hints**
- onegov-org --select /onegov_town6/wil ris-make-imported-files-general-file
### Pas

##### Remove Legislative, Add '/files' entry.

`Bugfix` | [OGC-2402](https://linear.app/onegovcloud/issue/OGC-2402) | [87ed8854c2](https://github.com/onegov/onegov-cloud/commit/87ed8854c2a0f2517a4935b915b8b79bff59b613)

### Ris

##### Make imported files from type general

`Feature` | [OGC-2550](https://linear.app/onegovcloud/issue/OGC-2550) | [313087dab3](https://github.com/onegov/onegov-cloud/commit/313087dab35246dcd0578997076d8ab47a11a294)

##### Don't show access field for meeting and political business

All RIS information is public

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [d2b375cc04](https://github.com/onegov/onegov-cloud/commit/d2b375cc0400f10effc8f3c2ae861bd89b44de0d)

##### Enhance layout for all views

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [b87bae8692](https://github.com/onegov/onegov-cloud/commit/b87bae86928666803a3fea2ff2f6da1d92dc05af)

### User

##### Fixes crash in `User.get_initials` related to dots in the username

`Bugfix` | [4163ae4783](https://github.com/onegov/onegov-cloud/commit/4163ae47838f5a252b333b89e59e00cad197d971)

## 2025.44

`2025-08-28` | [225a83e987...00c68baacd](https://github.com/OneGov/onegov-cloud/compare/225a83e987^...00c68baacd)

### Org

##### Displays invoice items in ticket PDF

`Feature` | [OGC-2563](https://linear.app/onegovcloud/issue/OGC-2563) | [857cd3e652](https://github.com/onegov/onegov-cloud/commit/857cd3e6529ac342dfc8a1caeb86502a7aff7979)

##### De-emphasizes allocations that are past the resource deadline (#2014)

Previously these could appear green and only yielded an error once you
tried to actually reserve them. Now they should appear gray. One can
still attempt to reserve those allocations, just like with past
allocations, but it should be less frustrating over all.

`Feature` | [OGC-2334](https://linear.app/onegovcloud/issue/OGC-2334) | [6d477c0577](https://github.com/onegov/onegov-cloud/commit/6d477c057769a2d58bb14b00e29ff154af24385f)

##### Adds view to add a new reservation to an existing ticket

`Feature` | [OGC-2571](https://linear.app/onegovcloud/issue/OGC-2571) | [cca0b68557](https://github.com/onegov/onegov-cloud/commit/cca0b68557b693c227488d664c4c09406aabb518)

##### Includes ticket url in iCal event description for compatibility

`Bugfix` | [OGC-2575](https://linear.app/onegovcloud/issue/OGC-2575) | [897c9f10c5](https://github.com/onegov/onegov-cloud/commit/897c9f10c5c75981caebfd9de7b98ed3ab7c0652)

##### Makes reservations acceptance view more robust

If for whatever reason the ticket managed to transition into a state
where only some of the reservations have been accepted, it was then
impossible to accept the remaining reservations, since the validation
only checks the state on the first reservation and assumes all
reservations share that state.

`Bugfix` | [OGC-2576](https://linear.app/onegovcloud/issue/OGC-2576) | [af4496b612](https://github.com/onegov/onegov-cloud/commit/af4496b61206e6bfa460a1bf48b4c66548be7c27)

### Pas

##### Fixes `InvalidRequestError`.

`Bugfix` | [353074d970](https://github.com/onegov/onegov-cloud/commit/353074d970e757841105ced645e7b52f7ad07eeb)

##### Fix N+1 query in /changes.

`Performance` | [OGC-2560](https://linear.app/onegovcloud/issue/OGC-2560) | [a905c060da](https://github.com/onegov/onegov-cloud/commit/a905c060da9be59b09035b7136e9d049a83e4166)

### Ris

##### Remove access extension as information is pubic

`Feature` | [OGC-2567](https://linear.app/onegovcloud/issue/OGC-2567) | [551476ef92](https://github.com/onegov/onegov-cloud/commit/551476ef92c724e360524559e4ea269951e34d4a)

### Town6

##### Align padding for menu group

`Feature` | [NONE](#NONE) | [56edafef0d](https://github.com/onegov/onegov-cloud/commit/56edafef0d647917dec5989f257ca69f7fc9522b)

## 2025.43

`2025-08-22` | [8642ecad1b...e0d7756edf](https://github.com/OneGov/onegov-cloud/compare/8642ecad1b^...e0d7756edf)

### Landsgemeinde

##### Add status "draft"

`Feature` | [OGC-2268](https://linear.app/onegovcloud/issue/OGC-2268) | [d418096d74](https://github.com/onegov/onegov-cloud/commit/d418096d749cfaf990cf8bbef03ef2615bbe972a)

### Org

##### Hides tickets that can't be processed from tickets list

Previously they were displayed, but couldn't be opened, because the
filter happened after the query, so completely hiding would've broken
pagination.

We now do our best to apply the filter as part of the query, so we get
a correct pagination, total number of results etc.

This also fixes a corner-case with non-exclusive ticket permissions on
a ticket group vs. exclusive ticket permissions on the handler code.

`Bugfix` | [OGC-2459](https://linear.app/onegovcloud/issue/OGC-2459) | [f83e80efbc](https://github.com/onegov/onegov-cloud/commit/f83e80efbcd92520acf68d7adbbb9af26095546d)

##### Fixes incomplete fix for corner case in ticket permissions

`Bugfix` | [cc6cb4a2aa](https://github.com/onegov/onegov-cloud/commit/cc6cb4a2aa1e244f05d00680f32c9e1761e00e32)

##### Avoids sending ticket notifications to users without permissions

Previously all new tickets lead to a unrestricted global broadcast, but
since ticket permissions can cause some users to only see a subset of
all the tickets, they should only receive broadcasts for those tickets.

`Bugfix` | [OGC-2554](https://linear.app/onegovcloud/issue/OGC-2554) | [18d3ba973e](https://github.com/onegov/onegov-cloud/commit/18d3ba973ea119fb86a7705440cace0e17127c51)

### Ris

##### Reorder menu actions to Edit, Delete, then Add

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [5249a732c4](https://github.com/onegov/onegov-cloud/commit/5249a732c45be35c888d66452a4c0cdc19bd64aa)

##### Show related meetings for political business

`Feature` | [OGC-2521](https://linear.app/onegovcloud/issue/OGC-2521) | [42cad7089f](https://github.com/onegov/onegov-cloud/commit/42cad7089f08faf9bf51b7c46448c23978e9c947)

##### Move menu to the top

Like elsewhere in town6

`Feature` | [OGC-2558](https://linear.app/onegovcloud/issue/OGC-2558) | [0f0d39b2b7](https://github.com/onegov/onegov-cloud/commit/0f0d39b2b717deee0fa805ce880508f2adf7d1f2)

##### Filtering for multiple parliamentarian attributes

`Feature` | [OGC-2509](https://linear.app/onegovcloud/issue/OGC-2509) | [cf4a5b2885](https://github.com/onegov/onegov-cloud/commit/cf4a5b288563a98fc9897b56532435ebbaa2fe57)

##### Handle empty status for political businesses

Older imported political businesses may have no status assigned

`Bugfix` | [OGC-2549](https://linear.app/onegovcloud/issue/OGC-2549) | [ac64ed1e03](https://github.com/onegov/onegov-cloud/commit/ac64ed1e03805211a9cdbc2b9ecba8a1bb12395f)

##### Fixes parliamentary group does not get processed when editing political business

`Bugfix` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [6a72477a71](https://github.com/onegov/onegov-cloud/commit/6a72477a71d11c315f0e09cab26d1dd7e98bfe91)

##### Meeting: Show political business type in any case

`Bugfix` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [38520a2863](https://github.com/onegov/onegov-cloud/commit/38520a2863647a0b51611b92715bdde6df7fde03)

##### Resolve issue when creating political business with files

As files cannot be handled in the collection add from get_useful_data moving to populate_obj approach

`Bugfix` | [OGC-2551](https://linear.app/onegovcloud/issue/OGC-2551) | [5b421e4b61](https://github.com/onegov/onegov-cloud/commit/5b421e4b611b8028f512e4683df5713a2db16de4)

##### Make meeting form more efficient

`Bugfix` | [OGC-2556](https://linear.app/onegovcloud/issue/OGC-2556) | [2ebf4885f8](https://github.com/onegov/onegov-cloud/commit/2ebf4885f86055b87e1f640dcab00f1e520a98a8)

## 2025.42

`2025-08-19` | [49b0111cab...1ca26203ca](https://github.com/OneGov/onegov-cloud/compare/49b0111cab^...1ca26203ca)

### Org

##### Verify attribute exists

`Bugfix` | [OGC-2547](https://linear.app/onegovcloud/issue/OGC-2547) | [d1165ed86e](https://github.com/onegov/onegov-cloud/commit/d1165ed86e0a78b1dac9c9e59c5cc74e3ccc0b4c)

### Ris

##### Link political business to meeting

`Feature` | [OGC-2521](https://linear.app/onegovcloud/issue/OGC-2521) | [9bf54e6dbd](https://github.com/onegov/onegov-cloud/commit/9bf54e6dbd8f481ae1a3122c4538991aa54e2ae6)

### Wil

##### Event import: Remove imported events that are not in the current xml stream

The xml stream represents a complete set of events

`Bugfix` | [OGC-2447](https://linear.app/onegovcloud/issue/OGC-2447) | [1ecaa32222](https://github.com/onegov/onegov-cloud/commit/1ecaa32222f8a69e76b9a739961f3656bc73009a)

## 2025.41

`2025-08-14` | [70e42da5d8...12ec42d921](https://github.com/OneGov/onegov-cloud/compare/70e42da5d8^...12ec42d921)

**Upgrade hints**
- onegov-org --select /onegov_town6/wil ris-rename-imported-participation-types-to-english or sudo ogc org --select /onegov_town6/wil ris-rename-imported-participation-types-to-english
### Ogc

##### Add hint for ideal event image size

`Feature` | [OGC-2338](https://linear.app/onegovcloud/issue/OGC-2338) | [29a9490c6a](https://github.com/onegov/onegov-cloud/commit/29a9490c6ac2ef67fb9f4c580f7deb2ace7fedbc)

### Org

##### Adds submitter filter to tickets list

`Feature` | [OGC-2438](https://linear.app/onegovcloud/issue/OGC-2438) | [2cc7b3227f](https://github.com/onegov/onegov-cloud/commit/2cc7b3227f722955e26c026271cc71ba6b2ab2ec)

##### Allows forms and resources to define a reply-to address

This supersedes the global reply-to address for ticket emails sent by
FRM and RSV tickets linked to their respective form or resource.

`Feature` | [OGC-2538](https://linear.app/onegovcloud/issue/OGC-2538) | [4e945fdd03](https://github.com/onegov/onegov-cloud/commit/4e945fdd03dd0b3f4cc92bb74446dd31485ddb6e)

##### Adds additional payment provider specific references to export

`Feature` | [OGC-2545](https://linear.app/onegovcloud/issue/OGC-2545) | [93cadab79a](https://github.com/onegov/onegov-cloud/commit/93cadab79a930ff59c4a8c374e9727a2b866a3d2)

##### Allows the submitter email to be changed for some ticket types

`Feature` | [OGC-2504](https://linear.app/onegovcloud/issue/OGC-2504) | [c5f28d0179](https://github.com/onegov/onegov-cloud/commit/c5f28d01796c76c10a7eeba55d6eb25a0236605f)

##### Avoids hard failures when revocation of a key code fails

Instead we log and report the error as a warning in the front end when
appropriate.

`Bugfix` | [OGC-2539](https://linear.app/onegovcloud/issue/OGC-2539) | [d2e6a5102d](https://github.com/onegov/onegov-cloud/commit/d2e6a5102d826779adc526f12b03d10e9fb70a45)

##### Avoids minimum price total validation if the minimum total is 0

The price can be negative to offset the prices that originate from
outside the form submission, like prices per entry or prices per hour.

`Bugfix` | [OGC-2540](https://linear.app/onegovcloud/issue/OGC-2540) | [3f6fdcb5af](https://github.com/onegov/onegov-cloud/commit/3f6fdcb5af842401cd3d23372bc707bfd3fd41ab)

### Ris

##### Ensure parliamentarians are listed with last name first

affected: political business, commissions, parliamentarian groups

`Feature` | [OGC-2506](https://linear.app/onegovcloud/issue/OGC-2506) | [e589685a2b](https://github.com/onegov/onegov-cloud/commit/e589685a2b951808c892948c4acda8877ea6e106)

##### Rename date label for political businesses

`Feature` | [OGC-2519](https://linear.app/onegovcloud/issue/OGC-2519) | [f34a6432a5](https://github.com/onegov/onegov-cloud/commit/f34a6432a5db8193db97cd74f5585c16f4720e55)

##### Rename parliamentarian membership to function

`Feature` | [OGC-2511](https://linear.app/onegovcloud/issue/OGC-2511) | [3f2024a426](https://github.com/onegov/onegov-cloud/commit/3f2024a426c689fd2c7a641ee1a424addc46f136)

##### List next meeting on top, always

`Feature` | [OGC-2514](https://linear.app/onegovcloud/issue/OGC-2514) | [9aa57fc487](https://github.com/onegov/onegov-cloud/commit/9aa57fc487a2105c1dd572db2593ba0b391a24e7)

##### Edit parliamentarian party and show it

`Feature` | [OGC-2508](https://linear.app/onegovcloud/issue/OGC-2508) | [88091dca8f](https://github.com/onegov/onegov-cloud/commit/88091dca8f0f134787e80799644681a8c7be3a15)

##### Adds gender-inclusive roles for parliament

`Feature` | [OGC-2510](https://linear.app/onegovcloud/issue/OGC-2510) | [6a88289dab](https://github.com/onegov/onegov-cloud/commit/6a88289dab7a632c84cd78606ad068042775e184)

##### Show political business number after title

`Feature` | [OGC-2512](https://linear.app/onegovcloud/issue/OGC-2512) | [ecdc2b604d](https://github.com/onegov/onegov-cloud/commit/ecdc2b604d8be6f041c74c799a2cb38e43f9fe5f)

##### Adds party filter to the parliamentarians view

`Feature` | [OGC-2509](https://linear.app/onegovcloud/issue/OGC-2509) | [d221ae6747](https://github.com/onegov/onegov-cloud/commit/d221ae6747304031aab1ec32cb37fa785abf88b0)

##### Fix/Translate political business participation types

`Bugfix` | [OGC-2534](https://linear.app/onegovcloud/issue/OGC-2534) | [70e42da5d8](https://github.com/onegov/onegov-cloud/commit/70e42da5d8c159f24a8baf509c333cf942387b1a)

## 2025.40

`2025-08-12` | [8693e9e3ad...1bd35958dc](https://github.com/OneGov/onegov-cloud/compare/8693e9e3ad^...1bd35958dc)

### Org

##### Displays invoice items in confirmation step before payment

`Feature` | [OGC-2287](https://linear.app/onegovcloud/issue/OGC-2287) | [e874288cc9](https://github.com/onegov/onegov-cloud/commit/e874288cc9f50331f1670039cd534d7d08bbea1d)

##### Upgrade db upgrade step

`Bugfix` | [OGC-2535](https://linear.app/onegovcloud/issue/OGC-2535) | [dd5d553803](https://github.com/onegov/onegov-cloud/commit/dd5d55380307bccf85fcdf9afb933cf169d5045a)

### Ris

##### Show parliamentarians last name first (as they are sorted by last name)

`Feature` | [OGC-2506](https://linear.app/onegovcloud/issue/OGC-2506) | [90a0333e0e](https://github.com/onegov/onegov-cloud/commit/90a0333e0eee30b6552c31514c6b69521d155225)

##### Show business type for agenda items of a meeting

`Feature` | [OGC-2518](https://linear.app/onegovcloud/issue/OGC-2518) | [f71417732d](https://github.com/onegov/onegov-cloud/commit/f71417732d7da73a8cfadff18b5ad6fc3619b77a)

##### Only show active members of parliamentary group

`Feature` | [OGC-2523](https://linear.app/onegovcloud/issue/OGC-2523) | [98edfb501c](https://github.com/onegov/onegov-cloud/commit/98edfb501c039fc06e9a1bf5abed10ecbd87ad76)

##### Load editor for html fields in meeting edit view

`Bugfix` | [OGC-2515](https://linear.app/onegovcloud/issue/OGC-2515) | [b5f6c6ced8](https://github.com/onegov/onegov-cloud/commit/b5f6c6ced8d42348c8fcc898eb0c26f9dab82700)

### Wil

##### Event import for multiple zip codes

`Feature` | [OGC-2530](https://linear.app/onegovcloud/issue/OGC-2530) | [4e7b700a57](https://github.com/onegov/onegov-cloud/commit/4e7b700a57d56fe325f021cb4ecec0028b55a547)

## 2025.39

`2025-08-06` | [3cfa6d9948...96f2b550b5](https://github.com/OneGov/onegov-cloud/compare/3cfa6d9948^...96f2b550b5)

### Org

##### Allows members to view tickets if they know the URL

They can also create notes and edit/delete their own notes, but they
cannot perform any other actions on the ticket.

This allows involving interested third parties to be involved in the
ticket process, like e.g. a janitor for a reservation ticket.

`Feature` | [OGC-2285](https://linear.app/onegovcloud/issue/OGC-2285) | [7b6a59e613](https://github.com/onegov/onegov-cloud/commit/7b6a59e6131a1782bcef5a5809ef13a40b479fcc)

##### Fixes deleting the final reservation on a ticket with a submission

`Bugfix` | [OGC-2503](https://linear.app/onegovcloud/issue/OGC-2503) | [2534b698f6](https://github.com/onegov/onegov-cloud/commit/2534b698f60cd51bfff1c451732badc028ce8ce9)

### Ris

##### Edit commission membership

`Feature` | [OGC-2461](https://linear.app/onegovcloud/issue/OGC-2461) | [d86689e0c0](https://github.com/onegov/onegov-cloud/commit/d86689e0c083a9ba3ba2597730bca523c7e4ca14)

##### Include commission memberships in Parliamentarians active property

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [62b6a77a88](https://github.com/onegov/onegov-cloud/commit/62b6a77a88cf84dd024e981f6d47dabc5adabd25)

##### Create interest ties from scratch for new parliamentarian

`Bugfix` | [OGC-2455](https://linear.app/onegovcloud/issue/OGC-2455) | [3cfa6d9948](https://github.com/onegov/onegov-cloud/commit/3cfa6d994887ada9404cbbc7a96f7f5c2e01fb71)

### User

##### Show active users by default

`Bugfix` | [OGC-2276](https://linear.app/onegovcloud/issue/OGC-2276) | [ec4eb4130c](https://github.com/onegov/onegov-cloud/commit/ec4eb4130cf6d0d2a895d4d97156ef8fe369bea1)

## 2025.38

`2025-08-05` | [1e867a456f...8ad8b62294](https://github.com/OneGov/onegov-cloud/compare/1e867a456f^...8ad8b62294)

### Agency

##### Add `miscField` for sync.

`Feature` | [OGC-1894](https://linear.app/onegovcloud/issue/OGC-1894) | [6af98c9c2f](https://github.com/onegov/onegov-cloud/commit/6af98c9c2f4a15175fa162c7e50c1e5ad9163ac1)

### Org

##### Makes sure that changing the tag updates the Kaba code

`Bugfix` | [OGC-2495](https://linear.app/onegovcloud/issue/OGC-2495) | [98ddf66068](https://github.com/onegov/onegov-cloud/commit/98ddf66068ac8bab03067dc2842e684c42fd4156)

### Ris

##### Meeting Items can be edited and extended

`Feature` | [OGC-2477](https://linear.app/onegovcloud/issue/OGC-2477) | [e435583f66](https://github.com/onegov/onegov-cloud/commit/e435583f664f31e36a684f8b3dbcdfc4213ed13e)

##### Interest ties are now editable

`Feature` | [OGC-2455](https://linear.app/onegovcloud/issue/OGC-2455) | [f3a878e491](https://github.com/onegov/onegov-cloud/commit/f3a878e49165933313ecdda96db6d706b862750d)

##### Adds hard-coded RIS link for non logged-in users

`Feature` | [OGC-2371](https://linear.app/onegovcloud/issue/OGC-2371) | [dafd61b5d9](https://github.com/onegov/onegov-cloud/commit/dafd61b5d92044d5ffee4443cec90ce42daa1828)

##### Main url for RIS is now configurable

`Feature` | [OGC-2371](https://linear.app/onegovcloud/issue/OGC-2371) | [2f0b2f4c8d](https://github.com/onegov/onegov-cloud/commit/2f0b2f4c8dfe8b461445a3177f9b96fa4257fd25)

##### Menu to add commission memberships

`Feature` | [OGC-2461](https://linear.app/onegovcloud/issue/OGC-2461) | [a139888454](https://github.com/onegov/onegov-cloud/commit/a1398884547a04c41deac591a7a07f0d4b2b0fff)

##### Improve political business filtering

Sentry: https://seantis-gmbh.sentry.io/issues/6778531266/

`Bugfix` | [NONE](#NONE) | [1e867a456f](https://github.com/onegov/onegov-cloud/commit/1e867a456f7b36044e8e0c248eee4467d929863d)

##### Makes form fields in edit meeting evenly wide.

`Bugfix` | [OGC-2453](https://linear.app/onegovcloud/issue/OGC-2453) | [0727a45720](https://github.com/onegov/onegov-cloud/commit/0727a457205f90d675509f671f03f8275050d9ed)

## 2025.37

`2025-07-31` | [7f64381a29...a77c094060](https://github.com/OneGov/onegov-cloud/compare/7f64381a29^...a77c094060)

### Dir

##### Bring fields in same field set together

`Bugfix` | [NONE](#NONE) | [af00a3b5c1](https://github.com/onegov/onegov-cloud/commit/af00a3b5c16c24414ed77881483fa0fbdc3dd900)

### Org

##### Adds ticket invoices with individual items

This allows more robust modifications of ticket details with those
modifications resulting in correct price changes. While also itemizing
manually granted discounts or surcharges.

`Feature` | [OGC-2321](https://linear.app/onegovcloud/issue/OGC-2321) | [69cd95cb21](https://github.com/onegov/onegov-cloud/commit/69cd95cb21bf0ab4857a842c0d05c97b32fe99b5)

##### Fixes mTAN statistics not being sent for every month

The previous fix actually introduced the problem it claimed to fix

`Bugfix` | [OGC-2288](https://linear.app/onegovcloud/issue/OGC-2288) | [7591396b9a](https://github.com/onegov/onegov-cloud/commit/7591396b9aa9941fa7f286fb6487dbd7c5621035)

### Pas

##### Allows to copy rate set.

`Feature` | [OGC-2443](https://linear.app/onegovcloud/issue/OGC-2443) | [e9c88617b2](https://github.com/onegov/onegov-cloud/commit/e9c88617b20557827b703420693ccd369aed1d91)

### Ris

##### Show parliamentarians place of residence

Display private address if available, otherwise show place of residence

`Feature` | [OGC-2487](https://linear.app/onegovcloud/issue/OGC-2487) | [7f64381a29](https://github.com/onegov/onegov-cloud/commit/7f64381a29f3eb772b43d19bf35f9474a70f3943)

##### Make parliamentarian labels gender neutral

`Feature` | [OGC-2486](https://linear.app/onegovcloud/issue/OGC-2486) | [5d8720535d](https://github.com/onegov/onegov-cloud/commit/5d8720535d0c28a68aa2e83502a2116301ace794)

## 2025.36

`2025-07-25` | [93fd541297...444995fa15](https://github.com/OneGov/onegov-cloud/compare/93fd541297^...444995fa15)

### Directories

##### Give access to publication dates to editor role

`Feature` | [OGC-2474](https://linear.app/onegovcloud/issue/OGC-2474) | [1cceecd334](https://github.com/onegov/onegov-cloud/commit/1cceecd33464402cda501b787fb31cfa784e4e41)

### Events

##### Allow header and footer information for event list

`Feature` | [OGC-2415](https://linear.app/onegovcloud/issue/OGC-2415) | [029b2c80a8](https://github.com/onegov/onegov-cloud/commit/029b2c80a878fd77a3d558c4d571388f0aa396bd)

### Org

##### Avoids invalid ticket `state` parameter propagating to the view

`Bugfix` | [93fd541297](https://github.com/onegov/onegov-cloud/commit/93fd5412978bf00b8963c28d56fc7a738322f04a)

### Pay

##### Properly filters our expected Worldline Saferpay payment errors

`Bugfix` | [8ef5f37124](https://github.com/onegov/onegov-cloud/commit/8ef5f37124fd4e56b3f3ab730d181aa05e6cf1db)

### Wil

##### Event import - prevent setting coordiantes to invalid values

`Bugfix` | [OGC-2380](https://linear.app/onegovcloud/issue/OGC-2380) | [867117fc85](https://github.com/onegov/onegov-cloud/commit/867117fc8565efa154eb5e82849ba6aba8d26aa8)

