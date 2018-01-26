Changelog
---------

- Adds a generic loading animation for ic-post buttons in the editbar.
  [href]

0.20.4 (2018-01-24)
~~~~~~~~~~~~~~~~~~~

- Fixes entry link during directory migration not working.
  [href]

0.20.3 (2018-01-24)
~~~~~~~~~~~~~~~~~~~

- Shows how many entries were imported during directory import.
  [href]

- Fixes a case where an empty image field would result in an error.
  [href]

- The check password function hasn't worked in a long time -> removed.
  [href]

0.20.2 (2018-01-22)
~~~~~~~~~~~~~~~~~~~

- Fixes links wrongly transforming class attributes.
  [href]

- Adds the ability to categorise users into tags and to filter them by it.
  [href]

0.20.1 (2018-01-17)
~~~~~~~~~~~~~~~~~~~

- Various small bugfixes.
  [href]

0.20.0 (2018-01-04)
~~~~~~~~~~~~~~~~~~~

- Updates intercooler to latest release.
  [href]

- Adds the ability to submit directory entries.
  [href]

0.19.8 (2017-12-29)
~~~~~~~~~~~~~~~~~~~

- Requires Python 3.6.
  [href]

- Unifies the coordinates usage across different modules.
  [href]

0.19.7 (2017-12-22)
~~~~~~~~~~~~~~~~~~~

- Switches to onegov core's custom json module.
  [href]

0.19.6 (2017-12-19)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with the latest onegov.form release.
  [href]

- Puts visibility related options in a separate fieldset.
  [href]

0.19.5 (2017-12-14)
~~~~~~~~~~~~~~~~~~~

- Fixes redactor not working in Chrome 60+.
  [href]

- Updates fullcalendar to latest release.
  [href]

0.19.4 (2017-12-11)
~~~~~~~~~~~~~~~~~~~

- Automatically adds confirm dialogs to intercooler responses.
  [href]

- Changes the confirmation setup to be idempotent.
  [href]

0.19.3 (2017-12-11)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to trigger an intercooler request only once.
  [href]

0.19.2 (2017-12-05)
~~~~~~~~~~~~~~~~~~~

- Adds a note to the new-user e-mail to inform them about password resets.
  [href]

0.19.1 (2017-12-04)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to override the sender line in e-mails.
  [href]

0.19.0 (2017-12-01)
~~~~~~~~~~~~~~~~~~~

- Changes the long date format to include the weekday.
  [href]

- Highlights the parent link in each breadcrumb.
  [href]

0.18.5 (2017-11-30)
~~~~~~~~~~~~~~~~~~~

- Fixes required fileinput fields not working.
  [href]

0.18.4 (2017-11-23)
~~~~~~~~~~~~~~~~~~~

- Fixes intercooler requests being sent using POST instead of DELETE.
  [href]

0.18.3 (2017-11-22)
~~~~~~~~~~~~~~~~~~~

- Prefixes the page ids to avoid javascript errors.
  [href]

- Shows an error messages when an AJAX call fails, instead of showing nothing.
  [href]

- Ensures idempotence of all ticket state changes.
  [href]

0.18.1 (2017-11-20)
~~~~~~~~~~~~~~~~~~~

- Includes the version, current user and role in javascript error reports.
  [href]

0.18.0 (2017-11-20)
~~~~~~~~~~~~~~~~~~~

- Moves yubikey/user registration toggles to configuration.
  [href]

0.17.6 (2017-11-16)
~~~~~~~~~~~~~~~~~~~

- Moves password reset views to the auth model.
  [href]

0.17.5 (2017-11-16)
~~~~~~~~~~~~~~~~~~~

- Adds directories to initial org layout.
  [href]

- Hides daily ticket statistic fields from members.
  [href]

0.17.4 (2017-11-14)
~~~~~~~~~~~~~~~~~~~

- Supports X-File-Notes encoded as JSON.
  [href]

0.17.3 (2017-11-14)
~~~~~~~~~~~~~~~~~~~

- Enables <pre> tags in page text.
  [href]

0.17.2 (2017-11-09)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to manually mute ticket e-mails.
  [href]

