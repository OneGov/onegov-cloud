Changelog
---------

1.1.0 (2017-06-21)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to clone occasions.
  [href]

- Renames "Periode" to "Zeitraum" in the German translation.
  [href]

- Shows activity/attendee/booking/billing links on the user view.
  [href]

- Shows a thumbnail for each activity in the overview.
  [href]

- Adds a sponsor-banner mechanism for the bookings view.
  [href]

- Adds Pro Juventute's Google Tag Manager script.
  [href]

- Updates the initial content for future feriennet orgs.
  [href]

1.0.0 (2017-05-29)
~~~~~~~~~~~~~~~~~~~

- Removes sponsorships for now.
  [href]

0.11.1 (2017-05-17)
~~~~~~~~~~~~~~~~~~~

- Shows the ESR participation number instead of the account if selected.
  [href]

- Changes the footer/sponsorship styles.
  [href]

- Fixes export not working if the period's cost was set to None.
  [href]

0.11.0 (2017-05-12)
~~~~~~~~~~~~~~~~~~~

- The deadline is now inclusive (including the day it ends).
  [href]

- Improves the speed by which the matches view is rendered.
  [href]

- Adds platform sponsoring.
  [href]

- Adds the ability to filter activities by weekday.
  [href]

0.10.1 (2017-05-10)
~~~~~~~~~~~~~~~~~~~

- No longer hides the enroll button if the occasion is full during prebooking.
  [href]

- Don't touch the cancelled bookings during matching reset.
  [href]

- Always shows the first date of any occasion in the matching view.
  [href]

- Hides the enroll button after the wishlist, but before the booking phase.
  [href]

- Fixes bank_beneficiary on userprofile not being saved.
  [href]

- Fixes prebooking phase not starting exactly at 00:00.
  [href]

0.10.0 (2017-05-08)
~~~~~~~~~~~~~~~~~~~

- Adds a link from the matching view to the userprofile.
  [href]

- Fixes an error caused by invalid credentials.
  [href]

- Adds exports for activities, occasions, invoice items and users.
  [href]

- Adds the ability to filter overfull and cancelled occasions when matching.
  [href]

- Fixes a number of grammatical errors in German.
  [href]

- Switches to a generic enroll text that works for all children.
  [href]

- Adds support for ESR payment orders.
  [href]

- Adds more target groups to send notifications to.
  [href]

0.9.0 (2017-05-03)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to search attendees and activity organisers.
  [href]

- Forces users update their profile after login and before booking.
  [href]

- Adds the ability to manage bokings/wishes on the matching view.
  [href]

- Adds links from the matching view to the attendee and its bookings/wishes.
  [href]

- Adds the ability to filter the matching view.
  [href]

- Limits editors edit activites/occasions only in preview or proposed state.
  [href]

0.8.0 (2017-04-28)
~~~~~~~~~~~~~~~~~~~

- Forces all usernames to be in lowercase.
  [href]

- Moves the period filter further up.
  [href]

- Increases the maximum allowed block-time from 90 to 360 minutes.
  [href]

0.7.1 (2017-04-11)
~~~~~~~~~~~~~~~~~~~

- Adds a beneficiary to the bank account.
  [href]

0.7.0 (2017-03-28)
~~~~~~~~~~~~~~~~~~~

- Switches to Elasticsearch 5.
  [href]

0.6.2 (2017-03-23)
~~~~~~~~~~~~~~~~~~~

- Enable messages to attendees of cancelled occasions.
  [href]

- Fixes no error showing for the first attendee added by a member.
  [href]

0.6.1 (2017-03-21)
~~~~~~~~~~~~~~~~~~~

- Rely on latest onegov.org release.
  [href]

0.6.0 (2017-03-15)
~~~~~~~~~~~~~~~~~~~

- Removes the 'denied' state for activities.
  [href]

- Further differentiates between ticket and activity.
  [href]

- Highlights the difference beteween a non-full occasion and a cancelled one.
  [href]

- No longer cascades changes when cancelling a booking.
  [href]

- Adds an IBAN field to all user profiles.
  [href]

- Fix wishlist-count excluding blocked/denied bookings.
  [href]

- Show the available spots in the activities list.
  [href]

- Moves the admin-only filters to the top of the activity-filters list.
  [href]

- Only count the accepted bookings when looking at the booking limit.
  [href]

- Fixes matching view omitting items at random.
  [href]

0.5.1 (2017-03-03)
~~~~~~~~~~~~~~~~~~~

- Fixes the daily ticket status being sent to editors.
  [href]

- Fixes being unable to change the ticket status in the user profile.
  [href]

- Fixes the daily ticket being disabled when editing the user profile.
  [href]

0.5.0 (2017-03-02)
~~~~~~~~~~~~~~~~~~~

- Reorganises the activity filters.
  [href]

- Adds the ability to filter activities by period weeks.
  [href]

- Fixes age check not working for existing attendees.
  [href]

- Adds the ability to selectivly incrase the priority of bookings.
  [href]

- Fixes activities visibility for members.
  [href]

- No longer send e-mails to inactive users.
  [href]

- Introduces a way to define the way an org name is split into two lines.
  [href]

- Use dropdowns instead of lists for the period/username selection.
  [href]

0.4.1 (2017-02-24)
~~~~~~~~~~~~~~~~~~~

- Adds a meeting point to the occasion, a location to the activity.
  [href]

- Renames "Opening hours" into something more fitting to a Ferienpass.
  [href]

- Adds a favicon.
  [href]

- Limit the bookings count to open/accepted bookings.
  [href]

- Hides the homepage images in the settings.
  [href]

