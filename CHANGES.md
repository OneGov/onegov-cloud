# Changes

## 2025.31

`2025-07-07` | [fe887383ec...1fec99e1b9](https://github.com/OneGov/onegov-cloud/compare/fe887383ec^...1fec99e1b9)

### Org

##### Vimeo unlisted videos

`Feature` | [OGC-2412](https://linear.app/onegovcloud/issue/OGC-2412) | [1fec99e1b9](https://github.com/onegov/onegov-cloud/commit/1fec99e1b9505559e6e07930a55511c151367dc6)

### Ris

##### Show date and time of meeting

`Feature` | [OGC-2254](https://linear.app/onegovcloud/issue/OGC-2254) | [7b7a5861b4](https://github.com/onegov/onegov-cloud/commit/7b7a5861b45e8ff8d8128ff0c07a565b3dbf3c67)

##### Provide files to political business template

`Bugfix` | [OGC-2419](https://linear.app/onegovcloud/issue/OGC-2419) | [fe887383ec](https://github.com/onegov/onegov-cloud/commit/fe887383ecd1a1210577e62541f4c28f83868d2d)

## 2025.30

`2025-07-03` | [5fb710d69d...5725423a04](https://github.com/OneGov/onegov-cloud/compare/5fb710d69d^...5725423a04)

### Org

##### Allows subscription to confirmed personal reservations via iCal

`Feature` | [OGC-2399](https://linear.app/onegovcloud/issue/OGC-2399) | [5fb710d69d](https://github.com/onegov/onegov-cloud/commit/5fb710d69d4b6df8476c6021c5e74a8ae2f94796)

### Pay

##### Silences 3D-Secure Verification errors

`Bugfix` | [92d3e8da7f](https://github.com/onegov/onegov-cloud/commit/92d3e8da7fd1b41ae6949bbbd26670136ed81903)

## 2025.29

`2025-07-03` | [93a736507d...bb698f8fd3](https://github.com/OneGov/onegov-cloud/compare/93a736507d^...bb698f8fd3)

**Upgrade hints**
- onegov-org --select /onegov_town6/wil ris-resolve-parliamentarian-doublette
### Form

##### Adds an optional reset button to forms

Adds that reset button to reservation forms for admins

`Feature` | [OGC-2390](https://linear.app/onegovcloud/issue/OGC-2390) | [6a5ffc42d9](https://github.com/onegov/onegov-cloud/commit/6a5ffc42d9bfdf5d66f2760f60d38712aedf4fd2)

##### Ensures `data-auto-fill` works for radio- and checkboxes

`Bugfix` | [OGC-2408](https://linear.app/onegovcloud/issue/OGC-2408) | [d5ab9369ca](https://github.com/onegov/onegov-cloud/commit/d5ab9369ca3317890c62d649ddda82ba7ac49286)

### Org

##### Adds a hint to the shared e-mail field in the user group form

`Feature` | [OGC-2396](https://linear.app/onegovcloud/issue/OGC-2396) | [d5e642c2c0](https://github.com/onegov/onegov-cloud/commit/d5e642c2c00cc914bfaf726747c7d42d0312939d)

##### Adds a citizen login with access to tickets and reservations

Rather than requiring user registration, all citizens have to do is to
request a login-link for their e-mail address with which they can gain
access to all the tickets and reservations tied to that e-mail address.

`Feature` | [OGC-2098](https://linear.app/onegovcloud/issue/OGC-2098) | [0048edd929](https://github.com/onegov/onegov-cloud/commit/0048edd9295228c9081bd1607a0c3d65321c6ca9)

##### Fixes small regression in reservation calendar

`Bugfix` | [OGC-2389](https://linear.app/onegovcloud/issue/OGC-2389) | [e96c912b1c](https://github.com/onegov/onegov-cloud/commit/e96c912b1c74476bf07c4d237ced65d5ea84e641)

### Ris

##### Various improvements

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [63ecf0b4d7](https://github.com/onegov/onegov-cloud/commit/63ecf0b4d70d649cc183de8a547d654bad18fe41)

##### Remove party view

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [82ceca571b](https://github.com/onegov/onegov-cloud/commit/82ceca571bae15b954f8df79df3d52f9e78b094b)

##### Move files for political business to sidebar

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [077dda6e0d](https://github.com/onegov/onegov-cloud/commit/077dda6e0d9fe409f4b7f66225e024899dddae26)

##### Use more-list for political business and meeting views

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [f1e1d2fec8](https://github.com/onegov/onegov-cloud/commit/f1e1d2fec84bff3fab1168e38ddc48abee61c914)

##### Set end date for inactive parliamentarian, copy shipping address to private address

onegov-org --select /onegov_town6/wil ris-shipping-to-private-address
onegov-org --select /onegov_town6/wil ris-set-end-date-for-inactive-parliamentarians

`Feature` | [OGC-2245, OGC-2409](https://linear.app/onegovcloud/issue/OGC-2245, OGC-2409) | [8f05e17030](https://github.com/onegov/onegov-cloud/commit/8f05e17030a8592abb45b7c0d8c3604cbd28d5e1)

##### Shows parliamentarians political businesses

`Feature` | [OGC-2405](https://linear.app/onegovcloud/issue/OGC-2405) | [a5112d5348](https://github.com/onegov/onegov-cloud/commit/a5112d534894da3b11b5e9bad05247600b1566da)

##### Resolve parliamentarian doublette

`Feature` | [OGC-2394](https://linear.app/onegovcloud/issue/OGC-2394) | [d3fc3c3971](https://github.com/onegov/onegov-cloud/commit/d3fc3c3971dc3f3f67f94dbf54c2fae21201e52d)

##### Sort participants of political business

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [6abcbdea95](https://github.com/onegov/onegov-cloud/commit/6abcbdea950caf9a29ed7a8c5a8bb2125ae83b13)

##### Remove personnel number and contract number from form

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [eaadff40a5](https://github.com/onegov/onegov-cloud/commit/eaadff40a5915a2403f3d4af5071ae559ba4803a)

### Town6

##### Writes a bunch of translations that were missing.

`Bugfix` | [OGC-2392](https://linear.app/onegovcloud/issue/OGC-2392) | [70c5b18543](https://github.com/onegov/onegov-cloud/commit/70c5b18543bed3d89034e9d19cee6c383331dc62)

##### In `MeetingItem` list, uses a different strategy to get the `PoliticalBusiness`, for now.

Currently the `political_business_id` is NULL.
This makes it impossible to generate valid political_business_link.
We can circumvent this problem by querying each `PoliticalBusiness` and
checking for `self_id` in meta.

`Bugfix` | [OGC-2388](https://linear.app/onegovcloud/issue/OGC-2388) | [ca68bd6202](https://github.com/onegov/onegov-cloud/commit/ca68bd620204afc1d60c62087b3a976956449ba9)

##### Filter meetings to only show those with items.

`Bugfix` | [OGC-2388](https://linear.app/onegovcloud/issue/OGC-2388) | [581e5260e4](https://github.com/onegov/onegov-cloud/commit/581e5260e463218b752a24a6469678ba91bac88f)

## 2025.28

`2025-06-30` | [61c47ca6f9...d352e57dcf](https://github.com/OneGov/onegov-cloud/compare/61c47ca6f9^...d352e57dcf)

### Ris

##### Adds missing translations and fixes address import

`Feature` | [OGC-2375](https://linear.app/onegovcloud/issue/OGC-2375) | [61c47ca6f9](https://github.com/onegov/onegov-cloud/commit/61c47ca6f9a3c2684b1e666a27354f6ba28a379a)

##### Link to membership only for managers

`Feature` | [OGC-2377](https://linear.app/onegovcloud/issue/OGC-2377) | [33cc1983c5](https://github.com/onegov/onegov-cloud/commit/33cc1983c5460942caf00b17e4c0c29bf07f5c57)

##### Display iterest table for parliamentarians

`Feature` | [OGC-2300](https://linear.app/onegovcloud/issue/OGC-2300) | [3e48eda4c4](https://github.com/onegov/onegov-cloud/commit/3e48eda4c4b1aa0ead39c579998ff3e6311c8af9)

##### Adds Political Business views

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [1aafa8de9e](https://github.com/onegov/onegov-cloud/commit/1aafa8de9e7cd0e26a2607acb46e4005e4829a97)

## 2025.27

`2025-06-27` | [b4b7a8fd28...9c0c99df62](https://github.com/OneGov/onegov-cloud/compare/b4b7a8fd28^...9c0c99df62)

### Form

##### Fixes another small regression in formcode related to pricing

`Bugfix` | [OGC-2349](https://linear.app/onegovcloud/issue/OGC-2349) | [fdd2ad3be7](https://github.com/onegov/onegov-cloud/commit/fdd2ad3be761dfeb7243cc3d5289969a1fa8e800)

### Org

##### Adds icon to date picker in calendar views to make it more obvious

This also ensures picked dates are added to the browser history

`Feature` | [OGC-2330](https://linear.app/onegovcloud/issue/OGC-2330) | [5abe2b07f9](https://github.com/onegov/onegov-cloud/commit/5abe2b07f931a95c67b6f2c696927af37883df4c)

##### Only display VAT for forms that have it enabled

This also includes a payment summary in the ticket opened/closed mails
which replaces the price display and a payment summary in the ticket
status page.

`Feature` | [OGC-2341](https://linear.app/onegovcloud/issue/OGC-2341) | [987e72bcb6](https://github.com/onegov/onegov-cloud/commit/987e72bcb60a243582127a7add0543c3c2b3a536)

##### Make it more obvious that pay later means pay by invoice

`Feature` | [OGC-2340](https://linear.app/onegovcloud/issue/OGC-2340) | [c714a4aa3c](https://github.com/onegov/onegov-cloud/commit/c714a4aa3c13c5a614e2d851c788bfff3cff7deb)

##### Allows setting a shared e-mail for immediate ticket notifications

`Feature` | [OGC-2360](https://linear.app/onegovcloud/issue/OGC-2360) | [5d80af7c0e](https://github.com/onegov/onegov-cloud/commit/5d80af7c0e5576fb1cae0bc37774a4bcc89800ad)

##### Keeps track of which tickets view was visited last

This applies to the link in the breadcrumbs and where we redirect to
after closing/deleting a ticket.

This also fixes an unrelated bug with the stored ticket summary for RSV
tickets.

`Feature` | [OGC-2362](https://linear.app/onegovcloud/issue/OGC-2362) | [d239ca03bc](https://github.com/onegov/onegov-cloud/commit/d239ca03bc560105e5b079d95215f16de70474f1)

##### Fixes crash in ticket PDF for Worldline Saferpay payments

`Bugfix` | [OGC-2345](https://linear.app/onegovcloud/issue/OGC-2345) | [00054ff0bf](https://github.com/onegov/onegov-cloud/commit/00054ff0bf62c1d0ecc3b3dc8f8e2fb508d25f89)

##### Avoid crash in latest occurrence view if there are no occurrences

`Bugfix` | [d4135bb209](https://github.com/onegov/onegov-cloud/commit/d4135bb2095c10d99177ae7e15c965293ef834d6)

### Pay

##### Avoid logging exception for aborted Saferpay transactions

`Bugfix` | [OGC-2239](https://linear.app/onegovcloud/issue/OGC-2239) | [fcba01085d](https://github.com/onegov/onegov-cloud/commit/fcba01085ddd1f274f64c5e7234ec513bb156330)

### Ris

##### Adding views

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [dfee5bf84f](https://github.com/onegov/onegov-cloud/commit/dfee5bf84fbff5f997a816d43a273c01673b5a2c)

### User

##### Fixes signature/digest configuration for SAML2 provider

`Bugfix` | [OGC-2248](https://linear.app/onegovcloud/issue/OGC-2248) | [78c9317dcc](https://github.com/onegov/onegov-cloud/commit/78c9317dcc7e27824f6feafcac1e3b22eaacaca9)

## 2025.26

`2025-06-21` | [52b383bcf1...3d7684c5ae](https://github.com/OneGov/onegov-cloud/compare/52b383bcf1^...3d7684c5ae)

### Form

##### Formcode relax line end requirement after discount/pricing/label in check-/radioboxes

`Bugfix` | [OGC-2315](https://linear.app/onegovcloud/issue/OGC-2315) | [ea0db55721](https://github.com/onegov/onegov-cloud/commit/ea0db557210779da0de2d58fd4112046782bd543)

### Landsgemeinde

##### Update timestamp through states view

Only update timestamp on save or when changing the state through the states view

`Feature` | [OGC-2242](https://linear.app/onegovcloud/issue/OGC-2242) | [52b383bcf1](https://github.com/onegov/onegov-cloud/commit/52b383bcf1c5c3bdfeb4da1c88dd1e676febeaec)

### Org

##### Add import reservation cli

`Feature` | [OGC-2179](https://linear.app/onegovcloud/issue/OGC-2179) | [8bfd03a5d5](https://github.com/onegov/onegov-cloud/commit/8bfd03a5d5605c234554f9e2a79d34618b6d1090)

##### Confirm deletion of pages and agencies

`Feature` | [OGC-2238](https://linear.app/onegovcloud/issue/OGC-2238) | [a3d0b20e5e](https://github.com/onegov/onegov-cloud/commit/a3d0b20e5e667afacce38913f9cc0007b957f26e)

##### Correct invalid submission definitions for Steinhausen

`Feature` | [OGC-2315](https://linear.app/onegovcloud/issue/OGC-2315) | [b6d023c336](https://github.com/onegov/onegov-cloud/commit/b6d023c3366963da77aa3c3bdbc7dd4a8475e3df)

##### Adds function to send a reservation summary mail

`Feature` | [OGC-2312](https://linear.app/onegovcloud/issue/OGC-2312) | [bd991be53e](https://github.com/onegov/onegov-cloud/commit/bd991be53e990fe0b5cd58ff4603d780193a9433)

##### Adds links to the occupancy view from the reservation ticket

`Feature` | [OGC2331](#OGC2331) | [871d97e57d](https://github.com/onegov/onegov-cloud/commit/871d97e57d546bee616861cc21dbe2375710aae0)

##### Allows granular ticket permissions for reservation resources

`Feature` | [OGC-2329](https://linear.app/onegovcloud/issue/OGC-2329) | [24c9590478](https://github.com/onegov/onegov-cloud/commit/24c9590478184c7910acef50df80ce518459317d)

##### Upgrades FullCalendar to v6 and adds a multi-month view

`Feature` | [OGC-2302](https://linear.app/onegovcloud/issue/OGC-2302) | [e58e584a2e](https://github.com/onegov/onegov-cloud/commit/e58e584a2e46326f17413514817a9f91df30f999)

##### Fixes broken `accept-reservation-with-message` forwarding

`Bugfix` | [OGC-2301](https://linear.app/onegovcloud/issue/OGC-2301) | [997583b219](https://github.com/onegov/onegov-cloud/commit/997583b21973169aaf5a523f4e8f4c06871d1936)

##### Disallows adjustments of accepted reservations

Previously this would lead to potentially opaque modifications of
reservations without the customer being informed of those changes.

If we end up needing to allow something like this again we should
do something more robust with workflow steps that keep the customer
in the loop.

`Bugfix` | [OGC-2322](https://linear.app/onegovcloud/issue/OGC-2322) | [9f1c0f3dc4](https://github.com/onegov/onegov-cloud/commit/9f1c0f3dc4e1cbe7632d9fa315ab15188943a0f5)

##### Once again shows the email address in occupancy view

`Bugfix` | [OGC-2336](https://linear.app/onegovcloud/issue/OGC-2336) | [0d4063c13e](https://github.com/onegov/onegov-cloud/commit/0d4063c13e9568822bb575642fe651507425c786)

### Ris

##### Models for RIS light

`Feature` | [OGC-2245](https://linear.app/onegovcloud/issue/OGC-2245) | [970de68241](https://github.com/onegov/onegov-cloud/commit/970de682415aca5284774c0474f594db8ebda33b)

### Ticket

##### Store submitter email directly on the ticket

`Performance` | [OGC-2323](https://linear.app/onegovcloud/issue/OGC-2323) | [92cc274f75](https://github.com/onegov/onegov-cloud/commit/92cc274f759569623f4a1403412e27881981ead6)

### User

##### Allows client key/cert pair to be specified for SAML2 SPs

Adds an internal endpoint for retrieving the sp.xml file

`Feature` | [OGC-2248](https://linear.app/onegovcloud/issue/OGC-2248) | [2736227c42](https://github.com/onegov/onegov-cloud/commit/2736227c42d2628a5bd64231576827350a177551)

## 2025.25

`2025-06-05` | [bd761b9a66...212a86a4eb](https://github.com/OneGov/onegov-cloud/compare/bd761b9a66^...212a86a4eb)

### Form

##### Fixes edge cases for priced/discounted options in form code

Previously you weren't allowed to use any parantheses in the label since
that would break the detection of the pricing information.

`Bugfix` | [OGC-2286](https://linear.app/onegovcloud/issue/OGC-2286) | [a4e1f674f4](https://github.com/onegov/onegov-cloud/commit/a4e1f674f4e6abcc50bf1767e0616ab82420d4f8)

### Newsletter

##### List all occurrences in newsletter creation form

Previously only Events without their re-occurrences were listed when creating a newsletter

`Feature` | [OGC-2280](https://linear.app/onegovcloud/issue/OGC-2280) | [3445bf9a30](https://github.com/onegov/onegov-cloud/commit/3445bf9a3035292b6e4c21dc669c74e8ed3e1ace)

### Org

##### Wil event import: Provider url alternatively to event url

`Feature` | [OGC-2184](https://linear.app/onegovcloud/issue/OGC-2184) | [23c27aca30](https://github.com/onegov/onegov-cloud/commit/23c27aca30d0f04286224efce47fa9f167c0271d)

##### Replaces the occupancy list with an interactive calendar view

`Feature` | [OGC-2236](https://linear.app/onegovcloud/issue/OGC-2236) | [5fc60fd943](https://github.com/onegov/onegov-cloud/commit/5fc60fd9434ee173ec7a5e202d87224cce4e86bc)

##### Refreshes results summary in occupancy view when changing filters

Previously we would only refresh the results list, but the summary is
just as important.

`Bugfix` | [OGC-2284](https://linear.app/onegovcloud/issue/OGC-2284) | [7d717caad1](https://github.com/onegov/onegov-cloud/commit/7d717caad17896e0b9be86294b4dac75a186e10c)

##### Fixes mTAN statistics not being sent for every month

`Bugfix` | [OGC-2288](https://linear.app/onegovcloud/issue/OGC-2288) | [6ff6be3419](https://github.com/onegov/onegov-cloud/commit/6ff6be3419e8a50982f06c853d4dee0a641343b6)

### Reservation

##### Allows prices in extra fields to count per hour or per item

This used to always be a one-off price, which was probably not intended.
The new default is to apply extra pricing per item, existing resources
will still use the old default of "one-off".

`Feature` | [OGC-2262](https://linear.app/onegovcloud/issue/OGC-2262) | [a94bdc2daf](https://github.com/onegov/onegov-cloud/commit/a94bdc2dafd2318deb21618a1613125807d20d05)

## 2025.24

`2025-05-23` | [2a00905128...f104144b6b](https://github.com/OneGov/onegov-cloud/compare/2a00905128^...f104144b6b)

### Landsgemeinde

##### Allow Fullscreen for Videos

`Bugfix` | [OGC-2231](https://linear.app/onegovcloud/issue/OGC-2231) | [eb98dcf795](https://github.com/onegov/onegov-cloud/commit/eb98dcf7951ff1a14ebb9efedf1e1b69379e49fe)

### Org

##### Adds optional proportional discounts for reservations to formcode

`Feature` | [OGC-2252](https://linear.app/onegovcloud/issue/OGC-2252) | [c2a46995af](https://github.com/onegov/onegov-cloud/commit/c2a46995af5e77701e20e29acd192a132cb9f8b7)

##### Allows key codes in tickets with future reservations to be edited

`Feature` | [OGC-2205](https://linear.app/onegovcloud/issue/OGC-2205) | [5fc2303cc7](https://github.com/onegov/onegov-cloud/commit/5fc2303cc7c8f16cb4e551a168311452082eae0b)

##### Add icons and links or tiktok and linkedIn

`Bugfix` | [OGC-2249](https://linear.app/onegovcloud/issue/OGC-2249) | [dff0d2db74](https://github.com/onegov/onegov-cloud/commit/dff0d2db745356273d4edebed048e6fa63404d29)

### Reservation

##### Switches libres JSON columns from `TEXT` to `JSONB`

`Performance` | [OGC-2035](https://linear.app/onegovcloud/issue/OGC-2035) | [10219ad990](https://github.com/onegov/onegov-cloud/commit/10219ad9906e18f5d91b76f503d18212b288054e)

### Search

##### Replaces `langdetect` with `lingua-language-detector`

`Performance` | [OGC-1781](https://linear.app/onegovcloud/issue/OGC-1781) | [23578296b5](https://github.com/onegov/onegov-cloud/commit/23578296b580b3c9342b77f53d10147e8cc9c7b7)

### Wil

##### Adds daily cron job to import events from saiten

`Feature` | [OGC-2184](https://linear.app/onegovcloud/issue/OGC-2184) | [2a00905128](https://github.com/onegov/onegov-cloud/commit/2a00905128f4d06b99d8a53dd7343d7355459571)

## 2025.23

`2025-05-19` | [cf50671551...039bb2563f](https://github.com/OneGov/onegov-cloud/compare/cf50671551^...039bb2563f)

### Org

##### Allows adjusting individual reservations within a ticket

For now these adjustments are limited to the same allocation on the same
day. Eventually we may allow moving reservations to arbitrary free
allocations as long as the settings on the target allocation allow it.

`Feature` | [OGC-2155](https://linear.app/onegovcloud/issue/OGC-2155) | [1d2870de8c](https://github.com/onegov/onegov-cloud/commit/1d2870de8cc67972c4f29ede5f236a9c2b8f62e2)

### Server

##### Avoids caching partially configured application instances

Since `CachedApplication` was setting `self.instance` before the
application was configured and the server will continue serving
subsequent requests after a failed one, it was possible for a
partially initialized application to end up in the cache, which
leads to cryptic error messages.

It's better if we fail the same way on every request, so we don't
get distracted by red herrings.

`Bugfix` | [6ae340b3d9](https://github.com/onegov/onegov-cloud/commit/6ae340b3d94c4b33c18b45dd7f41019db9b2958e)

### Town6

##### Reactivate recipient in cron job if no longer on postmark suppression list

`Feature` | [OGC-2212](https://linear.app/onegovcloud/issue/OGC-2212) | [4688da1d6f](https://github.com/onegov/onegov-cloud/commit/4688da1d6f6924b24f622055f9c072ba7a88a2a9)

## 2025.22

`2025-05-09` | [b1505595a8...71b5a6d944](https://github.com/OneGov/onegov-cloud/compare/b1505595a8^...71b5a6d944)

### Feriennet

##### Swisspass ID is now optional

`Feature` | [OGC-1388](https://linear.app/onegovcloud/issue/OGC-1388) | [49ed887c76](https://github.com/onegov/onegov-cloud/commit/49ed887c76b6b644795f256849eb4fde9d917d69)

### Form

##### Adds generic field for geographic autocompletion.

`Feature` | [OGC-2216](https://linear.app/onegovcloud/issue/OGC-2216) | [cf5e83d511](https://github.com/onegov/onegov-cloud/commit/cf5e83d5112446cfa82e14beaf844a791fd03a06)

### Landsgemeinde

##### Function color

`Feature` | [OGC-1892](https://linear.app/onegovcloud/issue/OGC-1892) | [b1505595a8](https://github.com/onegov/onegov-cloud/commit/b1505595a85da7fe8177237cf023936850f1983d)

##### Spacing between icon and time

`Bugfix` | [OGC-1620](https://linear.app/onegovcloud/issue/OGC-1620) | [aa7807ad63](https://github.com/onegov/onegov-cloud/commit/aa7807ad635a9e84b46f338f90df69d1c8ad07b0)

##### Fix ticker update

`Bugfix` | [OGC-2240](https://linear.app/onegovcloud/issue/OGC-2240) | [6031de92b4](https://github.com/onegov/onegov-cloud/commit/6031de92b45b906f6d3a076e6cca3ae908e522f5)

### Org

##### IFrame Information

`Feature` | [OGC-2175](https://linear.app/onegovcloud/issue/OGC-2175) | [0a11978dbd](https://github.com/onegov/onegov-cloud/commit/0a11978dbd8c07a9ba9461cf1b8acf3be05713ce)

##### User Information

Show additional user information

`Feature` | [OGC-2147](https://linear.app/onegovcloud/issue/OGC-2147) | [d6620b16b4](https://github.com/onegov/onegov-cloud/commit/d6620b16b4c67efd4b53311f0c6b850b03779268)

##### Add retry mechanism for postmark api calls on email bounce statistics cron job

`Feature` | [NONE](#NONE) | [a053a278f3](https://github.com/onegov/onegov-cloud/commit/a053a278f391d66d96da7c4a564db5bbdb263812)

##### People and Documents in Sidebar

`Bugfix` | [OGC-2142](https://linear.app/onegovcloud/issue/OGC-2142) | [e14af7a359](https://github.com/onegov/onegov-cloud/commit/e14af7a3597b5eb99694220f6fc97316796ea220)

### Ruff

##### Enables `ASYNC` and `LOG` as well as a couple of additional rules

Refactors capturing of exceptions and re-emitting them as `APIException`

`Other` | [e66369e960](https://github.com/onegov/onegov-cloud/commit/e66369e960e02e11da70cedd95b4feae16d21d9d)

### Town6

##### Skip form if there are no form fields in reservation

`Feature` | [OGC-2211](https://linear.app/onegovcloud/issue/OGC-2211) | [c33ffc11c2](https://github.com/onegov/onegov-cloud/commit/c33ffc11c2ed8c7130a2a3065e020ebe77218814)

##### Copy event button

`Feature` | [OGC-1900](https://linear.app/onegovcloud/issue/OGC-1900) | [a7e570ede0](https://github.com/onegov/onegov-cloud/commit/a7e570ede065c6f56b7e25fa3cb3a5b867fe68d9)

## 2025.21

`2025-04-24` | [6864d7cf50...8b0cd01cc9](https://github.com/OneGov/onegov-cloud/compare/6864d7cf50^...8b0cd01cc9)

### Org

##### Adds integration for dormakaba API

`Feature` | [OGC-2032](https://linear.app/onegovcloud/issue/OGC-2032) | [8268dfadff](https://github.com/onegov/onegov-cloud/commit/8268dfadff4754fddd73d74da5434e9008b4b91d)

### Reservation

##### Fixes upgrade task not running, when it should be run

`Bugfix` | [6864d7cf50](https://github.com/onegov/onegov-cloud/commit/6864d7cf50cd01fa78c71c698cfed93e8f712819)

## 2025.20

`2025-04-22` | [196ff526a9...3c6edf9228](https://github.com/OneGov/onegov-cloud/compare/196ff526a9^...3c6edf9228)

### Pas

##### Import data.

`Feature` | [OGC-2091](https://linear.app/onegovcloud/issue/OGC-2091) | [196ff526a9](https://github.com/onegov/onegov-cloud/commit/196ff526a9e3744fa7f3a64a9e0ffacc4ac93927)

## 2025.19

`2025-04-22` | [0e2daaf130...0515b72f63](https://github.com/OneGov/onegov-cloud/compare/0e2daaf130^...0515b72f63)

### Feriennet

##### Cancellation conditions in booking mail

`Feature` | [PRO1375](#PRO1375) | [0e2daaf130](https://github.com/onegov/onegov-cloud/commit/0e2daaf1309b7059ba2a781ebe7f11a7730fa9c3)

### Form

##### Increases default filesize for Upload to 100MB.

The comment regarding the filesize was referring to an
earlier implementation and probably no longer valid.

`Bugfix` | [OGC-2177](https://linear.app/onegovcloud/issue/OGC-2177) | [24ee549f89](https://github.com/onegov/onegov-cloud/commit/24ee549f892c8414c7070349c2c7fac04d438aea)

### Landsgemeinde

##### Navigation between assembly items

Add buttons for navigating between assembly items

`Feature` | [OGC-2198](https://linear.app/onegovcloud/issue/OGC-2198) | [f69359a71f](https://github.com/onegov/onegov-cloud/commit/f69359a71fcd27121caaccd89348c46a8df54b30)

### Org

##### Adds ticket tags with optional attached meta data

`Feature` | [OGC-2186](https://linear.app/onegovcloud/issue/OGC-2186) | [278928a937](https://github.com/onegov/onegov-cloud/commit/278928a937d7ff30df505e87428b11e53ba071af)

##### Adds copy/paste functionality for availability periods

`Feature` | [OGC-2202](https://linear.app/onegovcloud/issue/OGC-2202) | [f663a72fd4](https://github.com/onegov/onegov-cloud/commit/f663a72fd4ba5de225e277808b45c9122a6265d6)

##### Fixes crash when event filters are enabled without defining any

`Bugfix` | [ea5aafc7bb](https://github.com/onegov/onegov-cloud/commit/ea5aafc7bbfd4b3f6d559d67e3b54e440fc33fac)

## test

`2025-04-17` | [9c3aee5da3...c5f31f5611](https://github.com/OneGov/onegov-cloud/compare/9c3aee5da3^...c5f31f5611)

### Core

##### Switches Redis cache serialization over to MessagePack

`Feature` | [OGC-1893](https://linear.app/onegovcloud/issue/OGC-1893) | [b33e6c99a9](https://github.com/onegov/onegov-cloud/commit/b33e6c99a98040b05efc03099532f483a519a8b3)

### Feriennet

##### Display quotes in mail subjects correctly

`Bugfix` | [PRO-1297](https://linear.app/projuventute/issue/PRO-1297) | [9eb742296b](https://github.com/onegov/onegov-cloud/commit/9eb742296b21b8bcdb0c421a0e4b4a40bd9c3aaf)

### Intranet

##### Fixes anonymous user permissions

`Bugfix` | [SEA-1790](https://linear.app/seantis/issue/SEA-1790) | [c935dc299f](https://github.com/onegov/onegov-cloud/commit/c935dc299f47fbf332e3a682de3b81ae2b5563cd)

### Landsgemeinde

##### Change Label for audio

`Feature` | [OGC-2194](https://linear.app/onegovcloud/issue/OGC-2194) | [aa1339ba34](https://github.com/onegov/onegov-cloud/commit/aa1339ba34a0a7057e2f53215615d373a5b3f2ed)

### Org

##### Fixes potential `request_cached` issues in hourly maintenance tasks

Modifying `app.org` without immediate `flush` means `maybe_merge` can
fail. So it is more robust to factor the update to the end of the
cronjob after all the other things have been done.

`Bugfix` | [03d275054d](https://github.com/onegov/onegov-cloud/commit/03d275054d8c41bdcb40c45739ac46d4f2f25448)

### Town6

##### Option to display breadcrumbs via parameters in iframe

`Feature` | [OGC-2175](https://linear.app/onegovcloud/issue/OGC-2175) | [72113ad510](https://github.com/onegov/onegov-cloud/commit/72113ad510e1c71cec926498bb7cec0a86c8ec2c)

## 2025.18

`2025-04-11` | [a149dc874d...3a75844229](https://github.com/OneGov/onegov-cloud/compare/a149dc874d^...3a75844229)

### Agency

##### Suppress VAT settings

`Bugfix` | [NONE](#NONE) | [21362a6973](https://github.com/onegov/onegov-cloud/commit/21362a6973f8e1d1970e85dae70c14a590889c54)

### Feriennet

##### Hide ticket archive options for feriennet

`Feature` | [PRO-1386](https://linear.app/projuventute/issue/PRO-1386) | [f534636992](https://github.com/onegov/onegov-cloud/commit/f534636992a82088fc6423caa1ecdf6b940ba338)

##### Add field for SwissPass ID

`Feature` | [PRO-1388](https://linear.app/projuventute/issue/PRO-1388) | [5949eba81c](https://github.com/onegov/onegov-cloud/commit/5949eba81c3cf40584aba9740be76fc858398da7)

##### Remove Logo in Mail Header

`Bugfix` | [PRO-1362](https://linear.app/projuventute/issue/PRO-1362) | [3b08b37994](https://github.com/onegov/onegov-cloud/commit/3b08b379942a6f80e710ec9f32b6e4387d4c305c)

### Fsi

##### Ensure the six year intervall gets checked everywhere

`Bugfix` | [b05f2640a7](https://github.com/onegov/onegov-cloud/commit/b05f2640a77cf562794b7b6c5a2ce8120beda553)

### Landsgemeinde

##### Rename Audio ZIP

`Feature` | [OGC-2194](https://linear.app/onegovcloud/issue/OGC-2194) | [293a30e2f1](https://github.com/onegov/onegov-cloud/commit/293a30e2f17d2efb00c73fd02e1542aea433c68a)

### Org

##### Improve dashboard configuration

`Feature` | [OGC-1528](https://linear.app/onegovcloud/issue/OGC-1528) | [80cf9f7610](https://github.com/onegov/onegov-cloud/commit/80cf9f76103eb5329e5e196378897e6a60d5afc4)

##### Adds optional immediate ticket notifications for all ticket types

`Feature` | [OGC-2124](https://linear.app/onegovcloud/issue/OGC-2124) | [650f306032](https://github.com/onegov/onegov-cloud/commit/650f3060328a7dd8014b528f69bef2e0bb9cda39)

##### Adds the ability for resources to be organized into subgroups

`Feature` | [OGC-2021](https://linear.app/onegovcloud/issue/OGC-2021) | [8431ad8d0d](https://github.com/onegov/onegov-cloud/commit/8431ad8d0d7508ee214e58e90bb86b99d3671edf)

##### Improves support for series-reservations using find your spot

`Feature` | [OGC-2023](https://linear.app/onegovcloud/issue/OGC-2023) | [1781c0fd97](https://github.com/onegov/onegov-cloud/commit/1781c0fd970824c760b3c91240363746facb0686)

##### Scheduled daily newsletter

Add option for a scheduled daily newsletter.

`Feature` | [OGC-2217](https://linear.app/onegovcloud/issue/OGC-2217) | [c104a256f1](https://github.com/onegov/onegov-cloud/commit/c104a256f1c95da8f11b904509280b664eda88ab)

##### Rename rules and allocations

`Feature` | [OGC-2168](https://linear.app/onegovcloud/issue/OGC-2168) | [1f1f981a74](https://github.com/onegov/onegov-cloud/commit/1f1f981a7455e8fa90ad4046057cddcd32cab8c9)

### Reservation

##### Fixes price/hour calculation dropping decimal fractions.

This only occurred when the reservation duration wasn’t a whole hour
e.g., 1.5 hours was truncated to 1.0 hour.

`Bugfix` | [OGC-2152](https://linear.app/onegovcloud/issue/OGC-2152) | [cac7125206](https://github.com/onegov/onegov-cloud/commit/cac71252065e4293d790cd406e0896eb80a784fd)

### Search

##### Support phone number search (Agency, Org, Town6)

`Feature` | [OGC-2108](https://linear.app/onegovcloud/issue/OGC-2108) | [a149dc874d](https://github.com/onegov/onegov-cloud/commit/a149dc874d74c2066f2cfe2979e04402079cc2b6)

##### Returns the last change date of news items using the published_or_created attribute to lower priority of older news items (in favor for topics)

`Feature` | [OGC-2180](https://linear.app/onegovcloud/issue/OGC-2180) | [f21afb58e7](https://github.com/onegov/onegov-cloud/commit/f21afb58e766a75b26c64ab21e17a06d8208f3ab)

## 2025.17

`2025-04-04` | [1615b9b227...bb53914fba](https://github.com/OneGov/onegov-cloud/compare/1615b9b227^...bb53914fba)

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

