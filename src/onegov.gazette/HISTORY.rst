Changelog
---------
1.10.1 (2017-11-10)
~~~~~~~~~~~~~~~~~~~

- Uses a chosen select for parent organizations.
  [msom]

- Fixes setting the initial ID of a category or organization.
  [msom]

- Checks the category and organization before submitting and accepting notices.
  [msom]

- Displays a warning when editing a notice with an invalid category or
  organization.
  [msom]

- Uses an external organization name for accepted mails instead of the name.
  [msom]

1.10.0 (2017-11-09)
~~~~~~~~~~~~~~~~~~~

- Allows to manage categories, organizations and issues.
  [msom]

- Adds an unrestricted edit view for admins.
  [msom]

1.9.3 (2017-11-09)
~~~~~~~~~~~~~~~~~~~

- Fixes initialization of fields.
  [msom]

- Uses latest onegov.quill release.
  [msom]

- Adds a notice modified message.
  [msom]

- Changes the order of the items in the admin menu.
  [msom]

- Always shows the first and last pagination element.
  [msom]

1.9.2 (2017-10-26)
~~~~~~~~~~~~~~~~~~~

- Uses the HSTORES for category and organization ID from the latest
  onegov.notice.
  [msom]

1.9.1 (2017-10-26)
~~~~~~~~~~~~~~~~~~~

- Fixes redirects for various views.
  [msom]

- Fixes typo.
  [msom]

1.9.0 (2017-10-24)
~~~~~~~~~~~~~~~~~~~

- Adds an XLSX export of all publishers and editors.
  [msom]

- Adds a configurable help link.
  [msom]

- Updates the subject of the publish mail.
  [msom]

- Updates RavenJs to 3.19.1.
  [msom]

1.8.0 (2017-10-18)
~~~~~~~~~~~~~~~~~~~

- Adds a script to import members.
  [msom]

1.7.0 (2017-10-13)
~~~~~~~~~~~~~~~~~~~

- Allows to sort notices by group and user names.
  [msom]

- Allows to filter notices by categories, organizations, group names and
  user names.
  [msom]

1.6.0 (2017-10-05)
~~~~~~~~~~~~~~~~~~~

- Adds session managment for users.
  [msom]

- Orders the list of users by email.
  [msom]

- Updates RavenJs to 3.18.1.
  [msom]

- Fixes rejecting a notice of a deleted user throwing an error.
  [msom]

1.5.0 (2017-09-29)
~~~~~~~~~~~~~~~~~~~

- Allows publishers to edit, submit and delete any notice.
  [msom]

- Allows publishers to manage issues past the deadline
  [msom]

- Checks the deadlines/issue dates before submitting and accepting notices.
  [msom]

- Shows a warning in the edit notice view in case of past or overdue issues.
  [msom]

- Uses warnings instead of callouts in forms.
  [msom]

- Fixes dashboard warnings.
  [msom]

- Assume issue dates and times to be UTC.
  [msom]

1.4.1 (2017-09-22)
~~~~~~~~~~~~~~~~~~~

- Suppresses the IE/Edge popup when closing the preview.
  [msom]

1.4.0 (2017-09-21)
~~~~~~~~~~~~~~~~~~~

- Exports statistics as XLSX instead of CSV.
  [msom]

1.3.5 (2017-09-21)
~~~~~~~~~~~~~~~~~~~

- Updates chosen to 1.8.2.
  [msom]

- Configures chosen to search within words, too.
  [msom]

1.3.4 (2017-09-20)
~~~~~~~~~~~~~~~~~~~

- Patches the chosen library to fix searching for non-ascii characters.
  [msom]

1.3.3 (2017-09-15)
~~~~~~~~~~~~~~~~~~~

- Fixes reset password link not working when creating users with groups.
  [msom]

1.3.2 (2017-09-14)
~~~~~~~~~~~~~~~~~~~

- Improves print styles.
  [msom]

1.3.1 (2017-09-11)
~~~~~~~~~~~~~~~~~~~

- Improves styles for IE.
  [msom]

- Adds a link to the rejected notice in the rejected email.
  [msom]

- Redirects to the manage notices view when working with notices.
  [msom]

- Redirects to the login screen after setting the password.
  [msom]