- Improves period form descriptions.
  [href]

- Restrict cancellations after matching to admins only.
  [href]

- Adds the ability to define attendee-based limits.
  [href]

- Adds the ability to set a booking deadline on the period.
  [href]

- Hide pagination if there are no accessible activities.
  [href]

0.4.0 (2017-02-21)
~~~~~~~~~~~~~~~~~~~

- Adds more fields to the user form.
  [href]

- Splits attendee name into first/last name.
  [href]

- Show a description about the process instead of the content in the activity
  ticket view.
  [href]

- Adds the ability to set the minimum time between bookings.
  [href]

- Adds the ability to exclude occasions from the overlap check.
  [href]

- Adds four new categories.
  [href]

- Adds up-front age validation for enrollments.
  [href]

- Hides the activities to non-organisers/admins if there's no active period.
  [href]

- Shows the ages, costs and number of occasions on the activities view.
  [href]

- Removes schoolclass-references from the age filters.
  [href]

- Adds the ability to print all bookings or a specific one.
  [href]

0.3.1 (2017-02-14)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to work with multiple dates per occasion.
  [href]

- Revoke access to notifications for organisers.
  [href]

- Do not show the booking button before the wishlist phase has started.
  [href]

- Adds a notes field to the attendee.
  [href]

- Add organiser to the searchable attributes of activites.
  [href]

- Fixes users being able to book occasions of unapproved activites.
  [href]

- Start caching some often used data using the orm cache descriptor.
  [href]

- Hide activites without an occasion in the active period from anonymous users.
  [href]

- Adds the ability to enter the gender of an attendee.
  [href]

- Fixes wrong operability calculation.
  [href]

0.3.0 (2017-01-30)
~~~~~~~~~~~~~~~~~~~

- Fixes wrong font for generic logo.
  [href]

- Shows the management menu for organisers again.
  [href]

0.2.2 (2017-01-19)
~~~~~~~~~~~~~~~~~~~

- Depend on latest onegov.org release.
  [href]

0.2.1 (2017-01-19)
~~~~~~~~~~~~~~~~~~~

- Depend on latest onegov.org release.
  [href]

0.2.0 (2017-01-19)
~~~~~~~~~~~~~~~~~~~

- Improve design, moving all global tools to the top.
  [href]

- Improves the initial content.
  [href]

- No longer use custom page structure and cover page content.
  [href]

- No longer send e-mails to admins if they are publishing their own activites.
  [href]

0.1.5 (2016-12-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to send e-mails manually to different sets of people.
  [href]

0.1.4 (2016-12-15)
~~~~~~~~~~~~~~~~~~~

- Adds an emergency contact to the userprofile.
  [href]

- Fixes cancelled bookings blocking new bookings.
  [href]

0.1.3 (2016-12-13)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to create invoices and to mark them as paid
  [href]

- Ensures that the number of spots on an occasion cannot be lower than
  the number of already accepted bookings.
  [jref]

- Adds the ability to cancel, reactivate and delete occasions.
  [href]

0.1.2 (2016-12-01)
~~~~~~~~~~~~~~~~~~~

- Attendees may no longer book multiple occasions of an activity.
  [href]

- Shows the total costs on the booking view.
  [href]

- Shows the price of each booking and the cost for the activity pass.
  [href]

- Adds the ability to limit the number of bookings per attendee and period.
  [href]

- Adds the ability to set the price of a booking on the period.
  [href]

- Adds the ability to change the cost of an occasion.
  [href]

0.1.1 (2016-11-25)
~~~~~~~~~~~~~~~~~~~

- Adds the ability for administrators to create a booking for someone else.
  [href]

- Adds the ability to book directly and cancel existing bookings.
  [href]

- Indicate unoperable occasions in the booking view.
  [href]

- Adds the ability to confirm the automatic matching.
  [href]

- Adds the ability to influence the matching algorithm using various options.
  [href]

0.1.0 (2016-11-18)
~~~~~~~~~~~~~~~~~~~

- The bookings are now called wishlists until the period is confirmed.
  [href]

- Adds the ability to match bookings/attendees with occasions.
  [href]

0.0.9 (2016-11-02)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to enroll children in occasions.
  [href]

0.0.8 (2016-10-20)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to manage periods for occasions.
  [href]

- Fixes occasion factoids not aligning nicely over multiple lines.
  [href]

0.0.7 (2016-10-14)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to discard activites in the "preview" state.
  [href]

- Adds the ability to filter ones own activities.
  [href]

- Adds the ability to filter activities by age.
  [href]

0.0.6 (2016-10-11)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to change any userprofile as administrator.
  [href]

- Adds the ability to filter activites by the duration of their occasions.
  [href]

- Always show an "Activities" link in the top bar.
  [href]

- Organisers may now upload images and set internal links, file uploads
  are prohibited though.
  [href]

- Gives admins the ability to change the organiser of an activity.
  [href]

- Activites in preview are now always visible for admins.
  [href]

0.0.5 (2016-10-04)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to enter/delete occasions.
  [href]

- Fix activity access rule for editors.
  [href]

0.0.4 (2016-09-29)
~~~~~~~~~~~~~~~~~~~

- Shows the organiser of each activity on the activity itself.
  [href]

- Adds the ability to filter activites by tag.
  [href]

0.0.3 (2016-09-22)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to create, publish and change activites.
  [href]

0.0.2 (2016-09-13)
~~~~~~~~~~~~~~~~~~~

- Adds login/registration buttons to default homepage.
  [href]

0.0.1 (2016-09-13)
~~~~~~~~~~~~~~~~~~~

- Initial Release.
  [href]