0.17.1 (2017-11-08)
~~~~~~~~~~~~~~~~~~~

- Fixes new directories ignoring the enable_map setting.
  [href]

- Fixes timeline not loading all messages.
  [href]

- Limit the yubi key length on the form field as well.
  [href]

0.17.0 (2017-11-08)
~~~~~~~~~~~~~~~~~~~

- Adds directories, a generic way keep and present structured information.
  [href]

0.16.4 (2017-10-30)
~~~~~~~~~~~~~~~~~~~

- Fixes newsletter subject not rendering correctly.
  [href]

0.16.3 (2017-10-25)
~~~~~~~~~~~~~~~~~~~

- Fixes footer-height not working with new foundation theme release.
  [href]

0.16.2 (2017-10-19)
~~~~~~~~~~~~~~~~~~~

- Removes left-over pdb call.
  [href]

0.16.1 (2017-10-19)
~~~~~~~~~~~~~~~~~~~

- Fixes event dates being capitalized instead of titled.
  [href]

0.16.0 (2017-10-19)
~~~~~~~~~~~~~~~~~~~

- Adds a formcode snippet toolbar for formcode fields.
  [href]

0.15.4 (2017-10-13)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to pass extra parameters to the jquery datetime picker.
  [href]

0.15.3 (2017-10-12)
~~~~~~~~~~~~~~~~~~~

- Only show sliders once they can be correctly rendered.

  This improves the look of the homepage on the initial load.
  [href]

0.15.2 (2017-10-10)
~~~~~~~~~~~~~~~~~~~

- Removes leftover onegov.notices table.
  [href]

0.15.1 (2017-10-06)
~~~~~~~~~~~~~~~~~~~

- Fixes reservations not working after url change.
  [href]

- Adds the ability to use the payments table in other views.
  [href]

0.15.0 (2017-09-28)
~~~~~~~~~~~~~~~~~~~

- Consistently uses English in the urls, instead of a German/English mix.
  [href]

- Switches to onegov.search's automatic language detection.
  [href]

- Switches to onegov.file for form submission files.
  [href]

- Fixes dialog not showing for undeletable objects.
  [href]

0.14.6 (2017-08-25)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with the latest onegov.form release.
  [href]

0.14.5 (2017-08-23)
~~~~~~~~~~~~~~~~~~~

- Fixes newly created users with Yubikeys failing to login.
  [href]

0.14.4 (2017-08-03)
~~~~~~~~~~~~~~~~~~~

- Uses shared common code from onegov.form for HTML fields.
  [msom]

0.14.3 (2017-07-17)
~~~~~~~~~~~~~~~~~~~

- Adds missing German translation.
  [href]

0.14.2 (2017-07-13)
~~~~~~~~~~~~~~~~~~~

- Fixes being unable to delete a reservation if it has an associated payment.
  [href]

- Adds payment e-mail notifications triggered in tickets.
  [href]

0.14.1 (2017-07-12)
~~~~~~~~~~~~~~~~~~~

- Uses latest jquery.popupoverlay plugin release.
  [href]

- Fixes calucating the contrast of an invalid color throwing an error.
  [msom]

0.14.3 (2017-07-17)
~~~~~~~~~~~~~~~~~~~

- Adds missing German translation.
  [href]

0.14.2 (2017-07-13)
~~~~~~~~~~~~~~~~~~~

- Fixes being unable to delete a reservation if it has an associated payment.
  [href]

- Adds payment e-mail notifications triggered in tickets.
  [href]

0.14.1 (2017-07-12)
~~~~~~~~~~~~~~~~~~~

- Uses latest jquery.popupoverlay plugin release.
  [href]

- Fixes calucating the contrast of an invalid color throwing an error.
  [msom]

0.14.0 (2017-07-10)
~~~~~~~~~~~~~~~~~~~

- Adds an activity/audit log and the ability to create notes on tickets.
  [href]

0.13.1 (2017-07-05)
~~~~~~~~~~~~~~~~~~~

- No longer requires a reply-to address to send e-mails (though one still needs
  to enter one to save the org settings.)
  [href]