- Sends directly the password reset link when creating a user.
  [msom]

1.3.0 (2017-09-05)
~~~~~~~~~~~~~~~~~~~

- Adds a user name validator.
  [msom]

- Updates translation.
  [msom]

- Requires to select an organization when adding a notice.
  [msom]

- Doesn't use italic in the editor.
  [msom]

1.2.1 (2017-09-04)
~~~~~~~~~~~~~~~~~~~

- Uses latest onegov.quill release.
  [msom]

1.2.0 (2017-09-01)
~~~~~~~~~~~~~~~~~~~

- Uses quill editor instead of redactor.
  [msom]

1.1.0 (2017-08-31)
~~~~~~~~~~~~~~~~~~~

- Fixes chosen sprites.
  [msom]

- Adds a close button to the preview.
  [msom]

- Allows publishers to add notices.
  [msom]

1.0.0 (2017-08-31)
~~~~~~~~~~~~~~~~~~~

- Fixes clear search/dates view.
  [msom]

- Shows the preview in a separate window.
  [msom]

- Fixes test failing due to changes in the memory backend.
  [msom]

- Adjusts email texts.
  [msom]

- Adjusts dashboard warnings.
  [msom]

- Orders issues by issue year/number.
  [msom]

- Allows to set a reply to address when publishing.
  [msom]

- Reorders meta data column in notice detail view.
  [msom]

- Allows ordered and unordered lists in the editor.
  [msom]

- Allows to fold issues after unfolding again.
  [msom]

- Removes the principal name below the logo.
  [msom]

- Allows to filter notices by date.
  [msom]

- Shows state filters on notices view.
  [msom]

- Translates chosen strings.
  [msom]

- Moves the login/logout links to the top right.
  [msom]

- Adds an option to indicate if one needs to pay to publish a specific notice.
  [msom]

- Adds a print button to the preview.
  [msom]

0.1.2 (2017-08-22)
~~~~~~~~~~~~~~~~~~~

- Shows the publisher menu entries for the admin as well.
  [msom]

- Fixes delete icon on user managemenet view.
  [msom]

0.1.1 (2017-08-21)
~~~~~~~~~~~~~~~~~~~

- Fixes ordering by first issue.
  [msom]

0.1.0 (2017-08-21)
~~~~~~~~~~~~~~~~~~~

- Shows the name of the logged-in user.
  [msom]

- Reduces the font size of the title in the preview.
  [msom]

- Omits the emails on publishing.
  [msom]

- Sends an email when creating a user.
  [msom]

- Adds statistics to the menu.
  [msom]

- Adds a state filter to the statistics.
  [msom]

- Shows the weekday in the add/edit notice form.
  [msom]

- Adds comments for rejecting notices.
  [msom]

- Sanitizes HTML much stricter.
  [msom]

- Allows to delete users with official notices.
  [msom]

- Allows to filter notices by a search term.
  [msom]

- Allows admins to delete submitted and published notices.
  [msom]

- Adds organizations to notices.
  [msom]

- Removes hierarchy from categories.
  [msom]

- Allows to order notices.
  [msom]

- Adds filters for organizations and categories to the edit/create notice views.
  [msom]

- Allows to show the later issues in the edit/create notice views, too.
  [msom]

- Adds deadlines to issues.
  [msom]

- Adds date filters to statistices.
  [msom]

- Adds an accepted state.
  [msom]

- Caches the user and group name on notices in case they get deleted.
  [msom]

- Caches the user name on notice changes in case they get deleted.
  [msom]

- Shows notices for the same group.
  [msom]

0.0.4 (2017-08-03)
~~~~~~~~~~~~~~~~~~~

- Switches from onegov.testing to onegov_testing.
  [href]

0.0.3 (2017-07-17)
~~~~~~~~~~~~~~~~~~~

- Add github deploy key.
  [msom]

0.0.2 (2017-07-17)
~~~~~~~~~~~~~~~~~~~

- Sends emails on publish/reject.
  [msom]

- Adds a copy option.
  [msom]

- Adds statistics views.
  [msom]

- Adds a preview view.
  [msom]

0.0.1 (unreleased)
~~~~~~~~~~~~~~~~~~

- Initial Release.
  [msom]
