# Changes

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

## 2021.64

`2021-07-07` | [24957f62a8...8f423f4785](https://github.com/OneGov/onegov-cloud/compare/24957f62a8^...8f423f4785)

### Org

##### Improves message sending for tickets and forms

- Adds Email message form to form registration windows
- Adds /ticket-settings to skip ticket closing emails
- Adds batch cancellation for attendees of form registration windows
- Applies for town6 as well

`Feature` | [SEA-379](https://linear.app/seantis/issue/SEA-379) | [1748d18bad](https://github.com/onegov/onegov-cloud/commit/1748d18bad7f6bba9cb31131d479178a1a85b351)

##### Adds bullet list to contact panel

- Changes contact_html and adds a class to ul if the input contains '-'.
- Adds md explanation to contact form field
- applies for town6 as well

`Feature` | [SEA-430](https://linear.app/seantis/issue/SEA-430) | [b08f2be09f](https://github.com/onegov/onegov-cloud/commit/b08f2be09f5c11e4d9b425245660919ad22121fc)

## 2021.63

`2021-07-05` | [8bc8876629...efee5c2710](https://github.com/OneGov/onegov-cloud/compare/8bc8876629^...efee5c2710)

### Agency

##### Show full breadcrumb navigation.

`Feature` | [STAKABS-26](https://kt-bs.atlassian.net/browse/STAKABS-26) | [6094289084](https://github.com/onegov/onegov-cloud/commit/6094289084b4b9c580bb47a5cb0a2fe3c99fd639)

### Org

##### Adds ellipsis to typeahead.

`Feature` | [STAKABS-29](https://kt-bs.atlassian.net/browse/STAKABS-29) | [42eacf219d](https://github.com/onegov/onegov-cloud/commit/42eacf219df3740d0ac0b6829c0edbe0c86878c7)

## 2021.62

`2021-06-30` | [b0e5d8eb3d...97989eb6fb](https://github.com/OneGov/onegov-cloud/compare/b0e5d8eb3d^...97989eb6fb)

### Agency

##### Show function in organisations overview.

`Feature` | [STAKABS-28](https://kt-bs.atlassian.net/browse/STAKABS-28) | [f95e9cef90](https://github.com/onegov/onegov-cloud/commit/f95e9cef9069c6952129c0d4f0ea371fbde48f68)

### Election Day

##### Fix embedded vote views and make them more robust.

`Bugfix` | [df405aa72f](https://github.com/onegov/onegov-cloud/commit/df405aa72f65d24ec506e5a7f23e3f65c4de429e)

### Event

##### Fix virtual occurence being None if event is still far from today.

`Bugfix` | [1506e8e05f](https://github.com/onegov/onegov-cloud/commit/1506e8e05f597e1345d794b12feba4ea8627d1b9)

### Feriennet

##### Fixes empty transaction tid's from xml matching paid transactions without tid

`Bugfix` | [23b6f0991d](https://github.com/onegov/onegov-cloud/commit/23b6f0991d26a883b4032157d05ada58a5bedf1c)

### Org

##### Adds export views for payments (and tickets)

`Feature` | [SEA-428](https://linear.app/seantis/issue/SEA-428) | [b78b88a419](https://github.com/onegov/onegov-cloud/commit/b78b88a41949ed4a4b63ed2a758302fd1e2445b9)

##### Adds export view for payments

Exports manual and stripe payments with ticket information.

`Feature` | [SEA-428](https://linear.app/seantis/issue/SEA-428) | [fd0ebcef42](https://github.com/onegov/onegov-cloud/commit/fd0ebcef42e3f01bfc08ed418d6a38b402652c7e)

##### Adds ticket deletion feature (incl. town6)

- Only applies for decided and closed tickets
- Delete Button on a single ticket
- Batch Deletion on the tickets table with confirmation modal
- Adds modal macro to town6

`Feature` | [SEA-378](https://linear.app/seantis/issue/SEA-378) | [08007f1b8a](https://github.com/onegov/onegov-cloud/commit/08007f1b8a91ba94adb1cf78c4d6298f28d0868c)

##### Adds ticket message when changing payment amount

`Feature` | [26d0343e53](https://github.com/onegov/onegov-cloud/commit/26d0343e53de45da11a470d2db2d04dde52211d1)

##### Improves external links integration

- Adds Access section to external link forms
- Adds delete button to edit view

`Other` | [5f5f454c11](https://github.com/onegov/onegov-cloud/commit/5f5f454c11541405273df15b84e20451ec654824)

## 2021.61

`2021-06-23` | [8f72c8071f...59aa2da559](https://github.com/OneGov/onegov-cloud/compare/8f72c8071f^...59aa2da559)

### Agency

##### Display individual links to all parent agencies of a membership.

`Feature` | [STAKABS-30](https://kt-bs.atlassian.net/browse/STAKABS-30) | [8f72c8071f](https://github.com/onegov/onegov-cloud/commit/8f72c8071f5e7890a66c18d324b9da5edab23a21)

### Search

##### Add a CLI argument to fail on reindexing errors.

`Feature` | [455a4c6463](https://github.com/onegov/onegov-cloud/commit/455a4c6463a853649763bcf90dc3b04302a86057)

## 2021.60

`2021-06-21` | [5ca599442b...ff0ec616f5](https://github.com/OneGov/onegov-cloud/compare/5ca599442b^...ff0ec616f5)

### Agency

##### Add dedicated views for sorting.

`Feature` | [5239cb98f6](https://github.com/onegov/onegov-cloud/commit/5239cb98f6529141f1016cef05da17e25658f352)

### Fsi

##### Adapts ldap sync for teachers

- maps organisation by ldap base and filters
- adapts login for teachers
- adds helper class to query from config (json) for ldap sync

`Other` | [FSI-2](https://kanton-zug.atlassian.net/browse/FSI-2) | [3769935af9](https://github.com/onegov/onegov-cloud/commit/3769935af921df1639daa21a96a324695ec813d0)

### Gazette

##### Fixes SOGC importer.

`Bugfix` | [842352cd19](https://github.com/onegov/onegov-cloud/commit/842352cd19dae4a5912408e40084a9ce12cbcfc4)

## 2021.59

`2021-06-16` | [90f7a384b6...47f659af71](https://github.com/OneGov/onegov-cloud/compare/90f7a384b6^...47f659af71)

### Agency

##### Improve styling of memberships.

`Other` | [STAKABS-27](https://kt-bs.atlassian.net/browse/STAKABS-27) | [82f59fdfce](https://github.com/onegov/onegov-cloud/commit/82f59fdfce82d7ff3be518454d589ea9ca53557f)

### Feriennet

##### Fixes export of invoice items

Prevents double entries by joining on activity and invoice references.

`Bugfix` | [f3caf5e2f7](https://github.com/onegov/onegov-cloud/commit/f3caf5e2f7cff8734054f0705966fb303f2c4e3f)

### Winterthur

##### Adapts UI for multi missions

- Make time field required
- Always display correct time
- Remove mission count from /mission-reports table

`Other` | [673cf13b7b](https://github.com/onegov/onegov-cloud/commit/673cf13b7b55738536554cedf022e7f4d1576561)

## 2021.58

`2021-06-15` | [5efda0b90f...d8ebec8a12](https://github.com/OneGov/onegov-cloud/compare/5efda0b90f^...d8ebec8a12)

### Election Day

##### Show when the last update date on the upload forms.

`Feature` | [ZW-320](https://kanton-zug.atlassian.net/browse/ZW-320) | [e43a5de27b](https://github.com/onegov/onegov-cloud/commit/e43a5de27b2ea0b230776abfe547ec1d7ca8c211)

##### Show the last notifications on the notification screens.

`Feature` | [ZW-320](https://kanton-zug.atlassian.net/browse/ZW-320) | [b2abe8b3de](https://github.com/onegov/onegov-cloud/commit/b2abe8b3de39eb84dbd32be83986e47042ae6f3b)

## 2021.57

`2021-06-14` | [49f8a81daa...8961c85922](https://github.com/OneGov/onegov-cloud/compare/49f8a81daa^...8961c85922)

### Election Day

##### Improve widgets.

- Candidates chart: Add option for all/only elected.
- Candidates chart: Add filter for list/party names.
- Candidates table: Add filter for list/party names.
- Lists chart: Add filter for list/party names.
- Lists table: Add filter for list/party names.
- Counted Entities: Hide expats.
- Add a candidate results by entities table for majorz elections.

`Feature` | [426c0ea062](https://github.com/onegov/onegov-cloud/commit/426c0ea06231c724e6dc5949e54c961a6f268581)

##### Show turnouts for votes.

`Feature` | [c51dd2c5fc](https://github.com/onegov/onegov-cloud/commit/c51dd2c5fc7eb8db338435ab2a852f789dc0d45c)

### Org

##### Adds setting to auto-close FRM tickets for FormSubmissions

- Adds choice of admins in /ticket-settings that handles
auto-closing tickets

`Feature` | [SEA-376](https://linear.app/seantis/issue/SEA-376) | [49f8a81daa](https://github.com/onegov/onegov-cloud/commit/49f8a81daa2c3f7442b3425ce6e9ed3f20e22fe9)

##### Adds external link model

External links can be mixed in other collection views. It features a `member_of` attribute that denotes the collection name it should appear in.
Adds such links to the collection on `/forms`. Also applies for town6.

`Feature` | [SEA-382](https://linear.app/seantis/issue/SEA-382) | [00b7d22113](https://github.com/onegov/onegov-cloud/commit/00b7d22113d21fc5454375da7b36e615a9359f83)

##### Adds external link model

External links can be mixed in other collection views. It features a `member_of` attribute that denotes the collection name it should appear in.
Adds such links to the collection on `/forms`. Also applies for town6.

`Feature` | [SEA-382](https://linear.app/seantis/issue/SEA-382) | [990f2f11bb](https://github.com/onegov/onegov-cloud/commit/990f2f11bb9cf176fa5ca685c492863ece4fede5)

##### Adds qr-code endoint and QrCodeLink Element

A clickable link that sends an url as payload to the qr-endpoint and shows
the Qr Code in a modal.

Adds Qr link to editbar on /form/{name} for managers.

`Feature` | [SEA-380](https://linear.app/seantis/issue/SEA-380) | [937c7266e3](https://github.com/onegov/onegov-cloud/commit/937c7266e3d3b621185c506f1c6f9e185bcd97e7)

##### Adds edit button for payment amount in ticket view

`Feature` | [SEA-360](https://linear.app/seantis/issue/SEA-360) | [df815ed43b](https://github.com/onegov/onegov-cloud/commit/df815ed43b47ffdd51cb04462b56fc5b9f7093b2)

## 2021.56

`2021-06-07` | [d8fadefb86...e2836955ce](https://github.com/OneGov/onegov-cloud/compare/d8fadefb86^...e2836955ce)

### Core

##### Adds a shell command.

`Feature` | [eb9048e73c](https://github.com/onegov/onegov-cloud/commit/eb9048e73c8ac3b00b3bebfd7a8d64bc027d8112)

### Form

##### Make radio field renderer more robust

`Feature` | [c263089438](https://github.com/onegov/onegov-cloud/commit/c2630894386b3e0ea3a9d6b3ee4c0f99fb59eff1)

##### Adds https to empty url input fields

`Other` | [SEA-313](https://linear.app/seantis/issue/SEA-313) | [f034646fdb](https://github.com/onegov/onegov-cloud/commit/f034646fdb5a16be04998c94ad8694b783822710)

### Org

##### Changes newsletter confirm mail end text (incl. Town6)

- Remove best regards
- removes sender

`Other` | [SEA-359](https://linear.app/seantis/issue/SEA-359) | [69fcb45fe9](https://github.com/onegov/onegov-cloud/commit/69fcb45fe9e399b7efb7ec248e949ec4d6f61441)

##### Adds working link check for internal links

Requests internal urls with ajax calls.

`Improvement` | [SEA-331](https://linear.app/seantis/issue/SEA-331) | [67b24f7526](https://github.com/onegov/onegov-cloud/commit/67b24f75269916d5793a51d213d8e7a8bb63c20c)

### Ticket

##### Adds translations for handler codes

Render a better translation for each handler code if it is used by the app and translations exist.

`Feature` | [SEA-364](https://linear.app/seantis/issue/SEA-364) | [085924de20](https://github.com/onegov/onegov-cloud/commit/085924de20b2cf30e27cd5577f48df966c26bc95)

### Town6

##### Reduce height of form field people

`Feature` | [SEA-361](https://linear.app/seantis/issue/SEA-361) | [644a67e676](https://github.com/onegov/onegov-cloud/commit/644a67e67636349691efc17950480a980eecfc4b)

##### Adds title and hide-title to partners widget

`Feature` | [SEA-373](https://linear.app/seantis/issue/SEA-373) | [a1bcdb09db](https://github.com/onegov/onegov-cloud/commit/a1bcdb09dbb4a1b6729e9cb50e8fa9dd0c3661b4)

## 2021.55

`2021-05-31` | [e42dc76114...a7b04bb8e2](https://github.com/OneGov/onegov-cloud/compare/e42dc76114^...a7b04bb8e2)

## 2021.54

`2021-05-27` | [0f1e7e0776...a714dceda7](https://github.com/OneGov/onegov-cloud/compare/0f1e7e0776^...a714dceda7)

### Election Day

##### Improves screen widgets.

- Adds a generic text and logo widget
- Adds map widgets for votes
- Allows to set classes to widgets
- Allows to limit candidates and list charts

`Other` | [0a90662330](https://github.com/onegov/onegov-cloud/commit/0a90662330308eaafe0e9e39553b42929c361cd3)

### Org

##### Fixes user group form throwing an error for forms with hyphens.

`Bugfix` | [fd4637a07d](https://github.com/onegov/onegov-cloud/commit/fd4637a07de486aeae4d9ab6c517c8510e3caebc)

## 2021.53

`2021-05-26` | [30d9fb132b...be09de2c39](https://github.com/OneGov/onegov-cloud/compare/30d9fb132b^...be09de2c39)

### Feriennet

##### Adds WUP App banner DE only

Shows german banner version for all languages.

`Feature` | [FER-958](https://issues.seantis.ch/browse/FER-958) | [c05ea64481](https://github.com/onegov/onegov-cloud/commit/c05ea6448111adea2142c85817f0562bcea324a0)

### Fsi

##### Handle inactive users

- adds inactive field to attendee
- set users missing in ldap to inactive
- filter inactive attendees from some views

`Feature` | [FSI-45](https://kanton-zug.atlassian.net/browse/FSI-45) | [33788f532b](https://github.com/onegov/onegov-cloud/commit/33788f532ba35537644f1c928a0ddf189b100b60)

### Org

##### Add hashtag filter to news.

`Feature` | [SEA-250](https://linear.app/seantis/issue/SEA-250) | [d6813417d7](https://github.com/onegov/onegov-cloud/commit/d6813417d77d9c9f810ce0be7244445c0867dd0e)

### Town6

##### Fixes access hint in UI on path /forms

`Bugfix` | [SEA-335](https://linear.app/seantis/issue/SEA-335) | [617e32254e](https://github.com/onegov/onegov-cloud/commit/617e32254e53291eff664eb12555a509b45cc11a)

### Winterthur

##### Extends mission reports with type and mission count

`Feature` | [001072616e](https://github.com/onegov/onegov-cloud/commit/001072616e4036cbdb353608009e0fa9c5955e77)

## 2021.52

`2021-05-21` | [173c481049...2eb3f14319](https://github.com/OneGov/onegov-cloud/compare/173c481049^...2eb3f14319)

### Ballot

##### Add limit parameter to election compound list results.

`Feature` | [1e2d51d9a1](https://github.com/onegov/onegov-cloud/commit/1e2d51d9a16e3bee1e460c9b00c142f754906388)

### Core

##### Allow linking with additional query parameters.

`Feature` | [c801b0ed2b](https://github.com/onegov/onegov-cloud/commit/c801b0ed2b7d782e207ac87e0c305d1b69f33c06)

### Form

##### Allow MultiCheckboxFieldRenderer to render unkown or outdated data.

`Bugfix` | [173c481049](https://github.com/onegov/onegov-cloud/commit/173c481049c4a80fc2c4c6fa42cb9a10da870a16)

### Town6

##### Move login from header to footer.

`Other` | [SEA-345](https://linear.app/seantis/issue/SEA-345) | [3c5dd81156](https://github.com/onegov/onegov-cloud/commit/3c5dd81156313245ce7767ce36c3905370d6b13f)

##### Show full date in news.

`Other` | [SEA-344](https://linear.app/seantis/issue/SEA-344) | [4c84a0fdf7](https://github.com/onegov/onegov-cloud/commit/4c84a0fdf7d9ebb57891e7696df9e68895b0602d)

##### Hide news in top navigation.

`Other` | [SEA-343](https://linear.app/seantis/issue/SEA-343) | [9c6b2cd771](https://github.com/onegov/onegov-cloud/commit/9c6b2cd77132b322850b0771dc19aacc5d53dfc0)

## 2021.51

`2021-05-19` | [8eaa83aa1c...e9cd52c898](https://github.com/OneGov/onegov-cloud/compare/8eaa83aa1c^...e9cd52c898)

### Agency

##### Use honeypots in mutuation form.

`Feature` | [SEA-288](https://linear.app/seantis/issue/SEA-288) | [4c1553ec7e](https://github.com/onegov/onegov-cloud/commit/4c1553ec7ed2dace76307f384a6d2bc914191943)

### Form

##### Add honeypot fields.

A honey pot field is hidden using CSS and therefore not visible for
users
but bots (probably). We expect this field to be empty at any
time and throw an error if provided as well as adding a log message to
optionally ban the IP.

`Feature` | [SEA-288](https://linear.app/seantis/issue/SEA-288) | [8eaa83aa1c](https://github.com/onegov/onegov-cloud/commit/8eaa83aa1cd87eb20e7f0e4eca857194b5f6508a)

### Org

##### Add honeypot extensions for form definitions.

`Feature` | [4a076451f7](https://github.com/onegov/onegov-cloud/commit/4a076451f7d96473e03d164091df3c5396c8f9e6)

##### Adds a generic text homepage widget.

`Feature` | [SEA-334](https://linear.app/seantis/issue/SEA-334) | [2ba1ee6428](https://github.com/onegov/onegov-cloud/commit/2ba1ee642858c21b3979dc575906c1920e7a5635)

##### Check for overlapping form registration windows.

`Bugfix` | [f838b92cbc](https://github.com/onegov/onegov-cloud/commit/f838b92cbcda7d07c382bcdca1fda1b9c638b3b6)

### Translatordirectory

##### Don't correct language input.

`Bugfix` | [ZW-314](https://kanton-zug.atlassian.net/browse/ZW-314) | [f380853e13](https://github.com/onegov/onegov-cloud/commit/f380853e13dac0b726541509ba06e8cc587c9291)

## 2021.50

`2021-05-13` | [f767eccb86...ab32040507](https://github.com/OneGov/onegov-cloud/compare/f767eccb86^...ab32040507)

### Org

##### Adds a flush method to caches.

Invalidating a dogpile cache region only works for the current process.

`Feature` | [SEA-314](https://linear.app/seantis/issue/SEA-314) | [d40011e571](https://github.com/onegov/onegov-cloud/commit/d40011e5713f91c74cc61818f39ec5d4bf7b30e5)

## 2021.49

`2021-05-11` | [7cd3771161...c707683eae](https://github.com/OneGov/onegov-cloud/compare/7cd3771161^...c707683eae)

### Core

##### Updates dogpile.cache

Serialization and deserialization now take place within the CacheRegion so that backends may now assume string values in all cases.

`Other` | [SEA-306](https://linear.app/seantis/issue/SEA-306) | [16d92ed361](https://github.com/onegov/onegov-cloud/commit/16d92ed361f72130ff42453536ef1b0bf712692a)

##### Fixes race condition in sendmail command.

`Bugfix` | [SEA-321](https://linear.app/seantis/issue/SEA-321) | [866ed27ecb](https://github.com/onegov/onegov-cloud/commit/866ed27ecb9ac016c028d31046dd1f47e2aa2d17)

### Org

##### Add user group management.

`Feature` | [7cd3771161](https://github.com/onegov/onegov-cloud/commit/7cd37711619238c3e5092f38b04ca2ed1b6d36b7)

##### Adds permissions for tickets.

User groups have now a setting to restrain access to specific ticket
categories. If one is defined, only users within groups with that
setting has access to the tickets in that category.

`Feature` | [SEA-254](https://linear.app/seantis/issue/SEA-254) | [b901fc94c5](https://github.com/onegov/onegov-cloud/commit/b901fc94c516c4539d0127214059d8785176a6c0)

##### Adds start_date to import_reservations cli command

`Other` | [SEA-257](https://linear.app/seantis/issue/SEA-257) | [f7bb46ffde](https://github.com/onegov/onegov-cloud/commit/f7bb46ffde30bd962aafdec32821d906c3ae9d7a)

### Town6

##### Changes ContactsAndAlbumsWidget to ContactsWidget

- Adds contacts panel to initial content

`Other` | [SEA-320](https://linear.app/seantis/issue/SEA-320) | [7ed00fc816](https://github.com/onegov/onegov-cloud/commit/7ed00fc816f6b0cc0b8f04343057d40e52353877)

## 2021.48

`2021-05-03` | [bf9ae82dfd...336d7dc053](https://github.com/OneGov/onegov-cloud/compare/bf9ae82dfd^...336d7dc053)

### Town6

##### Adds header link to template

`Other` | [SEA-300](https://linear.app/seantis/issue/SEA-300) | [677352be3e](https://github.com/onegov/onegov-cloud/commit/677352be3efaf764645df5263874a52c696e68d0)

##### Display Directory Cards in flex grid

`Other` | [SEA-302](https://linear.app/seantis/issue/SEA-302) | [2e7c00779c](https://github.com/onegov/onegov-cloud/commit/2e7c00779c9fb99a358de3931359498a091dc9c5)

##### Styles albums and contacts widget

`Other` | [SEA-303](https://linear.app/seantis/issue/SEA-303) | [7d5879145d](https://github.com/onegov/onegov-cloud/commit/7d5879145d1b29e477ea205b37374c858d88a569)

## 2021.47

`2021-04-29` | [4f4f381207...184621e882](https://github.com/OneGov/onegov-cloud/compare/4f4f381207^...184621e882)

### Election Day

##### Add screens.

Screens allow to show tables, charts and other widgets for a given vote
or election in a flexible way.

`Feature` | [SEA-147](https://linear.app/seantis/issue/SEA-147) | [d3be6d7077](https://github.com/onegov/onegov-cloud/commit/d3be6d70771e0615b3373096eb2a714d2fd66055)

##### Fixes candidates chart not being displayed for intermediate results.

`Bugfix` | [4f4f381207](https://github.com/onegov/onegov-cloud/commit/4f4f381207e85e9c82b3c6be0baf21e8f4d8b009)

## 2021.46

`2021-04-27` | [5dd6c63404...f6b9143271](https://github.com/OneGov/onegov-cloud/compare/5dd6c63404^...f6b9143271)

### Org

##### Adds open graph meta tags with defaults

Meta tags can be overwritten by using layouts using the corresponding attribute: og:title -> og_title.
Applies for town6 as well.

`Feature` | [SEA-271](https://linear.app/seantis/issue/SEA-271) | [b829b72cca](https://github.com/onegov/onegov-cloud/commit/b829b72cca7ac6fea423756748ac33ea52399c75)

##### Adds open graph meta tags with defaults

Meta tags can be overwritten using the corresponding attribute in the layout: og:title -> og_title.
Applies for town6 as well.

`Feature` | [SEA-271](https://linear.app/seantis/issue/SEA-271) | [35aeaf118d](https://github.com/onegov/onegov-cloud/commit/35aeaf118da6d117a4aab21f00995f0656d784b8)

##### Adds daily-item Resource type

Adds news resource type for general purpose items that are reserved
for a whole day with multiple quantities possible per allocation.

- Adapts cli for importing legacy db
- Adds translations
- Adds the same to town6 app

`Other` | [53fe4cde0a](https://github.com/onegov/onegov-cloud/commit/53fe4cde0ad41c6be84bda2af2beae33b392ae2c)

## 2021.45

`2021-04-23` | [db4286be42...a05fa442cd](https://github.com/OneGov/onegov-cloud/compare/db4286be42^...a05fa442cd)

### Election Day

##### Adds missing newline in color suggestions.

`Bugfix` | [8bc504a68c](https://github.com/onegov/onegov-cloud/commit/8bc504a68cc6c04f84a10f76e2318c0019afc38a)

### People

##### Add CLI commands for clearing, exporting and importing people.

`Feature` | [SEA-252](https://linear.app/seantis/issue/SEA-252) | [39e6a28deb](https://github.com/onegov/onegov-cloud/commit/39e6a28debaced0038eaf4f4a027eb1f2af9e127)

## 2021.44

`2021-04-21` | [374e89a420...1fc3b1a099](https://github.com/OneGov/onegov-cloud/compare/374e89a420^...1fc3b1a099)

### Core

##### Use openpyxl for XLSX, xlrd for XLS conversion to CSV.

`Other` | [SEA-101](https://linear.app/seantis/issue/SEA-101) | [f8a2f4fcf1](https://github.com/onegov/onegov-cloud/commit/f8a2f4fcf10e921e30a4465bbce44fd91f0dca14)

### Feriennet

##### Fixes end of day for period phases

Ends phases at the end of day for prebooking, booking and wishlist phase.

`Bugfix` | [FER-947](https://issues.seantis.ch/browse/FER-947) | [7f06c9ca39](https://github.com/onegov/onegov-cloud/commit/7f06c9ca3991c8fb7ca4db6a3ffccca783ac0f04)

### Org

##### Adds option to change page urls path for admins

For news and topics, adds option to change the url path independant from the page title. Works for trait link and page, but prevents changing name of the parent news item under /news.

`Feature` | [SEA-255](https://linear.app/seantis/issue/SEA-255) | [ea0e3a610f](https://github.com/onegov/onegov-cloud/commit/ea0e3a610f306c48d30fce4a160e764f0a19008a)

##### Adds admin tools for link adjustments and link checking

- Adds change-url views for Pages.
  Migrates all subpages and links to itself and subpages.
- Adds migration tool to replace a chosen old domain to the current domain
- Add link health checker fetching links in async way

`Feature` | [SEA-255](https://linear.app/seantis/issue/SEA-255) | [133e3f16c2](https://github.com/onegov/onegov-cloud/commit/133e3f16c2444047444a152b019a272ac0c302af)

## 2021.43

`2021-04-21` | [47e62bf74e...2effac2bd6](https://github.com/OneGov/onegov-cloud/compare/47e62bf74e^...2effac2bd6)

### Form

##### Adds support for FontAwesome5 in IconWidget

Fixes IconField in DirectoryForm town6.

`Bugfix` | [SEA-248](https://linear.app/seantis/issue/SEA-248) | [879ded77fd](https://github.com/onegov/onegov-cloud/commit/879ded77fd01e60ae2669064e1fa4f47ab3d235a)

### Town6

##### Adds version link to Changes.md link to footer

`Feature` | [SEA-273](https://linear.app/seantis/issue/SEA-273) | [66462f9756](https://github.com/onegov/onegov-cloud/commit/66462f9756633b4499a2f80a96f797ea057ee349)

## 2021.42

`2021-04-15` | [4d9fa2f5ff...e5d040398b](https://github.com/OneGov/onegov-cloud/compare/4d9fa2f5ff^...e5d040398b)

## 2021.41

`2021-04-15` | [28790c3ee9...dba3ab2168](https://github.com/OneGov/onegov-cloud/compare/28790c3ee9^...dba3ab2168)

## 2021.40

`2021-04-14` | [f59ab70a55...f442d02925](https://github.com/OneGov/onegov-cloud/compare/f59ab70a55^...f442d02925)

### Agencies

##### Drop support for import from plone / seantis.agencies.

`Other` | [SEA-101](https://linear.app/seantis/issue/SEA-101) | [eb7c3cf5ad](https://github.com/onegov/onegov-cloud/commit/eb7c3cf5adb0d03022a86f8262ead7943d268ebf)

### Election Day

##### Fixes translations.

`Bugfix` | [f59ab70a55](https://github.com/onegov/onegov-cloud/commit/f59ab70a5520f82eabc95217a4fc3f226c1708a0)

##### Removes possibility to create majorz election compounds.

Currently, one can define election compounds with majorz elections but
these don't contain lists results, which we display. Since such
compounds are historically possible, but are not really a use case at
the moment, we drop this feature.

`Bugfix` | [fb9c2824a7](https://github.com/onegov/onegov-cloud/commit/fb9c2824a7ef1871e3f29444408ee8f9838dae67)

### Feriennet

##### Enables favicon from /favicon-settings

`Feature` | [FER-949](https://issues.seantis.ch/browse/FER-949) | [7092439672](https://github.com/onegov/onegov-cloud/commit/7092439672f367d88c27b3579b66f8390b9ca617)

### Org

##### Opens files in news/topics in new tab based on user setting

Enables settings org.open_files_target_blank for news and topics.

`Feature` | [FER-873](https://issues.seantis.ch/browse/FER-873) | [60e29148d6](https://github.com/onegov/onegov-cloud/commit/60e29148d69ab4790e5b6ec35f1ddf5c48e71346)

##### Make people side panel expandible

`Feature` | [SEA-7](https://linear.app/seantis/issue/SEA-7) | [33a6146f0b](https://github.com/onegov/onegov-cloud/commit/33a6146f0b14af32a6c456cf2b090bf900db95b6)

### Swissvotes

##### Use openpyxl instead of xlrd.

`Other` | [SEA-101](https://linear.app/seantis/issue/SEA-101) | [b1721cd1e2](https://github.com/onegov/onegov-cloud/commit/b1721cd1e2703adc181329bf768777e04de748dd)

### Town6

##### Adds chatbot integration

Adds a first integration for a chatbot with settings available on url /chatbot-settings.

`Feature` | [SEA-163](https://linear.app/seantis/issue/SEA-163) | [e295303bd4](https://github.com/onegov/onegov-cloud/commit/e295303bd4f245dc79bac11949e5d6c322b956eb)

##### Adds progress indicator

Adds step sequence registry. Defines 3 steps for forms, event suggestions, and new directories and directory change-requests.

`Feature` | [SEA-105](https://linear.app/seantis/issue/SEA-105) | [24c69a0e37](https://github.com/onegov/onegov-cloud/commit/24c69a0e37c17eff18b68f3922a0df4b7bea5263)

## 2021.39

`2021-04-06` | [575884a9a5...c05630558a](https://github.com/OneGov/onegov-cloud/compare/575884a9a5^...c05630558a)

### Election Day

##### Adds converters to paths.

`Bugfix` | [575884a9a5](https://github.com/onegov/onegov-cloud/commit/575884a9a5726de1670b2a3a3cf053a951f31f09)

### Org

##### Enables logo in email newsletter

Adds new setting at /newsletter-settings to include homepage logo.

`Feature` | [SEA-251](https://linear.app/seantis/issue/SEA-251) | [94db9f73d1](https://github.com/onegov/onegov-cloud/commit/94db9f73d132e802752324ff0b97fe838d062ade)

##### Enables ticket notifications for all external messages

Adds option to /ticket-settings to disable sending notifications for external messages. Outvotes setting in form message-to-submitter.

`Feature` | [SEA-245](https://linear.app/seantis/issue/SEA-245) | [e0162b5636](https://github.com/onegov/onegov-cloud/commit/e0162b563690ae4b7043eff4624a7cbf4cab0c14)

### Town6

##### Adds page setting to display page lead

On topic A with child B, show the B's lead on /topics/a if enabled in the settings of B.

`Feature` | [SEA-249](https://linear.app/seantis/issue/SEA-249) | [468544435f](https://github.com/onegov/onegov-cloud/commit/468544435f5165cbd2b6bad408a314a515951028)

## 2021.38

`2021-04-01` | [a54d571901...28f8485e85](https://github.com/OneGov/onegov-cloud/compare/a54d571901^...28f8485e85)

### Election Day

##### Fixes mandates of list in election compounds counted incorrectly.

`Bugfix` | [49f2ac6f85](https://github.com/onegov/onegov-cloud/commit/49f2ac6f85d3907e0a0cd4dd29a437e5e3e47241)

### Org

##### Fixes error rendering ticket pdf summary table

- limits ticket messages to 2000 chars
- Adds suppoert for max counter display on textarea
- Fixes padding right of .message

`Bugfix` | [SEA-243](https://linear.app/seantis/issue/SEA-243) | [823ae76786](https://github.com/onegov/onegov-cloud/commit/823ae767868a88dc9e45d96a641e9905e313a6a2)

### Pdf

##### Limits trustedSchemes for reportlab

Mitigates CVE-2020-28463.

`Other` | [OPS-349](#OPS-349) | [9822f014a3](https://github.com/onegov/onegov-cloud/commit/9822f014a3562b4a5c1ccb32513477a009444f13)

### Town6

##### Fixes wrapping dates in event cards

Use abbreviations for weekdays.

`Improvement` | [SEA-244](https://linear.app/seantis/issue/SEA-244) | [5b0e4bc6aa](https://github.com/onegov/onegov-cloud/commit/5b0e4bc6aa3e72dea15c4e3d76ff9b8ea06b417b)

## 2021.37

`2021-03-30` | [52585f5d2c...51c603749f](https://github.com/OneGov/onegov-cloud/compare/52585f5d2c^...51c603749f)

## 2021.36

`2021-03-25` | [2b1f49a369...0db36afcee](https://github.com/OneGov/onegov-cloud/compare/2b1f49a369^...0db36afcee)

## 2021.35

`2021-03-24` | [d90b0247fb...a634faaf40](https://github.com/OneGov/onegov-cloud/compare/d90b0247fb^...a634faaf40)

### Org

##### Make sure field placeholder and descriptions are rendered correctly

`Bugfix` | [SEA-220](https://linear.app/seantis/issue/SEA-220) | [d90b0247fb](https://github.com/onegov/onegov-cloud/commit/d90b0247fb1a740f4f8395b4cb518cad11e8ce26)

## 2021.34

`2021-03-23` | [01c2811fad...2b4e103fb5](https://github.com/OneGov/onegov-cloud/compare/01c2811fad^...2b4e103fb5)

## 2021.33

`2021-03-23` | [f784f15bb6...6f15672fb2](https://github.com/OneGov/onegov-cloud/compare/f784f15bb6^...6f15672fb2)

### Org

##### Adds publication dates to pages (topics, news)

Makes predefined topics and news editable with constraints. Removes site-navigation setting for news.
Pages are filtered by publication and access property. Any page or news can be hidden.
Adds publication hints.

`Feature` | [SEA-179](https://linear.app/seantis/issue/SEA-179) | [f3c1724333](https://github.com/onegov/onegov-cloud/commit/f3c17243330cddef639d802c468f2cbb87e1ef69)

### Tonw6

##### Improve test coverage, minor ui fixes

`Bugfix` | [f8754b24af](https://github.com/onegov/onegov-cloud/commit/f8754b24afdbb6e788157f7e1eed8831306fc7c7)

### Town6

##### Adds focus widget

Features `image-src`, `image-url`, `hide-lead`, `hide-title`, `hide-text.

`Feature` | [SEA-18](https://linear.app/seantis/issue/SEA-18) | [490c282f4f](https://github.com/onegov/onegov-cloud/commit/490c282f4fbfbe46644bcbdffbfe0d9470bef225)

## 2021.32

`2021-03-19` | [0bcfc993fe...88af288eef](https://github.com/OneGov/onegov-cloud/compare/0bcfc993fe^...88af288eef)

### Election Day

##### Add colors to list and candidate bar charts.

`Feature` | [SEA-162](https://linear.app/seantis/issue/SEA-162) | [3f05403a28](https://github.com/onegov/onegov-cloud/commit/3f05403a2840a0471ccb4613cd74b732fe98be3d)

##### Don't export empty party panachage results.

`Bugfix` | [SEA-202](https://linear.app/seantis/issue/SEA-202) | [d0bbc71167](https://github.com/onegov/onegov-cloud/commit/d0bbc711676d21e28d75cba604a3e4c1701b4ac7)

### Form

##### Allows multi line panels.

`Feature` | [3d54946a45](https://github.com/onegov/onegov-cloud/commit/3d54946a45336a5b958c9ac1eaf91371806f918d)

## 2021.31

`2021-03-17` | [c22a982b96...9ea8a9d53e](https://github.com/OneGov/onegov-cloud/compare/c22a982b96^...9ea8a9d53e)

## 2021.30

`2021-03-17` | [7157f0f0e3...144e0bb5b4](https://github.com/OneGov/onegov-cloud/compare/7157f0f0e3^...144e0bb5b4)

### Directory

##### Improves directory migration greatly

Adds support for migration when fieldsets are removed or added. Improve test coverage for directory migration.
Fixes sql alchemy observer calling migration of entries twice when triggering the migration.

`Bugfix` | [SEA-195](https://linear.app/seantis/issue/SEA-195) | [d7a436dfff](https://github.com/onegov/onegov-cloud/commit/d7a436dfff1ad8b9d09ffa784150be91f7c9206b)

## 2021.29

`2021-03-16` | [4d722f9b3f...6e2a9a9aa5](https://github.com/OneGov/onegov-cloud/compare/4d722f9b3f^...6e2a9a9aa5)

### Org

##### Fixes embedding youtu.be links not generating iframes

`Bugfix` | [SEA-178](https://linear.app/seantis/issue/SEA-178) | [656bc95e19](https://github.com/onegov/onegov-cloud/commit/656bc95e1915addc9d4e314d39f44375615e686e)

### Town

##### Adds event limit to homepage settings

`Other` | [SEA-19](https://linear.app/seantis/issue/SEA-19) | [bcec43f330](https://github.com/onegov/onegov-cloud/commit/bcec43f3308c2bcea7bb8686683f622c072921a1)

### Town6

##### Introdcues town6 redesign

Summary:

- Top News site is now editable (only contact and address available)
- Ctrl+Shift+F keyboard shortcut to open search
- Customizable homepage structure (like in org)
- Colors neutral, gray and primary can be chosen in homepage widgets as background
- Sticky editbar for constant visibility
- Nested side navigation with all layers with sorting
- New sidepanel for /news and /topics page showing address and contact
- Contact panel on the right is always shown for news and topics since the address is always displayed
- improved auto-opening menues
- improved mobile-friendliness (e.g. ticket table)
- improved globals toolbar with some animations

`Feature` | [SEA-131](https://linear.app/seantis/issue/SEA-131) | [a3af64722f](https://github.com/onegov/onegov-cloud/commit/a3af64722f603f4c5ca81f7b7eeb4f26867bddcd)

##### Adds option to display partners on all pages

- Hide it for admins in order not to clutter the page

`Other` | [df9dc9f9ee](https://github.com/onegov/onegov-cloud/commit/df9dc9f9ee57445cad3e3229a325e21d4be2f817)

##### Adds option to display partners on all pages

- Hide it for admins in order not to clutter the page

`Other` | [29979c0681](https://github.com/onegov/onegov-cloud/commit/29979c0681787bac4a1f870c8dabe5885134fd09)

##### Adds option to display partners on all pages

- Hide it for admins in order not to clutter the page

`Other` | [9d6a9135be](https://github.com/onegov/onegov-cloud/commit/9d6a9135bebade37332ba5e329a1fc952175c1f6)

## 2021.28

`2021-03-12` | [b16f503db2...eab8ec4369](https://github.com/OneGov/onegov-cloud/compare/b16f503db2^...eab8ec4369)

### Election Day

##### Invalidate pages cache after modifying elections and votes.

`Bugfix` | [SEA-184](https://linear.app/seantis/issue/SEA-184) | [93b6863c91](https://github.com/onegov/onegov-cloud/commit/93b6863c91d5540f1fd45b42086bbd6e23fc9a2c)

## 2021.27

`2021-03-11` | [783a05f22d...6f77624b93](https://github.com/OneGov/onegov-cloud/compare/783a05f22d^...6f77624b93)

### Election Day

##### Adds nice error pages in case PDF and SVG files are not ready yet.

`Feature` | [SEA-182](https://linear.app/seantis/issue/SEA-182) | [cf5febc17a](https://github.com/onegov/onegov-cloud/commit/cf5febc17aca0b40f4846b3ce977ce770b05721b)

### Org

##### Improves directory import and export

Fixes MissingColumnsError with import using csv/xlsx formats and some characters in labels.
Adds tests for all formats for the roundtrip.

`Bugfix` | [ff6ba08b35](https://github.com/onegov/onegov-cloud/commit/ff6ba08b35be708f9ab859150767e199a94f938e)

## 2021.26

`2021-03-10` | [640f8b1b67...cd35dde238](https://github.com/OneGov/onegov-cloud/compare/640f8b1b67^...cd35dde238)

### Org

##### Adds option to disable news

Disables the news view and hides the navigation entry.

`Feature` | [SEA-108](https://linear.app/seantis/issue/SEA-108) | [204bb7e759](https://github.com/onegov/onegov-cloud/commit/204bb7e759e816ea3ad5ee0dd7665332ce046c96)

##### Improves submissions of directories (submitter info)

Adds option on directory to include additional fields to be filled out by
a submitter. New submissions and change-request can be made if the url is known.
Adds additional fields to ticket pdf and ticket view.

`Feature` | [SEA-102](https://linear.app/seantis/issue/SEA-102) | [d0bf415993](https://github.com/onegov/onegov-cloud/commit/d0bf4159934100fb3c1f1d7edea257d0de57aa3d)

##### Improves directory export with filter panel

`Feature` | [eb0aacba50](https://github.com/onegov/onegov-cloud/commit/eb0aacba508759cf40d208b1b357d0cd27f24436)

## 2021.25

`2021-03-01` | [dd199312fb...70b85a9b97](https://github.com/OneGov/onegov-cloud/compare/dd199312fb^...70b85a9b97)

### Election Day

##### Adds missing pagination in election archive search.

`Bugfix` | [179d4513ab](https://github.com/onegov/onegov-cloud/commit/179d4513abe4c8f62a51fa45a2f9e60b19b30d1b)

## 2021.24

`2021-02-25` | [35fac7f40f...b8d872e9cd](https://github.com/OneGov/onegov-cloud/compare/35fac7f40f^...b8d872e9cd)

### Org

##### Adds default value for homepage left header color

Fixes issue for browsers not using default by themselves (IE11).

`Bugfix` | [2188aaa7fa](https://github.com/onegov/onegov-cloud/commit/2188aaa7face029ff760683fb901ace3b571dd2d)

### Swissvotes

##### Sort posters by links.

`Bugfix` | [VOTES-102](https://issues.seantis.ch/browse/VOTES-102) | [511c1c875a](https://github.com/onegov/onegov-cloud/commit/511c1c875abe8817696126185b8d71b8c7d3958e)

##### Fix vote attachments fallback URLs.

`Bugfix` | [VOTES-102](https://issues.seantis.ch/browse/VOTES-102) | [5a9d001dcf](https://github.com/onegov/onegov-cloud/commit/5a9d001dcf32379250ffe8a5272479cc2c92d080)

## 2021.23

`2021-02-16` | [9a6179524e...1c525760cf](https://github.com/OneGov/onegov-cloud/compare/9a6179524e^...1c525760cf)

### Swissvotes

##### Fixes various minor bugs.

`Bugfix` | [402a3c117e](https://github.com/onegov/onegov-cloud/commit/402a3c117ea05b342c91bad17cbc2e8fe4d83fe5)

## 2021.22

`2021-02-15` | [c025d2954e...a1d5d27ced](https://github.com/OneGov/onegov-cloud/compare/c025d2954e^...a1d5d27ced)

### Swissvotes

##### Adds Die Mitte.

`Feature` | [VOTES-98](https://issues.seantis.ch/browse/VOTES-98) | [2aa9ed9883](https://github.com/onegov/onegov-cloud/commit/2aa9ed98839a3b9b71365eb946beb64164d79257)

##### Add aditional post-vote poll dataset formats.

`Feature` | [VOTES-99](https://issues.seantis.ch/browse/VOTES-99) | [10c20c1026](https://github.com/onegov/onegov-cloud/commit/10c20c1026b5c6c6e83c3c46c4612fa9c07a07ed)

##### Add additional post-vote poll codebook format.

`Feature` | [VOTES-100](https://issues.seantis.ch/browse/VOTES-100) | [8600ae7e8d](https://github.com/onegov/onegov-cloud/commit/8600ae7e8df2b95ee35af6804a48f9506b138d87)

##### Add technical report of the post-vote poll.

`Feature` | [VOTES-101](https://issues.seantis.ch/browse/VOTES-101) | [17aa9d45e3](https://github.com/onegov/onegov-cloud/commit/17aa9d45e32bcdf5c020b9dcd180958a16a4868d)

## 2021.21

`2021-02-11` | [13aae131a1...a278187144](https://github.com/OneGov/onegov-cloud/compare/13aae131a1^...a278187144)

### Org

##### Adds Qr-Code to ticket pdf

`Feature` | [13aae131a1](https://github.com/onegov/onegov-cloud/commit/13aae131a1da6afd43266369671cfb5180ee7ab9)

### Swissvotes

##### Add slider to frontpage.

`Feature` | [VOTES-79](https://issues.seantis.ch/browse/VOTES-79) | [abaf934683](https://github.com/onegov/onegov-cloud/commit/abaf934683e4ab8fa0bf4c463df23a862af6eb43)

## 2021.20

`2021-02-10` | [eb99ea1ef8...52896c2160](https://github.com/OneGov/onegov-cloud/compare/eb99ea1ef8^...52896c2160)

### Form

##### Removes deprecated DateTimeField everywhere

`Feature` | [SEA-111](https://linear.app/seantis/issue/SEA-111) | [9f4af033d2](https://github.com/onegov/onegov-cloud/commit/9f4af033d229b53fc22046166f4961d2fa79b4bb)

### Org

##### Extends directory config to hide labels in main view

`Feature` | [SEA-92](https://linear.app/seantis/issue/SEA-92) | [eb99ea1ef8](https://github.com/onegov/onegov-cloud/commit/eb99ea1ef84535cae1652f5dc0189e2784bd1b9d)

## 2021.19

`2021-02-10` | [a1d6a50697...f6af388d87](https://github.com/OneGov/onegov-cloud/compare/a1d6a50697^...f6af388d87)

### Org

##### Improves newsletter sending (for news)

Adds preview to newsletter sending form. Adds option to choose
newsletter item text instead of the lead when sending a newsletter.

`Feature` | [SEA-109](https://linear.app/seantis/issue/SEA-109) | [67bacc49f9](https://github.com/onegov/onegov-cloud/commit/67bacc49f961c342442233b9cc7db69f500c543d)

##### Adds the form data to confirmation email in reservations

`Feature` | [SEA-112](https://linear.app/seantis/issue/SEA-112) | [c6527d2f71](https://github.com/onegov/onegov-cloud/commit/c6527d2f7100d4bb54559c1d06438fb0b2f932da)

##### Enable pick up information display for resources

Shows pick up hint if available on /ticket/../status instead of general info.

`Feature` | [SEA-97](https://linear.app/seantis/issue/SEA-97) | [97d1a480ac](https://github.com/onegov/onegov-cloud/commit/97d1a480ac2aea93472c0c80af2327ab8a79b87a)

##### Adds generic PDF's for tickets

Create PDF from (snapshotted) tickets and its messages. Does not iclude any files into the PDF.

`Feature` | [SEA-89](https://linear.app/seantis/issue/SEA-89) | [d3ea0464b2](https://github.com/onegov/onegov-cloud/commit/d3ea0464b2e4d32d70cf32107e7bc0bf8b4d8649)

### Swissvotes

##### Use thumbnails for additional poster material.

`Feature` | [VOTES-74](https://issues.seantis.ch/browse/VOTES-74) | [3d7ba8e004](https://github.com/onegov/onegov-cloud/commit/3d7ba8e004d87082967c0556d66b12101879e2f4)