0.13.0 (2017-06-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to create signup links.
  [href]

0.12.0 (2017-06-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to filter users in the usermanagement view.
  [href]

- Changes is-manager/is-not-manager class to role-member, role-editor, etc.
  [href]

0.11.1 (2017-06-23)
~~~~~~~~~~~~~~~~~~~

- Depends on the latest onegov.form release which fixes a critical parsing bug.
  [href]

0.11.0 (2017-06-22)
~~~~~~~~~~~~~~~~~~~

- Upgrades to latest onegov.user release.
  [msom]

- Upgrades to latest onegov.core release.
  [msom]

0.10.0 (2017-06-21)
~~~~~~~~~~~~~~~~~~~

- Upgrades to latest onegov.core release.
  [msom]

0.9.2 (2017-06-19)
~~~~~~~~~~~~~~~~~~~

- Fixes sentry js not working.
  [href]

- Fixes a minor style issue with checkout forms.
  [href]

0.9.1 (2017-06-16)
~~~~~~~~~~~~~~~~~~~

- Adds support for sentry js.
  [href]

- Fixes number formatting not working in Python < 3.5.
  [href]

0.9.0 (2017-06-16)
~~~~~~~~~~~~~~~~~~~

- Adds credit card payments for forms and reservations.
  [href]

0.8.3 (2017-05-29)
~~~~~~~~~~~~~~~~~~~

- Fixes wrong text-links margin.
  [href]

- Fixes missing translation of "more..." link.
  [href]

0.8.2 (2017-05-17)
~~~~~~~~~~~~~~~~~~~

- Adds an esr participation number to the bank account information.
  [href]

0.8.1 (2017-05-12)
~~~~~~~~~~~~~~~~~~~

- Fixes footer margins not working.
  [href]

0.8.0 (2017-05-12)
~~~~~~~~~~~~~~~~~~~

- Introduces an improved elements model for link generation.
  [href]

0.7.3 (2017-05-11)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to define an email signature through macros.
  [href]

0.7.2 (2017-05-10)
~~~~~~~~~~~~~~~~~~~

- Gives sub-applications more ways to customize the footer.
  [href]

- Fixes performance degradation on sites with lots of toggles/dropdowns.
  [href]

0.7.1 (2017-05-08)
~~~~~~~~~~~~~~~~~~~

- Further improves the capability of the export formatter.
  [href]

0.7.0 (2017-05-05)
~~~~~~~~~~~~~~~~~~~

- Adds a generic export view and implementation using directives.
  [href]

- Improves the capability of the export formatter.
  [href]

- Gives subapplications the ability to override the ticket status text.
  [href]

0.6.2 (2017-05-04)
~~~~~~~~~~~~~~~~~~~

- Adds a payment order setting to differentiate between basic and ESR payment
  orders.
  [href]

0.6.1 (2017-05-02)
~~~~~~~~~~~~~~~~~~~

- Make search more extendable by org applications.
  [href]

0.6.0 (2017-05-02)
~~~~~~~~~~~~~~~~~~~

- Gives org applications the ability to require a complete userprofile.
  [href]

- Adds the ability to force the button toggle state through javascript.
  [href]

0.5.2 (2017-04-27)
~~~~~~~~~~~~~~~~~~~

- Ignore the case of e-mails when doing a password reset.
  [href]

0.5.1 (2017-04-11)
~~~~~~~~~~~~~~~~~~~

- Adds a beneficiary to the bank account.
  [href]

0.5.0 (2017-03-28)
~~~~~~~~~~~~~~~~~~~

- Switches to Elasticsearch 5.
  [href]

0.4.8 (2017-03-21)
~~~~~~~~~~~~~~~~~~~

- Replaces onegov.libres with onegov.reservation.
  [href]

0.4.7 (2017-03-15)
~~~~~~~~~~~~~~~~~~~

- Supports translation of ticket groups through the handler.
  [href]

- No longer throw an unrelated error when the database connection goes offline.
  [href]

- Fix signup e-mail's subject not being translated.
  [href]

- Undoes the minor style fix for boolean fields - no good solution yet.
  [href]

0.4.6 (2017-03-03)
~~~~~~~~~~~~~~~~~~~

- Fixes a minor style issues with boolean fields.
  [href]

- Adds a setting for the roles selected for the daily status e-mail.
  [href]

- Fix wrong title on homepage.
  [href]

0.4.5 (2017-03-02)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to send an instructional e-mail to new users.
  [href]

0.4.4 (2017-02-27)
~~~~~~~~~~~~~~~~~~~

- Introduces a way to define the way an org name is split into two lines.
  [href]

0.4.3 (2017-02-24)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to show a location below the map.
  [href]

- Gives child-applications the ability to show a favicon.
  [href]

- Fix button color being unreadable with light backgrounds.
  [href]

0.4.2 (2017-02-21)
~~~~~~~~~~~~~~~~~~~

- Ensures that the user's status/role can always be changed.
  [href]

- Fixes typeahead autofocus being too eager.
  [href]

- Shows realname in user-management view alongside the username.
  [href]

- Makes e-mail address in user-management view clickable.
  [href]

0.4.1 (2017-02-14)
~~~~~~~~~~~~~~~~~~~

- Fixes ticket badges rendering wrongly in IE 10.
  [href]

0.4.0 (2017-02-09)
~~~~~~~~~~~~~~~~~~~

- Add "organiser" to the search query.
  [href]

- Use onegov.core's orm cache descriptor for better, easier caching.
  [href]

- Further improve the handling of light colors.
  [href]

0.3.3 (2017-01-30)
~~~~~~~~~~~~~~~~~~~

- Shows users in the search results.
  [href]

- Adds the removal of the depot directory to the delete command.
  [href]

- Shows a warning when the elasticsearch cluster is down.
  [href]

- Improves the look of events on tablets.
  [href]

0.3.2 (2017-01-19)
~~~~~~~~~~~~~~~~~~~

- Fixes faulty css rules resulting in style issues.
  [href]

0.3.1 (2017-01-19)
~~~~~~~~~~~~~~~~~~~

- Fixes initial content not being loaed with the right encoding.
  [href]

0.3.0 (2017-01-19)
~~~~~~~~~~~~~~~~~~~

- Improves the general look of the site through a limited redesign.
  [href]

- Adds better initial content.
  [href]

- Adds an IBAN account to the settings.
  [href]

0.2.0 (2017-01-10)
~~~~~~~~~~~~~~~~~~~

- Adds a simple prediction/suggestion to the calendar if multiple reservations
  are apparently repeating.
  [href]

- Adds the ability to send daily e-mails to interested parties about scheduled
  reservations.
  [href]

- Stop sending e-mails to admins/editors if they create tickets for themselves.
  [href]

- Adds the ability to swipe through the images in the photoalbum.
  [href]

- Make sure all image elements have the width and height set.
  [href]

- Adds the ability to filter tickets by owners.
  [href]

- Show utilisation on resource occupancy view.
  [href]

- On tablets, show the reservation selection next to the calendar.
  [href]

- Show the exact creation date on each ticket.
  [href]

- Multiple people with the same name no longer cause an error in the page form.
  [href]

- Fixes custom primary color not being used for e-mails.
  [href]

- Fixes e-mail sending not working for onegov.onboarding.
  [href]

0.1.9 (2016-12-28)
~~~~~~~~~~~~~~~~~~~

- Honor the return-to parameter in the usermanagement view.
  [href]

0.1.8 (2016-12-23)
~~~~~~~~~~~~~~~~~~~

- Adds support for Webob 1.7.
  [href]

- Fixes reservation delete not working for anonymous users.
  [href]

0.1.7 (2016-12-15)
~~~~~~~~~~~~~~~~~~~

- Prevent empty pages from being printed.
  [href]

- Make sure the userprofile honors the return-to parameter.
  [href]

0.1.6 (2016-12-13)
~~~~~~~~~~~~~~~~~~~

- Adds support for PyFilesystem 2.x and Chameleon 3.x.
  [href]

0.1.5 (2016-12-01)
~~~~~~~~~~~~~~~~~~~

- Adds a 'is-logged-in' and 'is-not-logged-in' body class to all views.
  [href]

0.1.4 (2016-12-01)
~~~~~~~~~~~~~~~~~~~

- Update FontAwesome to 4.7.
  [href]

0.1.3 (2016-11-25)
~~~~~~~~~~~~~~~~~~~

- Fix datetime picker not showing the hour/minutes in the placeholder.
  [href]

- Point the default map view to the Seantis office.
  [href]

- Improve multi-line checkbox/radio-button handling.
  [href]

0.1.2 (2016-11-18)
~~~~~~~~~~~~~~~~~~~

- Adds a jquery plugin to easily toggle blocks by button.
  [href]

- Fixes userprofile data being lost on erronous input.
  [href]

- Fixes datetime/date picker weeks not starting on the region-specific day.
  [href]

- Adds a to_timezone helper function to the default layout.
  [href]

0.1.1 (2016-11-02)
~~~~~~~~~~~~~~~~~~~

- Generate links in top-navigation just like it is done in other palces.
  [href]

- Automatically skip the login view if the target url is accessable.
  [href]

0.1.0 (2016-10-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to stick certain news items to the homepage.
  [href]

- Make sure that all time input fields support input parsing.
  [href]

- Accept a wider range of values in the time input fields.
  [href]

- Fix search url being wrong after multiple searches.
  [href]

- Upgrade to latest React release.
  [href]

- Adds the ability to easily switch between resources.
  [href]

- Use auto-height for fullcalendar, mainly to improve mobile usage.
  [href]

- Upgrade to Fullcalendar 3.0.1.
  [href]

- Fixes telephone links not working in person detail view.
  [href]

- Fixes input placeholder having the wrong color in IE11.
  [href]

- Supports excel/csv/json in the events export.
  [href]

- Adds organizer to events export.
  [href]

- Dates in excel exports are now formatted in a localized manner.
  [href]

0.0.14 (2016-10-19)
~~~~~~~~~~~~~~~~~~~

- Adds a separate date_range function for dates instead of datetimes.
  [href]

0.0.13 (2016-10-11)
~~~~~~~~~~~~~~~~~~~

- Hardens all return-to links.
  [href]

- Includes the userprofile in the usermanagement view.
  [href]

- Fixes 'News' title showing up twice on the newsletter view.
  [href]

0.0.12 (2016-10-04)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with Morepath 0.16.
  [href]

- Adds the ability to easily format a date range.
  [href]

- Adds input-type:datetime support to the datetimepicker.
  [href]

0.0.11 (2016-09-29)
~~~~~~~~~~~~~~~~~~~

- Ensure that all image upload views enforce the same checks.
  [href]

- Order tags by alphabet in events view.
  [href]

0.0.10 (2016-09-22)
~~~~~~~~~~~~~~~~~~~

- Upgrade to latest onegov.core release.
  [href]

0.0.9 (2016-09-22)
~~~~~~~~~~~~~~~~~~~

- Fixes being unable to edit builtin forms.
  [href]

- Adds a ConfirmLink element which works like a DeleteLink but for POST.
  [href]

- Fixes title being shown twice on the news site.
  [href]

0.0.8 (2016-09-12)
~~~~~~~~~~~~~~~~~~~

- Fixes morepath directives not working in all cases.
  [href]

0.0.7 (2016-09-12)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to define a custom homepage through widgets.
  [href]

- Use a uuid converter for all uuid-ids to turn bad requests into 404s.
  [href]

- Adds the ability to override the initial content creation function.
  [href]

- Fixes user editing not working when yubikeys are enabled.
  [href]

0.0.6 (2016-08-31)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to manage users in a usermanagement view.
  [href]

0.0.5 (2016-08-26)
~~~~~~~~~~~~~~~~~~~

- Enables the user profile for simple members.
  [href]

- Adds the ability for new users to register themselves.
  [href]

0.0.4 (2016-08-25)
~~~~~~~~~~~~~~~~~~~

- Fixes upgrade not working in all cases.
  [href]

0.0.3 (2016-08-25)
~~~~~~~~~~~~~~~~~~~

- Possibly fixes release not working for PyPI.
  [href]

0.0.2 (2016-08-24)
~~~~~~~~~~~~~~~~~~~

- Removes dependency to itself.
  [href]

0.0.1 (2016-08-24)
~~~~~~~~~~~~~~~~~~~

- Initial Release